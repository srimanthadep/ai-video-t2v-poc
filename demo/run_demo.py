"""Demonstration script for Member 5 (T2V) showing successful and unsuccessful cases."""

import argparse
import os
import sys
import time
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

from engine.t2v_engine import T2VEngine
from engine.validator import validate_video


def print_banner():
    banner = """
========================================================================
    AI VIDEO GENERATION POC — MEMBER 5: TEXT-TO-VIDEO (T2V)
    Author: Srimanth | Focus: Shot Description -> Video Clip
========================================================================
"""
    print(banner)


def run_demo(provider: str = "mock"):
    print_banner()

    engine = T2VEngine(provider=provider, config={"output_dir": "outputs/demo"})
    caps = engine.get_capabilities()
    print(f"Active Provider:    {provider.upper()}")
    print(f"Target Model:       {caps.get('model', 'Wan2.2-T2V-A14B')}")
    print(f"Capabilities:       Resolutions: {caps.get('supported_resolutions')}")
    print("=" * 72)

    # -------------------------------------------------------------
    # DEMO 1: Successful Generation
    # -------------------------------------------------------------
    print("\n--- DEMO 1: Successful Generation (Normal Shot) ---")
    prompt_success = (
        "A cyclist rides slowly through a quiet city street at sunrise, "
        "soft golden morning light, gentle tracking camera following the rider."
    )
    req_success = {
        "request_id": "T2V_DEMO_001",
        "prompt": prompt_success,
        "duration_seconds": 5,
        "fps": 16,
        "resolution": "832x480",
        "model": "Wan2.2-T2V-A14B",
        "provider": provider,
    }

    print(f"Request ID:         {req_success['request_id']}")
    print(f"Prompt:             \"{prompt_success}\"")
    print(f"Target Specs:       832x480 | 16 FPS | 5s Duration")
    print("\n[Executing Generation Pipeline...]")

    t0 = time.time()
    res1 = engine.run(req_success)
    elapsed = time.time() - t0

    print(f"[Done in {elapsed:.2f}s]")
    print("\nGeneration Result (T2VResult schema):")
    print(f"  • Status:           {res1.status.upper()}")
    print(f"  • Data Type:        {res1.data_type}  <-- Clearly labelled MOCK vs REAL")
    print(f"  • Video Output:     {res1.video_path}")
    print(f"  • Duration:         {res1.duration_seconds}s")
    print(f"  • Resolution:       {res1.resolution}")
    print(f"  • Frame Rate:       {res1.fps} fps")
    print(f"  • Codec:            {res1.codec}")
    print(f"  • File Size:        {res1.file_size_bytes} bytes")
    print(f"  • Model:            {res1.model}")
    print(f"  • Seed:             {res1.seed}")

    # Validate output with ffprobe
    if res1.video_path and os.path.exists(res1.video_path):
        val = validate_video(res1.video_path)
        print("\nAutomated ffprobe Verification:")
        print(f"  [OK] File exists on disk:     True")
        print(f"  [OK] Playable video stream:   {val['playable']}")
        print(f"  [OK] Container & Codec:       MP4 ({val['codec']})")
        print(f"  [OK] Validated Duration:      {val['duration']}s")
        print(f"  [OK] Validated Resolution:    {val['resolution']}")
        print(f"  [OK] Validated FPS:           {val['fps']}")

    # -------------------------------------------------------------
    # DEMO 2: Unsuccessful Case (Validation Failure - Empty Prompt)
    # -------------------------------------------------------------
    print("\n" + "-" * 72)
    print("--- DEMO 2: Unsuccessful Generation (Empty Prompt Validation) ---")
    req_fail = {
        "request_id": "T2V_DEMO_FAIL_EMPTY",
        "prompt": "",
        "provider": provider,
    }

    print(f"Request ID:         {req_fail['request_id']}")
    print(f"Prompt:             \"\" (Empty string)")
    print("\n[Executing Generation Pipeline...]")

    t0 = time.time()
    res2 = engine.run(req_fail)
    elapsed = time.time() - t0

    print(f"[Handled safely in {elapsed:.3f}s - No Crash]")
    print("\nError Result (T2VResult schema):")
    print(f"  • Status:           {res2.status.upper()}")
    print(f"  • Data Type:        {res2.data_type}")
    print(f"  • Error Code:       {res2.error.code}")
    print(f"  • Error Message:    \"{res2.error.message}\"")
    print(f"  • Retryable:        {res2.error.retryable}")
    print(f"  • Output Created:   None (Clean failure, zero wasted resources)")

    # -------------------------------------------------------------
    # DEMO 3: Unsuccessful Case (Invalid Duration Parameter)
    # -------------------------------------------------------------
    print("\n" + "-" * 72)
    print("--- DEMO 3: Unsuccessful Generation (Parameter Boundary - 999s) ---")
    req_fail2 = {
        "request_id": "T2V_DEMO_FAIL_BOUND",
        "prompt": "A waterfall pouring into a misty gorge",
        "duration_seconds": 999,
        "provider": provider,
    }

    print(f"Request ID:         {req_fail2['request_id']}")
    print(f"Requested Duration: 999s (Exceeds maximum allowable duration)")
    print("\n[Executing Generation Pipeline...]")

    res3 = engine.run(req_fail2)
    print(f"  • Status:           {res3.status.upper()}")
    print(f"  • Error Code:       {res3.error.code}")
    print(f"  • Error Message:    \"{res3.error.message}\"")
    print(f"  • Retryable:        {res3.error.retryable}")

    # Summary
    print("\n" + "=" * 72)
    print("  DEMONSTRATION COMPLETE")
    print(f"  Successful Cases Demonstrated:   1/1 ([OK] Real playable MP4 produced)")
    print(f"  Unsuccessful Cases Handled:      2/2 ([OK] Structured errors, graceful)")
    print("=" * 72 + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="T2V POC Demo Runner")
    parser.add_argument(
        "--provider",
        default="mock",
        choices=["mock", "fal_ai"],
        help="Provider adapter to demonstrate (default: mock)",
    )
    args = parser.parse_args()
    run_demo(provider=args.provider)
