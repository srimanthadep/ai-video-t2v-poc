"""Abstract base class and factory for T2V adapters."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Union

from schemas.t2v_request import T2VRequest
from schemas.t2v_result import T2VResult
from engine.errors import T2VValidationError


class T2VAdapter(ABC):
    """Provider-agnostic interface for Text-to-Video generation engines."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

    @abstractmethod
    def generate(self, request: Union[T2VRequest, Dict[str, Any]]) -> T2VResult:
        """Generate a video from a T2V request and return structured T2VResult."""
        pass

    @abstractmethod
    def validate_request(self, request: Union[T2VRequest, Dict[str, Any]]) -> T2VRequest:
        """Validate input parameters against adapter capabilities."""
        pass

    @abstractmethod
    def get_capabilities(self) -> Dict[str, Any]:
        """Return dict of supported resolutions, fps, max duration, features."""
        pass

    def health_check(self) -> bool:
        """Verify provider availability or local backend readiness."""
        return True

    def estimate_cost(self, request: Union[T2VRequest, Dict[str, Any]]) -> Optional[float]:
        """Return estimated generation cost in USD, or None if free/unsupported."""
        return 0.0


def create_adapter(provider: str, config: Optional[Dict[str, Any]] = None) -> T2VAdapter:
    """Factory creating the appropriate T2V adapter instance."""
    normalized_provider = provider.lower().strip()
    cfg = config or {}

    if normalized_provider == "mock":
        from adapters.mock_adapter import MockT2VAdapter
        return MockT2VAdapter(cfg)
    elif normalized_provider in ("fal_ai", "fal", "wan_fal"):
        from adapters.wan_fal_adapter import WanFalAIAdapter
        return WanFalAIAdapter(cfg)
    else:
        raise ValueError(
            f"Unsupported T2V provider '{provider}'. Supported providers: 'mock', 'fal_ai'"
        )
