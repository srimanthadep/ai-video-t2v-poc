# AI Video Generation POC — Member 5: Text-to-Video (T2V)

**Author:** Srimanth (Member 5)  
**Role:** Text-to-Video Shot Generation Engineer & Architect  
**Primary Model:** Wan2.2-T2V-A14B (Apache 2.0)  
**Primary Integration Strategy:** Option D — Mock Engine + Cloud API Adapter (fal.ai)  

---

## 1. Executive Summary

This repository contains the complete implementation for **Member 5 (Text-to-Video)** of the AI Video Generation Proof-of-Concept.

### Core Question Addressed
> *"Can a written description of a video shot be turned into a usable video clip?"*

The module accepts a natural language prompt describing a single shot (along with optional cinematographic constraints such as resolution, duration, and frame rate) and produces a verified, playable H.264 MP4 video clip accompanied by comprehensive structured generation metadata.

---

## 2. Manager Questions & Deliverables (Section 16 Answers)

Below are the direct answers to the 11 authoritative evaluation questions required by management:

### 1. What does your T2V module take as input?
The module consumes a validated `T2VRequest` schema containing:
- `prompt` (*string, required*): The written shot description.
- `duration_seconds` (*int, 1–10s, default: 5*): Length of the video shot.
- `resolution` (*string, default: "832x480"*): Supported dimensions (e.g., 832x480, 1280x720).
- `fps` (*int, 16/24/30, default: 16*): Frame rate.
- `model` (*string, default: "Wan2.2-T2V-A14B"*): Target AI model.
- `provider` (*string, default: "mock"*): Adapter backend (`mock` or `fal_ai`).
- `negative_prompt`, `seed`, `guidance_scale`, and `metadata` dict.

### 2. What does it produce as output?
A structured `T2VResult` object providing:
- `status`: `"success"` or `"error"`.
- `data_type`: Explicitly marked `"MOCK"` or `"REAL"`.
- `video_path`: Local path to verified playable H.264 MP4 file.
- Media parameters extracted directly from the video container via `ffprobe` (`duration_seconds`, `resolution`, `fps`, `codec`, `file_size_bytes`).
- Diagnostic metrics: `generation_time_seconds`, `cost_usd`, `model`, `seed`, and `error` details (code, message, retryable flag).

### 3. Which open-source option did you investigate and select?
We investigated the leading open-source models (Wan 2.2, CogVideoX-1.5, LTX-Video 2.5, HunyuanVideo 1.5, Open-Sora 2.0, Mochi-1).  
**Selected:** **Wan2.2-T2V-A14B** (API path) + **Wan2.2-TI2V-5B** (local consumer GPU fallback).

### 4. Why is it suitable for the POC?
- **Unrestricted License:** Apache 2.0 allows unrestricted experimentation and future commercialization without licensing royalties or geographic bans.
- **Pure T2V Specialization:** Generates clips directly from prompt text without requiring an input keyframe image.
- **MoE DiT Quality:** High-noise and low-noise expert routing delivers exceptional prompt adherence and cinematic quality at 14B active parameters.
- **API Availability:** Supported on serverless cloud providers (fal.ai, WaveSpeedAI) for ~$0.20/clip without requiring local $2,000+ GPUs.

### 5. What makes a generated clip usable?
A clip is considered usable if it meets four objective criteria:
1. **Container Integrity:** Valid H.264 MP4 container verified by `ffprobe` with non-zero byte size and playable video stream.
2. **Kinematic Adherence:** Matches requested duration (±0.75s) and frame rate.
3. **Semantic Grounding:** Depicts the primary subjects and actions requested in the prompt.
4. **Temporal Stability:** Maintains coherent subject identity without severe morphing or strobe artifacts.

### 6. What mock data did you create?
We generated a mock data package of **31 test cases**:
- **8 Normal / Simple prompts:** Common cinematic actions and lighting conditions.
- **4 Detailed prompts:** Multi-clause cinematographic styles, specific optics, and camera movements.
- **4 Incomplete / Ambiguous prompts:** Underspecified inputs testing default model behaviors.
- **4 Difficult prompts:** Complex spatial dynamics, extreme prompt length, reflections, and multi-agent action.
- **11 Failure Fixtures:** Explicit negative tests exercising validation boundaries and upstream outages.
- **21 Real playable mock MP4 videos** and **20 companion metadata files** indexed in `mock_data/manifest.json`.

### 7. Where did each mock-data type come from?
- Prompts were synthesized based on the team's production shot requirements.
- Mock MP4 videos were synthesized using our FFmpeg engine (`lavfi color` + `drawtext` filters), encoding request parameters and prompt previews directly onto video frames.
- Failure fixtures were mapped directly from the comprehensive Failure Matrix in Section 16 of our research plan.

### 8. Which files are mock and which are real AI outputs?
- **Mock outputs** are stored in `mock_data/videos/` and `outputs/mock/`, explicitly stamped with `data_type: "MOCK"` both in their metadata and burned directly into the visual video overlay.
- **Real outputs** are isolated to `outputs/real/` and stamped with `data_type: "REAL"`.

### 9. How do you test success and failure without consuming GPU time?
The `MockT2VAdapter` executes completely locally using CPU FFmpeg in ~0.2 seconds per video with zero GPU consumption and zero API costs. Simulated failure directives (`metadata.simulate_failure`) allow testing timeouts, provider crashes, out-of-memory errors, and corrupted files deterministically.

### 10. What happens when the prompt is incomplete or difficult?
- **Incomplete Prompts** (e.g. `"Nature."`): Pass schema validation, triggering default composition heuristics. In real models, this yields generic stock aesthetics without crashing.
- **Difficult Prompts** (e.g. contradictory vectors): Pass validation and generate output, but are flagged in benchmark quality reviews for potential motion blur or physics violations.

### 11. What generation information do you record?
Every generation records a complete `T2VResult` audit trail: request ID, prompt text, wall-clock latency, container parameters (`ffprobe`), seed, provider, model version, estimated cost, and error telemetry.

---

## 3. Architecture & Design

```
+-------------------------------------------------------------+
|                      Client / User / CLI                    |
+-------------------------------------------------------------+
                              | (T2VRequest)
                              v
+-------------------------------------------------------------+
|                  T2VEngine (Orchestrator)                   |
|  - Validates request schema                                 |
|  - Dispatches to configured adapter                         |
|  - Guarantees structured T2VResult even on fatal errors     |
+-------------------------------------------------------------+
                              |
              +---------------+---------------+
              |                               |
              v                               v
+---------------------------+   +---------------------------+
|      MockT2VAdapter       |   |      WanFalAIAdapter      |
|  - Fast local FFmpeg      |   |  - fal.ai cloud API       |
|  - Real playable MP4      |   |  - Wan2.2-T2V-A14B        |
|  - Failure simulation     |   |  - Retries & backoff      |
|  - data_type: "MOCK"      |   |  - data_type: "REAL"      |
+---------------------------+   +---------------------------+
              |                               |
              +---------------+---------------+
                              | (video path)
                              v
+-------------------------------------------------------------+
|               Output Validator (engine/validator.py)         |
|  - ffprobe container inspection                             |
|  - Codec, duration, resolution, fps verification           |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
|                      T2VResult (Output)                     |
+-------------------------------------------------------------+
```

---

## 4. Quick Start & Setup

### Prerequisites
1. **Python 3.10+** (tested on Python 3.14)
2. **FFmpeg & ffprobe** installed and on system `PATH` (Verify via `ffmpeg -version` and `ffprobe -version`)

### Installation

```bash
# Clone the repository
git clone https://github.com/srimanthadep/ai-video-t2v-poc.git
cd ai-video-t2v-poc

# Install dependencies
pip install -r requirements.txt
```

### Environment Configuration

```bash
# Copy example configuration template
copy .env.example .env

# Edit .env if you plan to run real API generations:
# FAL_KEY=your_key_here
```

---

## 5. Running the Demonstration

Run the automated CLI demonstration script to view successful and unsuccessful generation workflows:

```bash
# Run mock demonstration (instant, free, no GPU or API key required)
python demo/run_demo.py

# Optional: Run demonstration against real Wan 2.2 API (requires FAL_KEY in .env)
python demo/run_demo.py --provider fal_ai
```

---

## 6. Running Automated Tests

The repository includes a comprehensive test suite (40+ unit and integration tests):

```bash
# Run all automated tests
python -m pytest tests/ -v

# Run with test coverage report
python -m pytest tests/ -v --cov=.
```

---

## 7. Regenerating Mock Data Fixtures

To rebuild the entire mock data package (all 20 prompt JSONs, 11 failure fixtures, 20+ playable MP4s, metadata files, and `manifest.json`):

```bash
python mock_data/generate_fixtures.py
```

---

## 8. Repository Layout

```
ai-video-t2v-poc/
├── README.md                      # Authoritative project overview & manager answers
├── requirements.txt               # Pinned project dependencies
├── .env.example                   # Safe configuration template (NO SECRETS)
├── .gitignore                     # Git ignore rules protecting keys and binaries
├── schemas/                       # Pydantic data models
│   ├── __init__.py
│   ├── t2v_request.py             # T2VRequest specification & validation
│   └── t2v_result.py              # T2VResult & T2VErrorDetail specification
├── adapters/                      # T2V engine adapter implementations
│   ├── __init__.py
│   ├── base.py                    # T2VAdapter abstract base class & factory
│   ├── mock_adapter.py            # FFmpeg synthetic generator & failure simulator
│   └── wan_fal_adapter.py         # Real Wan 2.2 integration via fal.ai API
├── engine/                        # Core orchestration & validation
│   ├── __init__.py
│   ├── t2v_engine.py              # Facade orchestrator & exception boundary
│   ├── validator.py               # ffprobe output verification engine
│   └── errors.py                  # Structured error codes & custom exceptions
├── mock_data/                     # Complete mock data package
│   ├── generate_fixtures.py       # Fixture generator & manifest builder
│   ├── manifest.json              # Master manifest cataloging all 31 cases
│   ├── prompts/                   # 20 prompt JSON files across 4 categories
│   │   ├── normal/                # 8 simple/normal prompt cases
│   │   ├── detailed/              # 4 detailed cinematic prompt cases
│   │   ├── incomplete/            # 4 ambiguous/incomplete prompt cases
│   │   └── difficult/             # 4 difficult edge prompt cases
│   ├── failure_cases/             # 11 structured failure fixtures
│   ├── videos/                    # 20+ playable mock MP4 video files
│   └── metadata/                  # Per-video generation metadata JSON files
├── demo/                          # Demonstration scripts
│   ├── __init__.py
│   └── run_demo.py                # CLI demo showcasing success & error paths
├── outputs/                       # Runtime outputs
│   ├── mock/                      # Runtime mock video outputs
│   └── real/                      # Real AI-generated video outputs
├── benchmarks/                    # Empirical benchmarking system
│   ├── benchmark_template.json    # Standardized benchmark schema
│   ├── benchmark_results.json     # Empirical results (unfabricated)
│   └── README.md                  # Benchmarking methodology & rubric
├── docs/                          # In-depth technical documentation
│   ├── research.md                # T2V landscape & comparative evaluation
│   ├── model_selection.md         # Why Wan 2.2 was chosen
│   └── limitations.md             # Technical limitations & scope boundaries
└── tests/                         # Pytest automated test suite (40+ tests)
    ├── __init__.py
    ├── conftest.py                # Shared pytest fixtures
    ├── test_schemas.py            # Schema validation tests
    ├── test_mock_adapter.py       # Mock adapter & MP4 generation tests
    ├── test_output_validation.py  # ffprobe validation tests
    ├── test_failures.py           # Failure cases & error code tests
    ├── test_manifest.py           # Manifest integrity tests
    └── test_wan_api.py            # fal.ai adapter tests
```

---

## 9. Definition of Done Checklist

- [x] **T2V Module:** Functional and accessible via `T2VEngine` and `adapters`.
- [x] **Clear Input Definition:** Implemented in `schemas/t2v_request.py`.
- [x] **Clear Output Definition:** Implemented in `schemas/t2v_result.py`.
- [x] **Representative Test Set:** 20 prompt cases across 4 categories (`normal`, `detailed`, `incomplete`, `difficult`).
- [x] **Mock-Data Package:** 21 playable MP4s, 20 metadata JSONs, 11 failure fixtures, indexed in `mock_data/manifest.json`.
- [x] **Playable MP4 Videos:** Validated via `ffprobe` (H.264 container, correct duration/resolution/fps).
- [x] **Failure Cases:** 11 failure fixtures mapping to standard `T2VErrorCode` enum values.
- [x] **Automated Tests:** 42 pytest tests covering all components with 100% pass rate.
- [x] **Demonstration:** `demo/run_demo.py` showing successful and error generation workflows.
- [x] **Model Documentation:** Comprehensive documents in `docs/` and `README.md`.
- [x] **Mock vs Real Separation:** Strict tracking via `data_type` and separate output directories.
- [x] **Security:** Zero API keys or secrets committed; `.gitignore` and `.env.example` in place.