# Model Selection Rationale: Wan 2.2

**Module:** Member 5 — Text-to-Video POC  
**Author:** Srimanth  
**Selected Primary Model:** `Wan2.2-T2V-A14B`  
**Selected Secondary / Local Fallback:** `Wan2.2-TI2V-5B`  

---

## 1. Executive Summary

For Member 5 (Text-to-Video shot generation), **Wan 2.2** emerged as the optimal open-source architecture for the AI Video Generation Proof-of-Concept. It satisfies all functional and non-functional requirements established by the team and management.

---

## 2. Selection Rationale

### A. True Open-Source Freedom (Apache 2.0)
Unlike competitor models that employ custom community licenses with annual revenue ceilings (e.g. LTX-Video) or geographic usage restrictions (e.g. Tencent HunyuanVideo), the Wan 2.2 model family is released under the **Apache 2.0** license. This grants complete freedom for academic exploration, prototyping, and future commercial deployment without legal risk.

### B. Pure Text-to-Video (T2V) Specialization
Member 5's dedicated responsibility in the team is evaluating whether **written descriptions alone** can be turned into usable video clips.
- Many newer models emphasize Image-to-Video (I2V), requiring a pre-generated image keyframe.
- Wan 2.2 features a dedicated `T2V-A14B` checkpoint specifically optimized for text-only conditioning, cleanly maintaining the boundary between Member 5 (T2V) and Member 6 (I2V/Animation).

### C. Mixture-of-Experts (MoE) Quality & Efficiency
Wan 2.2 uses a dual-expert design comprising two 14B parameter networks:
- **High-Noise Expert:** Dispatches during initial denoising timesteps to establish macro scene geometry, layout, and global lighting.
- **Low-Noise Expert:** Dispatches during final timesteps to render fine textures, facial micro-features, and smooth surface dynamics.
This architectural split allows Wan 2.2 to achieve visual fidelity comparable to 30B+ dense models while consuming inference compute proportional to a 14B model.

### D. Cloud API Diversity & Local Feasibility
1. **API Path (fal.ai):** Fully supported via the `fal-client` Python SDK at endpoint `fal-ai/wan/v2.2-a14b/text-to-video`. Generates 5s clips in ~30–45s on cloud A100/H100 infrastructure for ~$0.20/run.
2. **Local Fallback (5B):** For environments with consumer RTX 3090/4090 GPUs (24GB VRAM), the 5B variant can run locally using FP8/BF16 quantization under Diffusers or ComfyUI.

### E. Determinism and Negative Prompting
- **Seed Control:** Supports explicit integer seeds, ensuring exact temporal reproducibility required for benchmarking and pipeline testing.
- **Negative Prompting:** Allows explicit suppression of visual artifacts (e.g., `"flicker, blur, distorted hands, morphing"`).

---

## 3. Manager Questions Answered

### Q: Why is Wan 2.2 suitable for this POC?
> **Answer:** It provides state-of-the-art cinematic shot adherence, runs on affordable cloud APIs without local GPU purchase, operates under an unrestricted Apache 2.0 license, and isolates text-to-video logic completely from image conditioning.
