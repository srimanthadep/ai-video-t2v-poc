"""Unit tests for engine/validator.py (ffprobe video validation)."""

from pathlib import Path
from engine.validator import validate_video


def test_validator_missing_file(tmp_path):
    """Ensure validator correctly flags missing file."""
    fake_path = str(tmp_path / "does_not_exist.mp4")
    val = validate_video(fake_path)
    assert val["valid"] is False
    assert val["exists"] is False
    assert any("does not exist" in err.lower() for err in val["errors"])


def test_validator_zero_byte_corrupt_file(tmp_path):
    """Ensure validator detects zero-byte empty or corrupted files."""
    corrupt_file = tmp_path / "corrupt.mp4"
    corrupt_file.touch()

    val = validate_video(str(corrupt_file))
    assert val["valid"] is False
    assert val["exists"] is True
    assert any("zero bytes" in err.lower() for err in val["errors"])


def test_validator_valid_video(mock_adapter, sample_valid_request):
    """Ensure validator accepts a valid generated video and reports media properties."""
    result = mock_adapter.generate(sample_valid_request)
    val = validate_video(result.video_path)

    assert val["valid"] is True
    assert val["playable"] is True
    assert val["codec"] == "h264"
    assert val["width"] == 832
    assert val["height"] == 480
    assert val["resolution"] == "832x480"
    assert val["fps"] is not None
    assert val["duration"] is not None


def test_validator_detects_duration_mismatch(mock_adapter, sample_valid_request):
    """Ensure validator flags when video duration significantly deviates from expected."""
    result = mock_adapter.generate(sample_valid_request)
    # Video is 5s, check if expect 10s
    val = validate_video(result.video_path, expected_params={"duration": 10.0})

    assert val["valid"] is False
    assert any("Duration mismatch" in err for err in val["errors"])


def test_validator_detects_resolution_mismatch(mock_adapter, sample_valid_request):
    """Ensure validator flags when video resolution deviates from expected."""
    result = mock_adapter.generate(sample_valid_request)
    # Video is 832x480, check if expect 1280x720
    val = validate_video(result.video_path, expected_params={"resolution": "1280x720"})

    assert val["valid"] is False
    assert any("Resolution mismatch" in err for err in val["errors"])
