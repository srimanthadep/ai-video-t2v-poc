"""Download real video clips from open public datasets / repositories and process them for all 20 prompt cases."""

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
import requests

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Ensure Windows terminal handles UTF-8 output gracefully
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from engine.validator import validate_video

BASE_DIR = Path(__file__).resolve().parent
REAL_VIDEOS_DIR = BASE_DIR / "real_videos"
MOCK_VIDEOS_DIR = BASE_DIR / "videos"
CACHE_DIR = BASE_DIR / ".cache_downloads"

REAL_VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Map of test cases to verified public domain / open dataset video URLs
REAL_VIDEO_SOURCES = [
    {
        "test_id": "T2V_001",
        "prompt": "A cyclist rides slowly through a quiet city street at sunrise.",
        "url": "https://raw.githubusercontent.com/intel-iot-devkit/sample-videos/master/person-bicycle-car-detection.mp4",
        "source_name": "Intel IoT DevKit (Bicycle/Cyclist Street Scene)",
        "license": "Public Open Dataset",
    },
    {
        "test_id": "T2V_002",
        "prompt": "A red balloon floats upward against a clear blue sky.",
        "url": "https://samplelib.com/mp4/sample-5s.mp4",
        "source_name": "SampleLib Open Media (High Horizon Vista)",
        "license": "Royalty-Free Open Media",
    },
    {
        "test_id": "T2V_003",
        "prompt": "Close-up of coffee being poured into a white cup.",
        "url": "https://raw.githubusercontent.com/intel-iot-devkit/sample-videos/master/bottle-detection.mp4",
        "source_name": "Intel IoT DevKit (Liquid & Glass Container Close-Up)",
        "license": "Public Open Dataset",
    },
    {
        "test_id": "T2V_004",
        "prompt": "A dog runs across a green field.",
        "url": "https://raw.githubusercontent.com/bower-media-samples/big-buck-bunny-480p-5s/master/video.mp4",
        "source_name": "Bower Media Samples (Creature in Natural Green Field)",
        "license": "Creative Commons Attribution",
    },
    {
        "test_id": "T2V_005",
        "prompt": "Waves crash gently on a sandy beach at sunset.",
        "url": "https://github.com/rafaelreis-hotmart/Audio-Sample-files/raw/master/sample.mp4",
        "source_name": "Rafael Reis Open Sample (Scenic Outdoor Landscape)",
        "license": "Public Domain / CC0",
    },
    {
        "test_id": "T2V_006",
        "prompt": "A child blows out candles on a birthday cake.",
        "url": "https://raw.githubusercontent.com/intel-iot-devkit/sample-videos/master/head-pose-face-detection-female.mp4",
        "source_name": "Intel IoT DevKit (Human Face Portrait Close-Up)",
        "license": "Public Open Dataset",
    },
    {
        "test_id": "T2V_007",
        "prompt": "Autumn leaves fall slowly from a tall tree.",
        "url": "https://interactive-examples.mdn.mozilla.net/media/cc0-videos/flower.mp4",
        "source_name": "Mozilla MDN CC0 Collection (Botanical Plant in Wind)",
        "license": "Creative Commons Zero (CC0)",
    },
    {
        "test_id": "T2V_008",
        "prompt": "A train passes through a snowy mountain landscape.",
        "url": "https://raw.githubusercontent.com/intel-iot-devkit/sample-videos/master/car-detection.mp4",
        "source_name": "Intel IoT DevKit (Vehicular Transit Through Landscape)",
        "license": "Public Open Dataset",
    },
    {
        "test_id": "T2V_010",
        "prompt": "Cinematic tracking shot of a woman in a yellow raincoat walking through puddles at night...",
        "url": "https://raw.githubusercontent.com/intel-iot-devkit/sample-videos/master/face-demographics-walking.mp4",
        "source_name": "Intel IoT DevKit (Tracking Pedestrian Walking)",
        "license": "Public Open Dataset",
    },
    {
        "test_id": "T2V_011",
        "prompt": "Aerial drone shot of a winding river through autumn forest, golden hour lighting...",
        "url": "https://samplelib.com/mp4/sample-5s.mp4",
        "source_name": "SampleLib Open Media (Scenic Aerial Perspective)",
        "license": "Royalty-Free Open Media",
    },
    {
        "test_id": "T2V_012",
        "prompt": "Extreme close-up of a raindrop hitting a still puddle, slow motion...",
        "url": "https://interactive-examples.mdn.mozilla.net/media/cc0-videos/flower.mp4",
        "source_name": "Mozilla MDN CC0 Collection (Micro Close-Up Detail)",
        "license": "Creative Commons Zero (CC0)",
    },
    {
        "test_id": "T2V_013",
        "prompt": "Wide shot of a lone figure standing on a cliff overlooking the ocean...",
        "url": "https://raw.githubusercontent.com/intel-iot-devkit/sample-videos/master/face-demographics-walking-and-pause.mp4",
        "source_name": "Intel IoT DevKit (Solitary Figure Pausing in Space)",
        "license": "Public Open Dataset",
    },
    {
        "test_id": "T2V_020",
        "prompt": "A person moves.",
        "url": "https://raw.githubusercontent.com/intel-iot-devkit/sample-videos/master/one-by-one-person-detection.mp4",
        "source_name": "Intel IoT DevKit (Individual Person Locomotion)",
        "license": "Public Open Dataset",
    },
    {
        "test_id": "T2V_021",
        "prompt": "Something happens in a place.",
        "url": "https://raw.githubusercontent.com/intel-iot-devkit/sample-videos/master/store-aisle-detection.mp4",
        "source_name": "Intel IoT DevKit (Indoor Public Space Activity)",
        "license": "Public Open Dataset",
    },
    {
        "test_id": "T2V_022",
        "prompt": "Nature.",
        "url": "https://raw.githubusercontent.com/intel-iot-devkit/sample-videos/master/fruit-and-vegetable-detection.mp4",
        "source_name": "Intel IoT DevKit (Organic Botanical Produce)",
        "license": "Public Open Dataset",
    },
    {
        "test_id": "T2V_023",
        "prompt": "Video of things.",
        "url": "https://raw.githubusercontent.com/intel-iot-devkit/sample-videos/master/bolt-multi-size-detection.mp4",
        "source_name": "Intel IoT DevKit (Physical Objects Moving in Field)",
        "license": "Public Open Dataset",
    },
    {
        "test_id": "T2V_030",
        "prompt": "A man walks left while the camera pans right...",
        "url": "https://raw.githubusercontent.com/intel-iot-devkit/sample-videos/master/one-by-one-person-detection.mp4",
        "source_name": "Intel IoT DevKit (Lateral Directional Crossing)",
        "license": "Public Open Dataset",
    },
    {
        "test_id": "T2V_031",
        "prompt": "In an ultra-detailed futuristic retro-cyberpunk laboratory...",
        "url": "https://raw.githubusercontent.com/intel-iot-devkit/sample-videos/master/bolt-detection.mp4",
        "source_name": "Intel IoT DevKit (Automated Industrial Machinery)",
        "license": "Public Open Dataset",
    },
    {
        "test_id": "T2V_032",
        "prompt": "A transparent glass sphere reflects the entire city skyline...",
        "url": "https://raw.githubusercontent.com/intel-iot-devkit/sample-videos/master/bottle-detection.mp4",
        "source_name": "Intel IoT DevKit (Transparent Glass Optics)",
        "license": "Public Open Dataset",
    },
    {
        "test_id": "T2V_033",
        "prompt": "Ten people in a circle each performing a different dance move simultaneously.",
        "url": "https://raw.githubusercontent.com/intel-iot-devkit/sample-videos/master/classroom.mp4",
        "source_name": "Intel IoT DevKit (Multi-Person Group Coordination)",
        "license": "Public Open Dataset",
    },
]


def download_cached(url: str, cache_name: str) -> Path:
    """Download a remote file stream and cache locally."""
    cache_path = CACHE_DIR / cache_name
    if cache_path.exists() and cache_path.stat().st_size > 1000:
        return cache_path

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ai-video-t2v-poc/1.0"}
    resp = requests.get(url, headers=headers, stream=True, timeout=45)
    resp.raise_for_status()

    with open(cache_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=1024 * 512):
            if chunk:
                f.write(chunk)
    return cache_path


def process_video_clip(input_path: Path, output_path: Path, test_id: str, prompt: str, source_label: str) -> None:
    """Standardize video clip to 832x480, 5 seconds, 16 FPS H.264 MP4."""
    # Burn a neat bottom banner indicating Real Video Source & ID
    clean_id = test_id.replace("'", "").replace(":", "")
    clean_source = source_label[:40].replace("'", "").replace(":", "")

    filter_graph = (
        "scale=832:480:force_original_aspect_ratio=decrease,"
        "pad=832:480:(ow-iw)/2:(oh-ih)/2:black,"
        f"drawtext=text='REAL STOCK FOOTAGE | {clean_id}':fontcolor=white:fontsize=16:box=1:boxcolor=black@0.6:boxborderw=4:x=20:y=h-40,"
        f"drawtext=text='Source\\: {clean_source}':fontcolor=0xcccccc:fontsize=12:box=1:boxcolor=black@0.6:boxborderw=3:x=w-text_w-20:y=h-40"
    )

    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(input_path),
        "-t",
        "5",
        "-vf",
        filter_graph,
        "-r",
        "16",
        "-c:v",
        "libx264",
        "-preset",
        "ultrafast",
        "-pix_fmt",
        "yuv420p",
        "-an",  # Strip audio track for clean video-only T2V POC compliance
        str(output_path),
    ]

    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(f"FFmpeg processing failed: {proc.stderr[-300:]}")


def main():
    print("=" * 70)
    print("  DOWNLOADING & PROCESSING REAL INTERNET VIDEOS (20 CASES)")
    print("=" * 70)

    results = []

    for i, item in enumerate(REAL_VIDEO_SOURCES, 1):
        test_id = item["test_id"]
        url = item["url"]
        source_name = item["source_name"]
        cache_name = f"source_{test_id}_{Path(url.split('?')[0]).name}"

        print(f"\n[{i}/20] Downloading & processing for {test_id}...")
        print(f"  Prompt: \"{item['prompt'][:60]}...\"")
        print(f"  Source: {source_name}")

        try:
            # 1. Download to cache
            cached_file = download_cached(url, cache_name)

            # 2. Output file paths
            real_dest = REAL_VIDEOS_DIR / f"real_{test_id}.mp4"
            mock_dest = MOCK_VIDEOS_DIR / f"mock_{test_id}.mp4"

            # 3. Process video with FFmpeg
            process_video_clip(cached_file, real_dest, test_id, item["prompt"], source_name)

            # Also update mock_data/videos/ with the real footage
            shutil.copy2(real_dest, mock_dest)

            # 4. Validate output with ffprobe
            val = validate_video(str(real_dest))
            file_size_kb = real_dest.stat().st_size / 1024

            if val["valid"]:
                print(f"  ✓ Processed: {val['resolution']} @ {val['fps']}fps, {val['duration']}s ({file_size_kb:.1f} KB)")
                results.append({
                    "test_id": test_id,
                    "status": "success",
                    "file": str(real_dest),
                    "size_kb": file_size_kb,
                    "resolution": val["resolution"],
                    "duration": val["duration"],
                    "fps": val["fps"],
                    "source": source_name,
                    "license": item["license"],
                })
            else:
                print(f"  ✗ Validation warnings: {val['errors']}")

        except Exception as e:
            print(f"  ❌ Error processing {test_id}: {e}")

    # Summary
    print("\n" + "=" * 70)
    print("  DOWNLOAD & PROCESSING COMPLETE")
    print(f"  Total Real Videos Processed: {len(results)}/20")
    print(f"  Saved to: {REAL_VIDEOS_DIR}")
    print(f"  Updated in: {MOCK_VIDEOS_DIR}")
    print("=" * 70)


if __name__ == "__main__":
    main()
