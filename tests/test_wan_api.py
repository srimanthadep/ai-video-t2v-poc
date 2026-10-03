"""Tests for WanFalAIAdapter."""

import os
import pytest
from adapters.wan_fal_adapter import WanFalAIAdapter


def test_wan_fal_adapter_capabilities():
    """Verify capabilities exposed by the Wan 2.2 fal.ai adapter."""
    adapter = WanFalAIAdapter({"api_key": "test_dummy_key"})
    caps = adapter.get_capabilities()
    assert caps["provider"] == "fal_ai"
    assert "fal-ai/wan" in caps["model"]
    assert "832x480" in caps["supported_resolutions"]
    assert "real_ai_output" in caps["features"]


def test_wan_fal_adapter_missing_key_graceful(monkeypatch):
    """Verify adapter handles missing FAL_KEY gracefully without throwing unhandled exceptions."""
    monkeypatch.delenv("FAL_KEY", raising=False)
    adapter = WanFalAIAdapter({})
    assert adapter.health_check() is False

    res = adapter.generate({"request_id": "test_no_key", "prompt": "A galloping horse"})
    assert res.status == "error"
    assert res.data_type == "REAL"
    assert res.error is not None
    assert "FAL_KEY" in res.error.message


@pytest.mark.skipif(not os.getenv("FAL_KEY"), reason="FAL_KEY not set in environment")
def test_wan_fal_adapter_live_api():
    """Live API test for Wan 2.2 on fal.ai (only runs when FAL_KEY is present)."""
    adapter = WanFalAIAdapter({})
    assert adapter.health_check() is True

    req = {
        "request_id": "live_wan22_test",
        "prompt": "A tiny toy sailboat on a calm glass bowl",
        "resolution": "832x480",
    }
    res = adapter.generate(req)
    assert res.status == "success"
    assert res.data_type == "REAL"
    assert res.video_path is not None
