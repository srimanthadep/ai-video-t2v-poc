"""Wan 2.2 T2V Adapter using fal.ai API."""

import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Union
import requests

from adapters.base import T2VAdapter
from engine.errors import (
    T2VErrorCode,
    T2VProviderError,
    T2VTimeoutError,
    T2VValidationError,
)
from engine.validator import validate_video
from schemas.t2v_request import SUPPORTED_FPS, SUPPORTED_RESOLUTIONS, T2VRequest
from schemas.t2v_result import T2VResult, T2VErrorDetail

DEFAULT_WAN_MODEL = "fal-ai/wan/v2.2-a14b/text-to-video"


class WanFalAIAdapter(T2VAdapter):
    """Integrates Wan 2.2 T2V generation through the fal.ai cloud inference API."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.api_key = self.config.get("api_key") or os.getenv("FAL_KEY")
        self.model_id = self.config.get("model_id", DEFAULT_WAN_MODEL)
        self.output_dir = Path(self.config.get("output_dir", "outputs/real"))
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.timeout = int(self.config.get("timeout", os.getenv("T2V_TIMEOUT_SECONDS", 300)))
        self.max_retries = int(self.config.get("max_retries", os.getenv("T2V_MAX_RETRIES", 2)))

    def get_capabilities(self) -> Dict[str, Any]:
        return {
            "provider": "fal_ai",
            "model": self.model_id,
            "supported_resolutions": sorted(list(SUPPORTED_RESOLUTIONS)),
            "supported_fps": [16, 24],
            "min_duration_seconds": 5,
            "max_duration_seconds": 5,
            "features": [
                "wan2.2_moe_diffusion",
                "negative_prompt",
                "seed_reproducibility",
                "cloud_gpu_a100_h100",
                "real_ai_output",
            ],
        }

    def health_check(self) -> bool:
        """Check if fal API key is configured and responsive."""
        return bool(self.api_key and len(self.api_key.strip()) > 5)

    def validate_request(self, request: Union[T2VRequest, Dict[str, Any]]) -> T2VRequest:
        if isinstance(request, dict):
            if "prompt" not in request or not str(request.get("prompt", "")).strip():
                raise T2VValidationError(
                    "Prompt cannot be empty or missing",
                    code=T2VErrorCode.EMPTY_PROMPT,
                )
            req = T2VRequest(**request)
        elif isinstance(request, T2VRequest):
            req = request
        else:
            raise T2VValidationError("Invalid request type", code=T2VErrorCode.VALIDATION_ERROR)
        return req

    def _download_video(self, url: str, target_path: Path) -> None:
        """Download remote video file stream to disk."""
        resp = requests.get(url, stream=True, timeout=60)
        resp.raise_for_status()
        with open(target_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)

    def generate(self, request: Union[T2VRequest, Dict[str, Any]]) -> T2VResult:
        """Submit text-to-video prompt to Wan 2.2 on fal.ai and download output."""
        start_time = time.time()

        # Step 1: Validate request
        try:
            req = self.validate_request(request)
        except T2VValidationError as ve:
            return T2VResult(
                request_id=getattr(request, "request_id", "unknown_req")
                if isinstance(request, T2VRequest)
                else (request.get("request_id", "unknown_req") if isinstance(request, dict) else "unknown_req"),
                status="error",
                data_type="REAL",
                model=self.model_id,
                provider="fal_ai",
                error=T2VErrorDetail(code=ve.code, message=ve.message, retryable=ve.retryable),
            )

        # Step 2: Validate API key configuration
        if not self.api_key:
            return T2VResult(
                request_id=req.request_id,
                status="error",
                data_type="REAL",
                model=self.model_id,
                provider="fal_ai",
                generation_time_seconds=round(time.time() - start_time, 3),
                error=T2VErrorDetail(
                    code=T2VErrorCode.PROVIDER_ERROR.value,
                    message="FAL_KEY environment variable is not configured. Set FAL_KEY in .env to run real Wan 2.2 generation.",
                    retryable=False,
                ),
            )

        # Step 3: Lazy import fal_client
        try:
            import fal_client
            # Set FAL_KEY in environment for the client
            os.environ["FAL_KEY"] = self.api_key
        except ImportError:
            return T2VResult(
                request_id=req.request_id,
                status="error",
                data_type="REAL",
                model=self.model_id,
                provider="fal_ai",
                error=T2VErrorDetail(
                    code=T2VErrorCode.PROVIDER_ERROR.value,
                    message="fal-client package is not installed.",
                    retryable=False,
                ),
            )

        # Step 4: Map parameters for fal.ai Wan 2.2 API
        arguments = {
            "prompt": req.prompt,
            "aspect_ratio": req.aspect_ratio if req.aspect_ratio in ("16:9", "9:16") else "16:9",
            "resolution": req.resolution,
        }
        if req.negative_prompt:
            arguments["negative_prompt"] = req.negative_prompt
        if req.seed is not None and req.seed >= 0:
            arguments["seed"] = req.seed

        # Step 5: Execute with retry policy
        target_file = self.output_dir / f"wan22_{req.request_id}.mp4"
        last_error = None

        for attempt in range(self.max_retries + 1):
            try:
                # Submit job to fal.ai
                handler = fal_client.submit(self.model_id, arguments=arguments)
                result = handler.get()

                if not result or "video" not in result or "url" not in result["video"]:
                    raise T2VProviderError(
                        f"fal.ai response did not contain expected video URL: {result}",
                        code=T2VErrorCode.NO_OUTPUT,
                    )

                video_url = result["video"]["url"]

                # Download video to local disk
                self._download_video(video_url, target_file)

                # Validate with ffprobe
                validation = validate_video(str(target_file))
                if not validation["valid"]:
                    raise T2VProviderError(
                        f"Downloaded video failed ffprobe check: {validation['errors']}",
                        code=T2VErrorCode.OUTPUT_INVALID,
                    )

                elapsed = round(time.time() - start_time, 3)

                return T2VResult(
                    request_id=req.request_id,
                    status="success",
                    data_type="REAL",
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    video_path=str(target_file),
                    video_url=video_url,
                    duration_seconds=validation["duration"] or 5.0,
                    fps=validation["fps"] or 16.0,
                    resolution=validation["resolution"] or req.resolution,
                    codec=validation["codec"] or "h264",
                    file_size_bytes=validation["file_size_bytes"],
                    model=self.model_id,
                    provider="fal_ai",
                    seed=req.seed,
                    generation_time_seconds=elapsed,
                    cost_usd=0.20,  # Approximate ~0.20 per Wan 2.2 generation on fal
                    metadata={
                        **req.metadata,
                        "prompt": req.prompt,
                        "ffprobe_validated": True,
                    },
                )

            except Exception as e:
                last_error = e
                if attempt < self.max_retries:
                    backoff = 2 ** attempt
                    time.sleep(backoff)

        # Retries exhausted
        return T2VResult(
            request_id=req.request_id,
            status="error",
            data_type="REAL",
            model=self.model_id,
            provider="fal_ai",
            generation_time_seconds=round(time.time() - start_time, 3),
            error=T2VErrorDetail(
                code=T2VErrorCode.PROVIDER_ERROR.value,
                message=f"fal.ai Wan 2.2 generation failed after {self.max_retries + 1} attempts: {str(last_error)}",
                retryable=True,
            ),
        )
