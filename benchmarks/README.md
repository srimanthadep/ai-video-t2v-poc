# T2V Empirical Benchmarking Guide

This directory manages empirical benchmarking metrics for Text-to-Video generation in the Member 5 POC.

## Integrity Policy

> **Important**: Per engineering guidelines and scientific rigour, **no benchmark metrics are fabricated**. Synthetic mock runs are clearly designated as `data_type: MOCK` and excluded from model performance scorecards. `benchmark_results.json` records only real empirical measurements obtained when calling live AI backends (e.g. fal.ai Wan 2.2 API or local GPU inference).

---

## Planned Experiments Matrix (EXP-01 to EXP-10)

| ID | Objective | Resolution | Steps | Hardware / Provider | Key Metric Observed |
|:---|:---|:---:|:---:|:---|:---|
| **EXP-01** | Baseline T2V Generation | 832x480 | 40 | fal.ai Wan2.2-A14B | Generation latency, cost |
| **EXP-02** | Resolution Scaling (720p) | 1280x720 | 40 | fal.ai Wan2.2-A14B | Latency increase, fidelity |
| **EXP-03** | Step Count Impact (20 vs 40) | 832x480 | 20 | fal.ai Wan2.2-A14B | Speedup vs artifact density |
| **EXP-04** | Step Count Impact (50 steps) | 832x480 | 50 | fal.ai Wan2.2-A14B | Diminishing return point |
| **EXP-05** | Negative Prompt Efficacy | 832x480 | 40 | fal.ai Wan2.2-A14B | Visual defect suppression |
| **EXP-06** | Seed Determinism Check | 832x480 | 40 | fal.ai Wan2.2-A14B | Pixel-level consistency across identical seeds |
| **EXP-07** | High-Complexity Multi-Vector Scene | 832x480 | 40 | fal.ai Wan2.2-A14B | Physics, motion stability |
| **EXP-08** | Incomplete / Ambiguous Prompt Handling | 832x480 | 40 | fal.ai Wan2.2-A14B | Hallucination vs generic visual defaults |
| **EXP-09** | Turbo Variant Latency Comparison | 832x480 | Turbo | fal.ai Wan2.2-Turbo | Real-time viability (<10s) |
| **EXP-10** | Local GPU Inference (Fallback) | 720p | 40 | NVIDIA RTX 4090 (Wan2.2-TI2V-5B) | VRAM ceiling, FP8 throughput |

---

## Subjective Quality Scoring Rubric (1 to 5)

When evaluating real AI outputs, three 1–5 ordinal scales are used:

### 1. Visual Quality (VQ)
- **5 (Flawless):** Crisp edges, natural textures, photorealistic or consistent stylization, no visible blur or rendering glitches.
- **4 (Good):** Minor textural softness or brief compression artifact, overall high aesthetic standard.
- **3 (Acceptable):** Noticeable blur or temporal shimmer on fine details, but overall structure intact.
- **2 (Degraded):** Severe distortion, morphing objects, unnatural noise patterns.
- **1 (Unusable):** Incoherent visual noise or corrupted frames.

### 2. Prompt Adherence (PA)
- **5 (Exact):** All prompt entities, lighting specifications, actions, and camera movements faithfully depicted.
- **4 (Substantial):** Primary subjects and action depicted; subtle stylistic or minor atmospheric cues omitted.
- **3 (Partial):** Main subject present, but critical actions, directional vectors, or secondary elements missing.
- **2 (Poor):** Loose association with prompt topic; key subject misidentified or distorted.
- **1 (Ignored):** Completely unrelated scene rendered.

### 3. Motion Smoothness (MS)
- **5 (Cinematic):** Natural inertia, fluid camera pan, consistent physical kinematics.
- **4 (Smooth):** Good overall motion with slight micro-stutter at frame transitions.
- **3 (Tolerable):** Visible pacing jumps or rubber-banding motion.
- **2 (Jittery):** Significant flickering, sudden temporal jumps, or warping.
- **1 (Static/Broken):** Frozen frames or chaotic strobe effect.

---

## How to Record a Benchmark Run

When executing an experiment with an active API key:

```bash
# Run generation with benchmark logging
python demo/run_demo.py --provider fal_ai
```

Add the resulting output entry into `benchmarks/benchmark_results.json` matching `benchmarks/benchmark_template.json`.
