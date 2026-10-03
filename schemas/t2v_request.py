"""T2VRequest schema definition."""

import uuid
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, field_validator

from engine.errors import T2VErrorCode, T2VValidationError

SUPPORTED_RESOLUTIONS = {
    "832x480",
    "480x832",
    "1280x720",
    "720x1280",
    "960x544",
    "544x960",
    "1024x576",
    "576x1024",
}

SUPPORTED_FPS = {16, 24, 30}


class T2VRequest(BaseModel):
    """Input specification for Text-to-Video generation."""

    request_id: str = Field(
        default_factory=lambda: f"req_{uuid.uuid4().hex[:8]}",
        description="Unique identifier for the generation request",
    )
    prompt: str = Field(
        ...,
        description="Text description of the video shot to generate",
    )
    negative_prompt: Optional[str] = Field(
        default="",
        description="Elements or attributes to avoid in generation",
    )
    model: str = Field(
        default="Wan2.2-T2V-A14B",
        description="Model identifier to use",
    )
    provider: str = Field(
        default="mock",
        description="Provider adapter to use (mock, fal_ai, wavespeedai, local_wan)",
    )
    duration_seconds: int = Field(
        default=5,
        description="Duration of the generated video in seconds (1 to 10)",
    )
    fps: int = Field(
        default=16,
        description="Frames per second (16, 24, or 30)",
    )
    resolution: str = Field(
        default="832x480",
        description="Video resolution formatted as WxH",
    )
    aspect_ratio: str = Field(
        default="16:9",
        description="Target aspect ratio",
    )
    seed: int = Field(
        default=-1,
        description="Random seed for reproducibility (-1 for random)",
    )
    guidance_scale: float = Field(
        default=5.0,
        description="Classifier-free guidance scale",
    )
    num_inference_steps: int = Field(
        default=40,
        description="Number of denoising steps",
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Pass-through metadata and runtime directives (e.g. simulate_failure)",
    )

    @field_validator("prompt")
    @classmethod
    def validate_prompt(cls, v: str) -> str:
        if v is None or not str(v).strip():
            raise T2VValidationError(
                "Prompt must be a non-empty string",
                code=T2VErrorCode.EMPTY_PROMPT,
            )
        return v.strip()

    @field_validator("duration_seconds")
    @classmethod
    def validate_duration(cls, v: int) -> int:
        if v is None or v <= 0 or v > 10:
            raise T2VValidationError(
                f"duration_seconds must be between 1 and 10, got {v}",
                code=T2VErrorCode.INVALID_DURATION,
            )
        return v

    @field_validator("fps")
    @classmethod
    def validate_fps(cls, v: int) -> int:
        if v not in SUPPORTED_FPS:
            raise T2VValidationError(
                f"fps must be one of {sorted(list(SUPPORTED_FPS))}, got {v}",
                code=T2VErrorCode.INVALID_FPS,
            )
        return v

    @field_validator("resolution")
    @classmethod
    def validate_resolution(cls, v: str) -> str:
        if v not in SUPPORTED_RESOLUTIONS:
            raise T2VValidationError(
                f"resolution '{v}' unsupported. Supported: {sorted(list(SUPPORTED_RESOLUTIONS))}",
                code=T2VErrorCode.UNSUPPORTED_RESOLUTION,
            )
        return v

    def get_width_height(self) -> tuple[int, int]:
        """Parse resolution string to width and height integers."""
        parts = self.resolution.lower().split("x")
        return int(parts[0]), int(parts[1])
