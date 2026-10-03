"""Unit tests for mock_data/manifest.json integrity."""

from pathlib import Path


def test_manifest_structure(manifest_data):
    """Verify top-level structure of manifest.json."""
    assert "manifest_version" in manifest_data
    assert "total_cases" in manifest_data
    assert "summary" in manifest_data
    assert "cases" in manifest_data
    assert manifest_data["total_cases"] >= 30


def test_manifest_category_counts(manifest_data):
    """Verify correct distribution across all 5 test categories."""
    counts = manifest_data["summary"]["category_counts"]
    assert counts["normal"] == 8
    assert counts["detailed"] == 4
    assert counts["incomplete"] == 4
    assert counts["difficult"] == 4
    assert counts["failure"] == 11


def test_manifest_mock_videos_exist_on_disk(manifest_data):
    """Verify that every mock video cataloged in manifest actually exists on disk."""
    base_mock_dir = Path(__file__).resolve().parent.parent / "mock_data"

    for case in manifest_data["cases"]:
        if case["expected_status"] == "success":
            video_rel_path = case["video_path"]
            full_video_path = base_mock_dir / video_rel_path
            assert full_video_path.exists(), f"Video file missing: {full_video_path}"
            assert full_video_path.stat().st_size > 0, f"Video is zero bytes: {full_video_path}"


def test_manifest_metadata_files_exist_on_disk(manifest_data):
    """Verify companion metadata files exist for all mock videos."""
    base_mock_dir = Path(__file__).resolve().parent.parent / "mock_data"

    for case in manifest_data["cases"]:
        if case["expected_status"] == "success":
            meta_rel_path = case["metadata_path"]
            full_meta_path = base_mock_dir / meta_rel_path
            assert full_meta_path.exists(), f"Metadata JSON missing: {full_meta_path}"
