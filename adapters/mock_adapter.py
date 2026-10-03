"""FFmpeg-based Mock T2V Adapter producing real playable MP4 videos."""

import json
import os
import re
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Union

from adapters.base import T2VAdapter
from engine.errors import (
    T2VErrorCode,
    T2VOutputError,
    T2VProviderError,
    T2VTimeoutError,
    T2VValidationError,
)
from engine.validator import validate_video
from schemas.t2v_request import SUPPORTED_FPS, SUPPORTED_RESOLUTIONS, T2VRequest
from schemas.t2v_result import T2VResult, T2VErrorDetail


def _sanitize_for_drawtext(text: str) -> str:
    """Sanitize strings for FFmpeg drawtext filter syntax."""
    # Replace single quotes, backslashes, colons, percent signs
    text = re.sub(r"['\\:%]", " ", text)
    # Remove control characters
    text = "".join(ch for ch in text if ch.isprintable())
    return text.strip()


class MockT2VAdapter(T2VAdapter):
    """Generates synthetic, fully playable MP4 videos locally using FFmpeg."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.output_dir = Path(self.config.get("output_dir", "outputs/mock"))
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def get_capabilities(self) -> Dict[str, Any]:
        return {
            "provider": "mock",
            "model": "Mock-FFmpeg-H264",
            "supported_resolutions": sorted(list(SUPPORTED_RESOLUTIONS)),
            "supported_fps": sorted(list(SUPPORTED_FPS)),
            "min_duration_seconds": 1,
            "max_duration_seconds": 10,
            "features": [
                "offline",
                "deterministic",
                "h264_mp4",
                "failure_simulation",
                "ffprobe_verified",
            ],
        }

    def validate_request(self, request: Union[T2VRequest, Dict[str, Any]]) -> T2VRequest:
        """Validate input parameters against constraints."""
        if isinstance(request, dict):
            # Check for missing prompt explicitly before Pydantic parsing
            if "prompt" not in request:
                raise T2VValidationError(
                    "Missing required field 'prompt'",
                    code=T2VErrorCode.MISSING_PROMPT,
                )
            if not str(request.get("prompt", "")).strip():
                raise T2VValidationError(
                    "Prompt cannot be empty or whitespace only",
                    code=T2VErrorCode.EMPTY_PROMPT,
                )
            try:
                req = T2VRequest(**request)
            except T2VValidationError:
                raise
            except Exception as e:
                raise T2VValidationError(
                    f"Request validation failed: {e}",
                    code=T2VErrorCode.VALIDATION_ERROR,
                )
        elif isinstance(request, T2VRequest):
            req = request
        else:
            raise T2VValidationError(
                f"Expected T2VRequest or dict, got {type(request)}",
                code=T2VErrorCode.VALIDATION_ERROR,
            )
        return req

    def generate(self, request: Union[T2VRequest, Dict[str, Any]]) -> T2VResult:
        """Generate a synthetic MP4 video and return T2VResult with data_type='MOCK'."""
        start_time = time.time()

        # Step 1: Validate request
        try:
            req = self.validate_request(request)
        except T2VValidationError as ve:
            return T2VResult(
                request_id=getattr(request, "request_id", None)
                or (request.get("request_id") if isinstance(request, dict) else "unknown_req"),
                status="error",
                data_type="MOCK",
                timestamp=datetime.now(timezone.utc).isoformat(),
                model="Mock-FFmpeg-H264",
                provider="mock",
                error=T2VErrorDetail(code=ve.code, message=ve.message, retryable=ve.retryable),
            )

        # Step 2: Handle simulated failure directives if requested
        simulate_failure = req.metadata.get("simulate_failure")
        if simulate_failure:
            sim_code = str(simulate_failure).upper()
            if sim_code == "TIMEOUT":
                return T2VResult(
                    request_id=req.request_id,
                    status="error",
                    data_type="MOCK",
                    model=req.model,
                    provider="mock",
                    generation_time_seconds=round(time.time() - start_time, 3),
                    error=T2VErrorDetail(
                        code=T2VErrorCode.TIMEOUT.value,
                        message="Simulated generation timeout exceeded limit",
                        retryable=True,
                    ),
                    metadata=req.metadata,
                )
            elif sim_code == "PROVIDER_ERROR":
                return T2VResult(
                    request_id=req.request_id,
                    status="error",
                    data_type="MOCK",
                    model=req.model,
                    provider="mock",
                    generation_time_seconds=round(time.time() - start_time, 3),
                    error=T2VErrorDetail(
                        code=T2VErrorCode.PROVIDER_ERROR.value,
                        message="Simulated provider infrastructure error",
                        retryable=True,
                    ),
                    metadata=req.metadata,
                )
            elif sim_code == "OOM":
                return T2VResult(
                    request_id=req.request_id,
                    status="error",
                    data_type="MOCK",
                    model=req.model,
                    provider="mock",
                    generation_time_seconds=round(time.time() - start_time, 3),
                    error=T2VErrorDetail(
                        code=T2VErrorCode.OOM.value,
                        message="Simulated out-of-memory error during video diffusion",
                        retryable=False,
                    ),
                    metadata=req.metadata,
                )
            elif sim_code == "OUTPUT_INVALID":
                # Create a 0-byte corrupt file
                custom_path = req.metadata.get("output_path")
                target_file = Path(custom_path) if custom_path else self.output_dir / f"mock_{req.request_id}.mp4"
                target_file.parent.mkdir(parents=True, exist_ok=True)
                with open(target_file, "w") as f:
                    pass  # Zero-byte file
                val = validate_video(str(target_file))
                return T2VResult(
                    request_id=req.request_id,
                    status="error",
                    data_type="MOCK",
                    model=req.model,
                    provider="mock",
                    video_path=str(target_file),
                    generation_time_seconds=round(time.time() - start_time, 3),
                    error=T2VErrorDetail(
                        code=T2VErrorCode.OUTPUT_INVALID.value,
                        message=f"Output video validation failed: {'; '.join(val['errors'])}",
                        retryable=True,
                    ),
                    metadata=req.metadata,
                )
            elif sim_code == "NO_OUTPUT":
                return T2VResult(
                    request_id=req.request_id,
                    status="error",
                    data_type="MOCK",
                    model=req.model,
                    provider="mock",
                    generation_time_seconds=round(time.time() - start_time, 3),
                    error=T2VErrorDetail(
                        code=T2VErrorCode.NO_OUTPUT.value,
                        message="Generation completed but no output file was created",
                        retryable=True,
                    ),
                    metadata=req.metadata,
                )

        # Step 3: Determine target output video path
        custom_path = req.metadata.get("output_path")
        if custom_path:
            output_file = Path(custom_path)
        else:
            output_file = self.output_dir / f"mock_{req.request_id}.mp4"

        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Step 4: Build FFmpeg command
        width, height = req.get_width_height()
        duration = req.duration_seconds
        fps = req.fps
        bg_color = "0x121826"  # Sleek dark navy/slate background

        # Format clean text overlay
        safe_req_id = _sanitize_for_drawtext(req.request_id)
        raw_prompt = req.prompt[:60] + ("..." if len(req.prompt) > 60 else "")
        safe_prompt = _sanitize_for_drawtext(raw_prompt)
        safe_footer = _sanitize_for_drawtext(
            f"MOCK DATA | {width}x{height} | {fps}fps | {duration}s | Wan2.2 POC"
        )

        filter_graph = (
            f"drawtext=text='MOCK T2V - {safe_req_id}':fontcolor=white:fontsize=24:"
            f"x=(w-text_w)/2:y=35,"
            f"drawtext=text='{safe_prompt}':fontcolor=0xcccccc:fontsize=18:"
            f"x=(w-text_w)/2:y=(h-text_h)/2,"
            f"drawtext=text='{safe_footer}':fontcolor=0x888888:fontsize=14:"
            f"x=(w-text_w)/2:y=h-45"
        )

        cmd = [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"color=c={bg_color}:s={width}x{height}:d={duration}:r={fps}",
            "-vf",
            filter_graph,
            "-c:v",
            "libx264",
            "-preset",
            "ultrafast",
            "-pix_fmt",
            "yuv420p",
            str(output_file),
        ]

        try:
            proc = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=30,
                check=False,
            )
            if proc.returncode != 0:
                raise T2VProviderError(
                    f"FFmpeg process returned non-zero code {proc.returncode}: {proc.stderr[-300:]}",
                    code=T2VErrorCode.PROVIDER_ERROR,
                )
        except subprocess.TimeoutExpired:
            raise T2VTimeoutError(
                "FFmpeg generation timed out", code=T2VErrorCode.TIMEOUT
            )
        except Exception as e:
            raise T2VProviderError(
                f"FFmpeg generation failed: {e}", code=T2VErrorCode.PROVIDER_ERROR
            )

        # Step 5: Validate output using ffprobe
        validation = validate_video(
            str(output_file),
            expected_params={
                "duration": duration,
                "fps": fps,
                "resolution": req.resolution,
            },
        )

        if not validation["valid"]:
            return T2VResult(
                request_id=req.request_id,
                status="error",
                data_type="MOCK",
                video_path=str(output_file),
                model=req.model,
                provider="mock",
                generation_time_seconds=round(time.time() - start_time, 3),
                error=T2VErrorDetail(
                    code=T2VErrorCode.OUTPUT_INVALID.value,
                    message=f"ffprobe validation failed: {'; '.join(validation['errors'])}",
                    retryable=True,
                ),
                metadata=req.metadata,
            )

        elapsed = round(time.time() - start_time, 3)

        # Return verified success result
        return T2VResult(
            request_id=req.request_id,
            status="success",
            data_type="MOCK",
            timestamp=datetime.now(timezone.utc).isoformat(),
            video_path=str(output_file),
            duration_seconds=validation["duration"] or float(duration),
            fps=validation["fps"] or float(fps),
            resolution=validation["resolution"] or f"{width}x{height}",
            codec=validation["codec"] or "h264",
            file_size_bytes=validation["file_size_bytes"],
            model=req.model,
            provider="mock",
            seed=req.seed if req.seed != -1 else 42,
            generation_time_seconds=elapsed,
            cost_usd=0.0,
            metadata={
                **req.metadata,
                "ffprobe_validated": True,
                "prompt": req.prompt,
            },
        )
