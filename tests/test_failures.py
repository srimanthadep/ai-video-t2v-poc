"""Unit tests for failure handling and error matrix verification."""

import json
from pathlib import Path
import pytest

from engine.errors import T2VErrorCode


def test_failure_empty_prompt(mock_adapter):
    """T2V_F01: Empty prompt should return EMPTY_PROMPT error without crashing."""
    res = mock_adapter.generate({"request_id": "T2V_F01", "prompt": ""})
    assert res.status == "error"
    assert res.error is not None
    assert res.error.code == T2VErrorCode.EMPTY_PROMPT.value
    assert res.video_path is None


def test_failure_missing_prompt(mock_adapter):
    """T2V_F02: Missing prompt field should return MISSING_PROMPT error."""
    res = mock_adapter.generate({"request_id": "T2V_F02"})
    assert res.status == "error"
    assert res.error is not None
    assert res.error.code == T2VErrorCode.MISSING_PROMPT.value


def test_failure_invalid_duration(mock_adapter):
    """T2V_F03 & T2V_F04: Duration boundaries."""
    res_neg = mock_adapter.generate({"request_id": "F03", "prompt": "shot", "duration_seconds": -1})
    assert res_neg.status == "error"
    assert res_neg.error.code == T2VErrorCode.INVALID_DURATION.value

    res_long = mock_adapter.generate({"request_id": "F04", "prompt": "shot", "duration_seconds": 999})
    assert res_long.status == "error"
    assert res_long.error.code == T2VErrorCode.INVALID_DURATION.value


def test_failure_invalid_fps(mock_adapter):
    """T2V_F05: Disallowed frame rate."""
    res = mock_adapter.generate({"request_id": "F05", "prompt": "shot", "fps": 999})
    assert res.status == "error"
    assert res.error.code == T2VErrorCode.INVALID_FPS.value


def test_failure_unsupported_resolution(mock_adapter):
    """T2V_F06: Unsupported resolution."""
    res = mock_adapter.generate({"request_id": "F06", "prompt": "shot", "resolution": "7680x4320"})
    assert res.status == "error"
    assert res.error.code == T2VErrorCode.UNSUPPORTED_RESOLUTION.value


def test_failure_simulated_timeout(mock_adapter):
    """T2V_F07: Timeout simulation."""
    res = mock_adapter.generate(
        {
            "request_id": "F07",
            "prompt": "shot",
            "metadata": {"simulate_failure": "TIMEOUT"},
        }
    )
    assert res.status == "error"
    assert res.error.code == T2VErrorCode.TIMEOUT.value
    assert res.error.retryable is True


def test_failure_simulated_provider_error(mock_adapter):
    """T2V_F08: Provider outage simulation."""
    res = mock_adapter.generate(
        {
            "request_id": "F08",
            "prompt": "shot",
            "metadata": {"simulate_failure": "PROVIDER_ERROR"},
        }
    )
    assert res.status == "error"
    assert res.error.code == T2VErrorCode.PROVIDER_ERROR.value
    assert res.error.retryable is True


def test_failure_simulated_oom(mock_adapter):
    """T2V_F09: Out-of-memory simulation."""
    res = mock_adapter.generate(
        {
            "request_id": "F09",
            "prompt": "shot",
            "metadata": {"simulate_failure": "OOM"},
        }
    )
    assert res.status == "error"
    assert res.error.code == T2VErrorCode.OOM.value
    assert res.error.retryable is False


def test_failure_simulated_corrupt_output(mock_adapter):
    """T2V_F10: Output corruption detection."""
    res = mock_adapter.generate(
        {
            "request_id": "F10",
            "prompt": "shot",
            "metadata": {"simulate_failure": "OUTPUT_INVALID"},
        }
    )
    assert res.status == "error"
    assert res.error.code == T2VErrorCode.OUTPUT_INVALID.value


def test_failure_simulated_no_output(mock_adapter):
    """T2V_F11: Missing output file detection."""
    res = mock_adapter.generate(
        {
            "request_id": "F11",
            "prompt": "shot",
            "metadata": {"simulate_failure": "NO_OUTPUT"},
        }
    )
    assert res.status == "error"
    assert res.error.code == T2VErrorCode.NO_OUTPUT.value


def test_all_failure_fixtures_from_disk(mock_adapter):
    """Load and verify all 11 failure fixtures saved in mock_data/failure_cases/."""
    fixtures_dir = Path(__file__).resolve().parent.parent / "mock_data" / "failure_cases"
    fixture_files = list(fixtures_dir.glob("*.json"))
    assert len(fixture_files) >= 11, f"Expected at least 11 failure fixtures, found {len(fixture_files)}"

    for f_path in fixture_files:
        with open(f_path, "r", encoding="utf-8") as f:
            fixture = json.load(f)

        res = mock_adapter.generate(fixture["request"])
        assert res.status == fixture["expected_status"], f"Status mismatch in {f_path.name}"
        assert res.error is not None, f"Expected error details in {f_path.name}"
        assert (
            res.error.code == fixture["expected_error_code"]
        ), f"Error code mismatch in {f_path.name}: expected {fixture['expected_error_code']}, got {res.error.code}"
