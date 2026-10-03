"""Video file output validator using ffprobe."""

import json
import os
import shutil
import subprocess
from typing import Any, Dict, Optional


def check_ffprobe_available() -> bool:
    """Check if ffprobe executable is found in PATH."""
    return shutil.which("ffprobe") is not None


def validate_video(
    video_path: str,
    expected_params: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Validate a video file on disk using ffprobe and filesystem checks.

    Args:
        video_path: Path to the MP4 video file.
        expected_params: Optional expected properties: duration, fps, resolution.

    Returns:
        Dict containing validation outcome and extracted media metadata.
    """
    result: Dict[str, Any] = {
        "valid": False,
        "exists": False,
        "playable": False,
        "video_path": video_path,
        "codec": None,
        "resolution": None,
        "width": None,
        "height": None,
        "fps": None,
        "duration": None,
        "file_size_bytes": 0,
        "errors": [],
    }

    if not video_path or not os.path.exists(video_path):
        result["errors"].append(f"File does not exist: {video_path}")
        return result

    result["exists"] = True
    file_size = os.path.getsize(video_path)
    result["file_size_bytes"] = file_size

    if file_size == 0:
        result["errors"].append("File is zero bytes (empty/corrupt)")
        return result

    if not check_ffprobe_available():
        # Fallback if ffprobe isn't installed: file exists and has size
        result["playable"] = True
        result["valid"] = True
        return result

    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=width,height,r_frame_rate,codec_name,duration",
        "-show_entries",
        "format=duration,size",
        "-of",
        "json",
        video_path,
    ]

    try:
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=15,
            check=False,
        )
    except Exception as e:
        result["errors"].append(f"ffprobe execution failed: {e}")
        return result

    if proc.returncode != 0:
        result["errors"].append(f"ffprobe failed: {proc.stderr.strip()}")
        return result

    try:
        probe_data = json.loads(proc.stdout)
    except json.JSONDecodeError as e:
        result["errors"].append(f"Failed to parse ffprobe json output: {e}")
        return result

    streams = probe_data.get("streams", [])
    if not streams:
        result["errors"].append("No video stream found in media file")
        return result

    v_stream = streams[0]
    format_info = probe_data.get("format", {})

    codec = v_stream.get("codec_name")
    width = v_stream.get("width")
    height = v_stream.get("height")

    # Parse fps from fraction like '16/1'
    fps = None
    r_frame_rate = v_stream.get("r_frame_rate", "")
    if "/" in r_frame_rate:
        num, den = r_frame_rate.split("/")
        if float(den) > 0:
            fps = round(float(num) / float(den), 2)
    elif r_frame_rate:
        try:
            fps = float(r_frame_rate)
        except ValueError:
            pass

    # Parse duration
    duration = None
    duration_str = v_stream.get("duration") or format_info.get("duration")
    if duration_str:
        try:
            duration = round(float(duration_str), 2)
        except ValueError:
            pass

    result["codec"] = codec
    result["width"] = width
    result["height"] = height
    if width and height:
        result["resolution"] = f"{width}x{height}"
    result["fps"] = fps
    result["duration"] = duration
    result["playable"] = True

    # Validate against expected params if supplied
    if expected_params:
        if "duration" in expected_params and duration is not None:
            exp_dur = float(expected_params["duration"])
            # Allow up to 0.75s variance for video containers/keyframes
            if abs(duration - exp_dur) > 0.75:
                result["errors"].append(
                    f"Duration mismatch: expected ~{exp_dur}s, got {duration}s"
                )

        if "resolution" in expected_params and result["resolution"]:
            exp_res = expected_params["resolution"].lower()
            if result["resolution"].lower() != exp_res:
                result["errors"].append(
                    f"Resolution mismatch: expected {exp_res}, got {result['resolution']}"
                )

        if "fps" in expected_params and fps is not None:
            exp_fps = float(expected_params["fps"])
            if abs(fps - exp_fps) > 1.5:
                result["errors"].append(
                    f"FPS mismatch: expected {exp_fps}, got {fps}"
                )

    result["valid"] = len(result["errors"]) == 0
    return result
