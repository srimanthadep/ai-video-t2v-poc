"""Main orchestrator engine for Text-to-Video generation."""

import os
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Union
from dotenv import load_dotenv

from adapters.base import T2VAdapter, create_adapter
from engine.errors import (
    T2VError,
    T2VErrorCode,
    T2VValidationError,
)
from schemas.t2v_request import T2VRequest
from schemas.t2v_result import T2VResult, T2VErrorDetail

# Load environment variables from .env if present
load_dotenv()


class T2VEngine:
    """High-level facade orchestrating request validation, adapter dispatch, and error handling."""

    def __init__(
        self,
        provider: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
    ):
        self.provider = provider or os.getenv("T2V_PROVIDER", "mock")
        self.config = config or {}

        # Merge environment defaults if not explicitly set in config
        if "output_dir" not in self.config:
            self.config["output_dir"] = os.getenv("T2V_OUTPUT_DIR", "outputs")

        self.adapter: T2VAdapter = create_adapter(self.provider, self.config)

    def run(self, request: Union[T2VRequest, Dict[str, Any]]) -> T2VResult:
        """Process a T2V request safely, guaranteeing a valid T2VResult even on failure."""
        start_time = time.time()
        req_id = "unknown"

        if isinstance(request, T2VRequest):
            req_id = request.request_id
        elif isinstance(request, dict):
            req_id = request.get("request_id", "unknown")

        try:
            return self.adapter.generate(request)
        except T2VValidationError as ve:
            return T2VResult(
                request_id=req_id,
                status="error",
                data_type="MOCK" if self.provider == "mock" else "REAL",
                timestamp=datetime.now(timezone.utc).isoformat(),
                model=getattr(request, "model", "unknown")
                if isinstance(request, T2VRequest)
                else (request.get("model", "unknown") if isinstance(request, dict) else "unknown"),
                provider=self.provider,
                generation_time_seconds=round(time.time() - start_time, 3),
                error=T2VErrorDetail(code=ve.code, message=ve.message, retryable=ve.retryable),
            )
        except T2VError as te:
            return T2VResult(
                request_id=req_id,
                status="error",
                data_type="MOCK" if self.provider == "mock" else "REAL",
                timestamp=datetime.now(timezone.utc).isoformat(),
                provider=self.provider,
                generation_time_seconds=round(time.time() - start_time, 3),
                error=T2VErrorDetail(code=te.code, message=te.message, retryable=te.retryable),
            )
        except Exception as ex:
            return T2VResult(
                request_id=req_id,
                status="error",
                data_type="MOCK" if self.provider == "mock" else "REAL",
                timestamp=datetime.now(timezone.utc).isoformat(),
                provider=self.provider,
                generation_time_seconds=round(time.time() - start_time, 3),
                error=T2VErrorDetail(
                    code=T2VErrorCode.PROVIDER_ERROR.value,
                    message=f"Unhandled internal error: {str(ex)}",
                    retryable=False,
                ),
            )

    def get_capabilities(self) -> Dict[str, Any]:
        """Query active adapter capabilities."""
        return self.adapter.get_capabilities()

    def health_check(self) -> bool:
        """Verify readiness of active adapter."""
        return self.adapter.health_check()
