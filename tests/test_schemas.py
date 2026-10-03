"""Unit tests for T2VRequest and T2VResult schemas."""

import pytest
from pydantic import ValidationError

from engine.errors import T2VErrorCode, T2VValidationError
from schemas.t2v_request import T2VRequest
from schemas.t2v_result import T2VResult, T2VErrorDetail


def test_request_schema_valid(sample_valid_request):
    """Verify that a fully specified valid request parses correctly."""
    req = T2VRequest(**sample_valid_request)
    assert req.request_id == "pytest_valid_001"
    assert req.prompt == sample_valid_request["prompt"]
    assert req.duration_seconds == 5
    assert req.fps == 16
    assert req.resolution == "832x480"
    assert req.provider == "mock"


def test_request_schema_minimal(sample_minimal_request):
    """Verify that minimal inputs apply defaults according to spec."""
    req = T2VRequest(**sample_minimal_request)
    assert req.request_id == "pytest_minimal_001"
    assert req.duration_seconds == 5
    assert req.fps == 16
    assert req.resolution == "832x480"
    assert req.model == "Wan2.2-T2V-A14B"
    assert req.provider == "mock"


def test_request_schema_reject_empty_prompt():
    """Verify that empty prompt strings raise T2VValidationError with EMPTY_PROMPT."""
    with pytest.raises((T2VValidationError, ValidationError)) as exc_info:
        T2VRequest(request_id="fail_empty", prompt="")
    assert "EMPTY_PROMPT" in str(exc_info.value) or "empty" in str(exc_info.value).lower()


def test_request_schema_reject_whitespace_prompt():
    """Verify that whitespace-only prompts are rejected."""
    with pytest.raises((T2VValidationError, ValidationError)):
        T2VRequest(request_id="fail_space", prompt="   \n\t  ")


def test_request_schema_reject_missing_prompt():
    """Verify that missing prompt field fails validation."""
    with pytest.raises(ValidationError):
        T2VRequest(request_id="fail_missing")


def test_request_schema_reject_invalid_duration():
    """Verify negative and excessive durations are rejected."""
    with pytest.raises((T2VValidationError, ValidationError)):
        T2VRequest(request_id="fail_neg_dur", prompt="test", duration_seconds=-1)

    with pytest.raises((T2VValidationError, ValidationError)):
        T2VRequest(request_id="fail_max_dur", prompt="test", duration_seconds=999)


def test_request_schema_reject_invalid_fps():
    """Verify non-standard FPS values are rejected."""
    with pytest.raises((T2VValidationError, ValidationError)):
        T2VRequest(request_id="fail_fps", prompt="test", fps=999)


def test_request_schema_reject_unsupported_resolution():
    """Verify arbitrary unsupported resolutions are rejected."""
    with pytest.raises((T2VValidationError, ValidationError)):
        T2VRequest(request_id="fail_res", prompt="test", resolution="7680x4320")


def test_result_schema_valid_success():
    """Verify T2VResult serialization for success cases with data_type='MOCK'."""
    res = T2VResult(
        request_id="req_success_1",
        status="success",
        data_type="MOCK",
        video_path="outputs/mock/video.mp4",
        duration_seconds=5.0,
        fps=16.0,
        resolution="832x480",
        codec="h264",
        file_size_bytes=24000,
        model="Wan2.2-T2V-A14B",
        provider="mock",
    )
    dumped = res.model_dump()
    assert dumped["status"] == "success"
    assert dumped["data_type"] == "MOCK"
    assert dumped["codec"] == "h264"
    assert dumped["duration_seconds"] == 5.0


def test_result_schema_valid_error():
    """Verify T2VResult serialization for error cases."""
    res = T2VResult(
        request_id="req_err_1",
        status="error",
        data_type="MOCK",
        error=T2VErrorDetail(
            code=T2VErrorCode.EMPTY_PROMPT.value,
            message="Prompt cannot be empty",
            retryable=False,
        ),
    )
    dumped = res.model_dump()
    assert dumped["status"] == "error"
    assert dumped["error"]["code"] == "EMPTY_PROMPT"
    assert dumped["error"]["retryable"] is False
