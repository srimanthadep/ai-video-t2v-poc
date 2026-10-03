"""T2VResult schema definition."""

from datetime import datetime, timezone
from typing import Any, Dict, Literal, Optional
from pydantic import BaseModel, Field


class T2VErrorDetail(BaseModel):
    """Structured error information for failed generation."""

    code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable explanation")
    retryable: bool = Field(default=False, description="Whether repeating the request might succeed")


class T2VResult(BaseModel):
    """Output specification for Text-to-Video generation."""

    request_id: str = Field(
        ...,
        description="The matching request identifier",
    )
    status: Literal["success", "error"] = Field(
        ...,
        description="Outcome of the generation request",
    )
    data_type: Literal["MOCK", "REAL"] = Field(
        ...,
        description="Explicit label distinguishing synthetic MOCK data from REAL AI generation",
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 timestamp of generation",
    )
    video_path: Optional[str] = Field(
        default=None,
        description="Local path to the video MP4 file",
    )
    video_url: Optional[str] = Field(
        default=None,
        description="Remote hosted URL if produced via cloud API",
    )
    duration_seconds: Optional[float] = Field(
        default=None,
        description="Actual measured duration from ffprobe",
    )
    fps: Optional[float] = Field(
        default=None,
        description="Actual measured frames per second",
    )
    resolution: Optional[str] = Field(
        default=None,
        description="Actual video dimensions (WxH)",
    )
    codec: Optional[str] = Field(
        default=None,
        description="Video codec name (e.g. h264)",
    )
    file_size_bytes: Optional[int] = Field(
        default=None,
        description="Output file size in bytes",
    )
    model: str = Field(
        default="Wan2.2-T2V-A14B",
        description="Model identifier",
    )
    provider: str = Field(
        default="mock",
        description="Provider adapter used (mock, fal_ai, etc.)",
    )
    seed: Optional[int] = Field(
        default=None,
        description="Seed used during generation",
    )
    generation_time_seconds: Optional[float] = Field(
        default=None,
        description="Wall-clock elapsed time for generation in seconds",
    )
    cost_usd: Optional[float] = Field(
        default=None,
        description="Estimated or reported cost in USD",
    )
    error: Optional[T2VErrorDetail] = Field(
        default=None,
        description="Details on error if status is 'error'",
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional diagnostics, prompt echoes, or runtime metadata",
    )
