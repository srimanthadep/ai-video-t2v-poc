"""Structured error types and error codes for T2V module."""

from enum import Enum
from typing import Optional


class T2VErrorCode(str, Enum):
    """Standardized error codes for the T2V system."""

    EMPTY_PROMPT = "EMPTY_PROMPT"
    MISSING_PROMPT = "MISSING_PROMPT"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INVALID_DURATION = "INVALID_DURATION"
    INVALID_FPS = "INVALID_FPS"
    UNSUPPORTED_RESOLUTION = "UNSUPPORTED_RESOLUTION"
    TIMEOUT = "TIMEOUT"
    PROVIDER_ERROR = "PROVIDER_ERROR"
    OOM = "OOM"
    OUTPUT_INVALID = "OUTPUT_INVALID"
    NO_OUTPUT = "NO_OUTPUT"
    OUTPUT_MISMATCH = "OUTPUT_MISMATCH"
    RATE_LIMITED = "RATE_LIMITED"


class T2VError(Exception):
    """Base exception for all T2V generation errors."""

    def __init__(
        self,
        message: str,
        code: T2VErrorCode = T2VErrorCode.PROVIDER_ERROR,
        retryable: bool = False,
    ):
        super().__init__(message)
        self.message = message
        self.code = code.value if isinstance(code, T2VErrorCode) else str(code)
        self.retryable = retryable

    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "message": self.message,
            "retryable": self.retryable,
        }


class T2VValidationError(T2VError):
    """Raised when request validation fails."""

    def __init__(
        self,
        message: str,
        code: T2VErrorCode = T2VErrorCode.VALIDATION_ERROR,
        retryable: bool = False,
    ):
        super().__init__(message=message, code=code, retryable=retryable)


class T2VProviderError(T2VError):
    """Raised when upstream AI provider/engine fails."""

    def __init__(
        self,
        message: str,
        code: T2VErrorCode = T2VErrorCode.PROVIDER_ERROR,
        retryable: bool = True,
    ):
        super().__init__(message=message, code=code, retryable=retryable)


class T2VTimeoutError(T2VError):
    """Raised when generation times out."""

    def __init__(
        self,
        message: str = "T2V generation timed out",
        code: T2VErrorCode = T2VErrorCode.TIMEOUT,
        retryable: bool = True,
    ):
        super().__init__(message=message, code=code, retryable=retryable)


class T2VOutputError(T2VError):
    """Raised when generated video output is missing or invalid."""

    def __init__(
        self,
        message: str,
        code: T2VErrorCode = T2VErrorCode.OUTPUT_INVALID,
        retryable: bool = True,
    ):
        super().__init__(message=message, code=code, retryable=retryable)
