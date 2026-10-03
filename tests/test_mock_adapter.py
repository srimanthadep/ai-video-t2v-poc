"""Unit tests for MockT2VAdapter and T2VEngine integration."""

import os
from pathlib import Path
import pytest

from adapters.base import create_adapter
from adapters.mock_adapter import MockT2VAdapter
from engine.t2v_engine import T2VEngine
from engine.validator import validate_video


def test_mock_adapter_capabilities(mock_adapter):
    """Verify reported capabilities of the mock adapter."""
    caps = mock_adapter.get_capabilities()
    assert caps["provider"] == "mock"
    assert "832x480" in caps["supported_resolutions"]
    assert 16 in caps["supported_fps"]
    assert caps["min_duration_seconds"] == 1
    assert caps["max_duration_seconds"] == 10
    assert "h264_mp4" in caps["features"]


def test_mock_adapter_generate_success(mock_adapter, sample_valid_request):
    """Verify that MockT2VAdapter successfully generates a playable MP4."""
    result = mock_adapter.generate(sample_valid_request)

    assert result.status == "success"
    assert result.data_type == "MOCK"
    assert result.video_path is not None
    assert os.path.exists(result.video_path)
    assert result.file_size_bytes > 0
    assert result.codec == "h264"
    assert result.error is None


def test_mock_mp4_playable_via_ffprobe(mock_adapter, sample_valid_request):
    """Verify that generated mock MP4 is validated by ffprobe."""
    result = mock_adapter.generate(sample_valid_request)
    val = validate_video(result.video_path)

    assert val["exists"] is True
    assert val["playable"] is True
    assert val["valid"] is True
    assert val["codec"] == "h264"


def test_mock_mp4_duration_adherence(mock_adapter):
    """Verify generated video respects requested duration."""
    req = {
        "request_id": "test_dur_3s",
        "prompt": "Clouds drifting over peaks",
        "duration_seconds": 3,
        "fps": 16,
        "resolution": "832x480",
    }
    result = mock_adapter.generate(req)
    assert result.status == "success"
    assert abs(result.duration_seconds - 3.0) < 0.5


def test_mock_mp4_resolution_adherence(mock_adapter):
    """Verify generated video respects requested resolution."""
    req = {
        "request_id": "test_res_720p",
        "prompt": "Ocean waves",
        "duration_seconds": 2,
        "fps": 16,
        "resolution": "1280x720",
    }
    result = mock_adapter.generate(req)
    assert result.status == "success"
    assert result.resolution == "1280x720"


def test_mock_mp4_fps_adherence(mock_adapter):
    """Verify generated video respects requested FPS."""
    req = {
        "request_id": "test_fps_24",
        "prompt": "Bird taking flight",
        "duration_seconds": 2,
        "fps": 24,
        "resolution": "832x480",
    }
    result = mock_adapter.generate(req)
    assert result.status == "success"
    assert abs(result.fps - 24.0) < 1.0


def test_mock_data_type_is_explicitly_mock(mock_adapter, sample_valid_request):
    """Critical check: output must always be marked as MOCK data."""
    result = mock_adapter.generate(sample_valid_request)
    assert result.data_type == "MOCK"


def test_adapter_factory():
    """Verify create_adapter returns appropriate class."""
    adapter = create_adapter("mock")
    assert isinstance(adapter, MockT2VAdapter)

    with pytest.raises(ValueError) as exc_info:
        create_adapter("non_existent_provider_xyz")
    assert "Unsupported T2V provider" in str(exc_info.value)


def test_engine_orchestration_run(t2v_engine, sample_valid_request):
    """Verify T2VEngine processes requests end-to-end through mock adapter."""
    result = t2v_engine.run(sample_valid_request)
    assert result.status == "success"
    assert result.data_type == "MOCK"
    assert os.path.exists(result.video_path)
