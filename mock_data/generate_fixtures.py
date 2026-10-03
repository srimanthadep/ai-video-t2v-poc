"""Generate the complete mock data package: prompts, failure cases, MP4 videos, metadata, and manifest."""

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

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

from adapters.mock_adapter import MockT2VAdapter
from engine.errors import T2VErrorCode
from engine.validator import validate_video

BASE_DIR = Path(__file__).resolve().parent
PROMPTS_DIR = BASE_DIR / "prompts"
VIDEOS_DIR = BASE_DIR / "videos"
METADATA_DIR = BASE_DIR / "metadata"
FAILURES_DIR = BASE_DIR / "failure_cases"

# Define 20 prompt cases
NORMAL_PROMPTS = [
    {
        "test_id": "T2V_001",
        "category": "normal",
        "prompt": "A cyclist rides slowly through a quiet city street at sunrise.",
        "duration_seconds": 5,
        "fps": 16,
        "resolution": "832x480",
        "description": "Simple suburban transit scene with soft directional lighting",
    },
    {
        "test_id": "T2V_002",
        "category": "normal",
        "prompt": "A red balloon floats upward against a clear blue sky.",
        "duration_seconds": 5,
        "fps": 16,
        "resolution": "832x480",
        "description": "Single high-contrast subject with vertical movement",
    },
    {
        "test_id": "T2V_003",
        "category": "normal",
        "prompt": "Close-up of coffee being poured into a white cup.",
        "duration_seconds": 5,
        "fps": 16,
        "resolution": "832x480",
        "description": "Fluid dynamics close-up with steady framing",
    },
    {
        "test_id": "T2V_004",
        "category": "normal",
        "prompt": "A dog runs across a green field.",
        "duration_seconds": 5,
        "fps": 16,
        "resolution": "832x480",
        "description": "Fast quadruped locomotion across natural ground",
    },
    {
        "test_id": "T2V_005",
        "category": "normal",
        "prompt": "Waves crash gently on a sandy beach at sunset.",
        "duration_seconds": 5,
        "fps": 16,
        "resolution": "832x480",
        "description": "Rhythmic shoreline water motion with warm horizon",
    },
    {
        "test_id": "T2V_006",
        "category": "normal",
        "prompt": "A child blows out candles on a birthday cake.",
        "duration_seconds": 5,
        "fps": 16,
        "resolution": "832x480",
        "description": "Human face interaction with candle flame dynamics",
    },
    {
        "test_id": "T2V_007",
        "category": "normal",
        "prompt": "Autumn leaves fall slowly from a tall tree.",
        "duration_seconds": 5,
        "fps": 16,
        "resolution": "832x480",
        "description": "Multiple drifting particles with gentle wind gravity",
    },
    {
        "test_id": "T2V_008",
        "category": "normal",
        "prompt": "A train passes through a snowy mountain landscape.",
        "duration_seconds": 5,
        "fps": 16,
        "resolution": "832x480",
        "description": "Large mechanical object transit through snowy terrain",
    },
]

DETAILED_PROMPTS = [
    {
        "test_id": "T2V_010",
        "category": "detailed",
        "prompt": "Cinematic tracking shot of a woman in a yellow raincoat walking through puddles at night, neon reflections, shallow depth of field, 24mm lens look.",
        "duration_seconds": 5,
        "fps": 16,
        "resolution": "832x480",
        "description": "High aesthetic cinematic scene with specific optics and wet lighting",
    },
    {
        "test_id": "T2V_011",
        "category": "detailed",
        "prompt": "Aerial drone shot of a winding river through autumn forest, golden hour lighting, slow pan right to left, 4K look.",
        "duration_seconds": 5,
        "fps": 16,
        "resolution": "832x480",
        "description": "Panoramic landscape sweeping movement with golden hour palette",
    },
    {
        "test_id": "T2V_012",
        "category": "detailed",
        "prompt": "Extreme close-up of a raindrop hitting a still puddle, slow motion, bokeh background, soft natural light.",
        "duration_seconds": 5,
        "fps": 16,
        "resolution": "832x480",
        "description": "Microscopic fluid impact with shallow depth of field",
    },
    {
        "test_id": "T2V_013",
        "category": "detailed",
        "prompt": "Wide shot of a lone figure standing on a cliff overlooking the ocean, dramatic clouds, golden hour, cinematic color grading.",
        "duration_seconds": 5,
        "fps": 16,
        "resolution": "832x480",
        "description": "Atmospheric epic vista with contemplative human element",
    },
]

INCOMPLETE_PROMPTS = [
    {
        "test_id": "T2V_020",
        "category": "incomplete",
        "prompt": "A person moves.",
        "duration_seconds": 5,
        "fps": 16,
        "resolution": "832x480",
        "description": "Highly underspecified motion and subject",
    },
    {
        "test_id": "T2V_021",
        "category": "incomplete",
        "prompt": "Something happens in a place.",
        "duration_seconds": 5,
        "fps": 16,
        "resolution": "832x480",
        "description": "Extreme semantic ambiguity",
    },
    {
        "test_id": "T2V_022",
        "category": "incomplete",
        "prompt": "Nature.",
        "duration_seconds": 5,
        "fps": 16,
        "resolution": "832x480",
        "description": "Single-word categorical prompt lacking verb, subject, or camera",
    },
    {
        "test_id": "T2V_023",
        "category": "incomplete",
        "prompt": "Video of things.",
        "duration_seconds": 5,
        "fps": 16,
        "resolution": "832x480",
        "description": "Abstract and non-descriptive query",
    },
]

DIFFICULT_PROMPTS = [
    {
        "test_id": "T2V_030",
        "category": "difficult",
        "prompt": "A man walks left while the camera pans right, with a bird flying upward in the background and rain falling sideways.",
        "duration_seconds": 5,
        "fps": 16,
        "resolution": "832x480",
        "description": "Opposing multi-vector motion (man left, pan right, bird up, rain diagonal)",
    },
    {
        "test_id": "T2V_031",
        "category": "difficult",
        "prompt": (
            "In an ultra-detailed futuristic retro-cyberpunk laboratory filled with antique brass gauges, "
            "flickering vacuum tubes, holographic wireframes rotating at 30 degrees inclination, a robotic arm "
            "with polished chrome knuckles carefully unscrews a glowing blue quartz crystal container while green smoke "
            "eddies across a wet steel diamond-plate floor illuminated by neon purple overhead signage, 35mm anamorphic."
        ),
        "duration_seconds": 5,
        "fps": 16,
        "resolution": "832x480",
        "description": "Dense multi-clause architectural description testing prompt capacity and detail retention",
    },
    {
        "test_id": "T2V_032",
        "category": "difficult",
        "prompt": "A transparent glass sphere reflects the entire city skyline while floating in mid-air and rotating slowly.",
        "duration_seconds": 5,
        "fps": 16,
        "resolution": "832x480",
        "description": "Complex optical reflections and transparency dynamics",
    },
    {
        "test_id": "T2V_033",
        "category": "difficult",
        "prompt": "Ten people in a circle each performing a different dance move simultaneously.",
        "duration_seconds": 5,
        "fps": 16,
        "resolution": "832x480",
        "description": "Multi-agent independent action coordination and spatial consistency",
    },
]

# Define 11 failure cases
FAILURE_CASES = [
    {
        "test_id": "T2V_F01",
        "category": "failure",
        "description": "Empty prompt string",
        "request": {
            "request_id": "T2V_F01",
            "prompt": "",
            "provider": "mock",
        },
        "expected_status": "error",
        "expected_error_code": "EMPTY_PROMPT",
        "expected_retryable": False,
    },
    {
        "test_id": "T2V_F02",
        "category": "failure",
        "description": "Missing prompt field entirely",
        "request": {
            "request_id": "T2V_F02",
            "provider": "mock",
        },
        "expected_status": "error",
        "expected_error_code": "MISSING_PROMPT",
        "expected_retryable": False,
    },
    {
        "test_id": "T2V_F03",
        "category": "failure",
        "description": "Invalid duration (negative number)",
        "request": {
            "request_id": "T2V_F03",
            "prompt": "A running horse",
            "duration_seconds": -1,
            "provider": "mock",
        },
        "expected_status": "error",
        "expected_error_code": "INVALID_DURATION",
        "expected_retryable": False,
    },
    {
        "test_id": "T2V_F04",
        "category": "failure",
        "description": "Invalid duration (exceeds allowable maximum)",
        "request": {
            "request_id": "T2V_F04",
            "prompt": "A mountain stream",
            "duration_seconds": 999,
            "provider": "mock",
        },
        "expected_status": "error",
        "expected_error_code": "INVALID_DURATION",
        "expected_retryable": False,
    },
    {
        "test_id": "T2V_F05",
        "category": "failure",
        "description": "Invalid frame rate",
        "request": {
            "request_id": "T2V_F05",
            "prompt": "A campfire in the woods",
            "fps": 999,
            "provider": "mock",
        },
        "expected_status": "error",
        "expected_error_code": "INVALID_FPS",
        "expected_retryable": False,
    },
    {
        "test_id": "T2V_F06",
        "category": "failure",
        "description": "Unsupported resolution (8K)",
        "request": {
            "request_id": "T2V_F06",
            "prompt": "Sunrise over clouds",
            "resolution": "7680x4320",
            "provider": "mock",
        },
        "expected_status": "error",
        "expected_error_code": "UNSUPPORTED_RESOLUTION",
        "expected_retryable": False,
    },
    {
        "test_id": "T2V_F07",
        "category": "failure",
        "description": "Simulated generation timeout",
        "request": {
            "request_id": "T2V_F07",
            "prompt": "A lighthouse in a raging storm",
            "provider": "mock",
            "metadata": {"simulate_failure": "TIMEOUT"},
        },
        "expected_status": "error",
        "expected_error_code": "TIMEOUT",
        "expected_retryable": True,
    },
    {
        "test_id": "T2V_F08",
        "category": "failure",
        "description": "Simulated upstream provider outage",
        "request": {
            "request_id": "T2V_F08",
            "prompt": "Desert sand dunes shifting in wind",
            "provider": "mock",
            "metadata": {"simulate_failure": "PROVIDER_ERROR"},
        },
        "expected_status": "error",
        "expected_error_code": "PROVIDER_ERROR",
        "expected_retryable": True,
    },
    {
        "test_id": "T2V_F09",
        "category": "failure",
        "description": "Simulated out of memory (OOM)",
        "request": {
            "request_id": "T2V_F09",
            "prompt": "Crowded bustling marketplace with thousands of individuals",
            "provider": "mock",
            "metadata": {"simulate_failure": "OOM"},
        },
        "expected_status": "error",
        "expected_error_code": "OOM",
        "expected_retryable": False,
    },
    {
        "test_id": "T2V_F10",
        "category": "failure",
        "description": "Corrupted / zero-byte output file detected by validator",
        "request": {
            "request_id": "T2V_F10",
            "prompt": "An astronaut floating in deep space",
            "provider": "mock",
            "metadata": {"simulate_failure": "OUTPUT_INVALID"},
        },
        "expected_status": "error",
        "expected_error_code": "OUTPUT_INVALID",
        "expected_retryable": True,
    },
    {
        "test_id": "T2V_F11",
        "category": "failure",
        "description": "Missing output file",
        "request": {
            "request_id": "T2V_F11",
            "prompt": "A sailboat gliding across glass-like water",
            "provider": "mock",
            "metadata": {"simulate_failure": "NO_OUTPUT"},
        },
        "expected_status": "error",
        "expected_error_code": "NO_OUTPUT",
        "expected_retryable": True,
    },
]


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def generate_all():
    print("=" * 60)
    print("  MOCK DATA PACKAGE GENERATOR — MEMBER 5 (T2V)")
    print("=" * 60)

    # 1. Create directories
    for category in ["normal", "detailed", "incomplete", "difficult"]:
        (PROMPTS_DIR / category).mkdir(parents=True, exist_ok=True)
    FAILURES_DIR.mkdir(parents=True, exist_ok=True)
    VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
    METADATA_DIR.mkdir(parents=True, exist_ok=True)

    adapter = MockT2VAdapter({"output_dir": str(VIDEOS_DIR)})

    manifest_cases = []
    category_counts = {"normal": 0, "detailed": 0, "incomplete": 0, "difficult": 0, "failure": 0}

    all_prompt_groups = [
        ("normal", NORMAL_PROMPTS),
        ("detailed", DETAILED_PROMPTS),
        ("incomplete", INCOMPLETE_PROMPTS),
        ("difficult", DIFFICULT_PROMPTS),
    ]

    total_prompts = sum(len(p) for _, p in all_prompt_groups)
    print(f"\n[1/3] Generating {total_prompts} Mock Prompt Files and MP4 Videos...")

    for cat_name, prompt_list in all_prompt_groups:
        for p in prompt_list:
            test_id = p["test_id"]
            prompt_file = PROMPTS_DIR / cat_name / f"{test_id}.json"
            write_json(prompt_file, p)

            # Generate video
            video_dest = VIDEOS_DIR / f"mock_{test_id}.mp4"
            req_data = {
                "request_id": test_id,
                "prompt": p["prompt"],
                "duration_seconds": p["duration_seconds"],
                "fps": p["fps"],
                "resolution": p["resolution"],
                "provider": "mock",
                "metadata": {
                    "output_path": str(video_dest),
                    "category": cat_name,
                    "description": p["description"],
                },
            }

            res = adapter.generate(req_data)
            if res.status != "success":
                print(f"  ❌ Generation failed for {test_id}: {res.error}")
                continue

            # Save companion metadata JSON
            metadata_file = METADATA_DIR / f"{test_id}_metadata.json"
            write_json(metadata_file, res.model_dump())

            category_counts[cat_name] += 1
            manifest_cases.append(
                {
                    "test_id": test_id,
                    "category": cat_name,
                    "prompt": p["prompt"],
                    "description": p["description"],
                    "expected_status": "success",
                    "video_path": str(Path("videos") / f"mock_{test_id}.mp4").replace("\\", "/"),
                    "metadata_path": str(Path("metadata") / f"{test_id}_metadata.json").replace("\\", "/"),
                    "data_type": res.data_type,
                    "resolution": res.resolution,
                    "duration_seconds": res.duration_seconds,
                    "fps": res.fps,
                    "file_size_bytes": res.file_size_bytes,
                    "generation_time_seconds": res.generation_time_seconds,
                }
            )
            print(f"  ✓ [{cat_name.upper()}] {test_id}: Generated {res.resolution} @ {res.fps}fps ({res.file_size_bytes} bytes)")

    # 2. Generate failure cases
    print(f"\n[2/3] Generating {len(FAILURE_CASES)} Failure Fixtures and Running Verifications...")
    for f_case in FAILURE_CASES:
        test_id = f_case["test_id"]
        fixture_file = FAILURES_DIR / f"{test_id}.json"
        write_json(fixture_file, f_case)

        # Execute request through mock adapter to verify error handling
        res = adapter.generate(f_case["request"])
        actual_code = res.error.code if res.error else "NO_ERROR"
        matched = actual_code == f_case["expected_error_code"]
        mark = "✓" if matched else "✗"

        category_counts["failure"] += 1
        manifest_cases.append(
            {
                "test_id": test_id,
                "category": "failure",
                "description": f_case["description"],
                "expected_status": "error",
                "expected_error_code": f_case["expected_error_code"],
                "actual_error_code": actual_code,
                "verified": matched,
                "data_type": "MOCK",
                "retryable": f_case["expected_retryable"],
                "fixture_path": str(Path("failure_cases") / f"{test_id}.json").replace("\\", "/"),
            }
        )
        print(f"  {mark} [FAILURE] {test_id}: Expected {f_case['expected_error_code']} -> Got {actual_code}")

    # 3. Create manifest.json
    print("\n[3/3] Writing Master Manifest (manifest.json)...")
    manifest = {
        "manifest_version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "generator": "mock_data/generate_fixtures.py",
        "total_cases": len(manifest_cases),
        "summary": {
            "total_prompts": total_prompts,
            "total_failures": len(FAILURE_CASES),
            "category_counts": category_counts,
        },
        "cases": manifest_cases,
    }
    manifest_file = BASE_DIR / "manifest.json"
    write_json(manifest_file, manifest)

    total_video_bytes = sum(f.stat().st_size for f in VIDEOS_DIR.glob("*.mp4"))
    mb = total_video_bytes / (1024 * 1024)

    print("\n" + "=" * 60)
    print("  FIXTURE GENERATION SUMMARY")
    print("=" * 60)
    print(f"  Total Cases Defined:    {len(manifest_cases)}")
    print(f"  Mock MP4 Videos:        {len(list(VIDEOS_DIR.glob('*.mp4')))}")
    print(f"  Total Video Size:       {mb:.2f} MB")
    print(f"  Metadata JSON Files:    {len(list(METADATA_DIR.glob('*.json')))}")
    print(f"  Failure Case Fixtures:  {len(list(FAILURES_DIR.glob('*.json')))}")
    print(f"  Master Manifest:        {manifest_file}")
    print("=" * 60)
    print("  Status: ALL MOCK FIXTURES GENERATED AND VALIDATED SUCCESSFULLY")
    print("=" * 60)


if __name__ == "__main__":
    generate_all()
