# Text-to-Video (T2V) Landscape Research

**Module:** Member 5 — Text-to-Video POC  
**Author:** Srimanth  
**Date:** October 2026  

---

## 1. Overview of Modern Open-Source T2V Models

The open-source Text-to-Video ecosystem has evolved rapidly from early 2D diffusion models to 3D Diffusion Transformers (DiT) utilizing spatial-temporal attention mechanisms.

### Core Architecture Paradigm
Modern video generators employ:
1. **Spatial-Temporal Video VAEs:** Compress raw video frames into compact 3D latent tensors (e.g. 16×16 spatial compression, 4× temporal compression).
2. **Text Encoders:** Large language models (T5, UMT5, or CLIP) encoding complex cinematic and directorial instructions into high-dimensional embeddings.
3. **Diffusion Transformers (DiT):** 3D full-attention or causal temporal attention predicting clean latent representations across iterative denoising steps.
4. **Mixture-of-Experts (MoE):** Advanced routing dividing denoising duties between high-noise experts (macro layout/composition) and low-noise experts (fine detail/texture).

---

## 2. Comparative Evaluation Matrix

| Model | Architecture | Active Parameters | License | Native Resolution | Native FPS | Min VRAM (Inference) | Cloud API Availability | POC Fit Score |
|:---|:---|:---:|:---|:---:|:---:|:---:|:---:|:---:|
| **Wan2.2-T2V-A14B** | MoE DiT (2x14B) | ~14B | **Apache 2.0** | 832x480, 1280x720 | 16 | 18–26 GB (FP8) | fal.ai, WaveSpeed, Replicate | ⭐⭐⭐⭐⭐ (Selected) |
| **Wan2.2-TI2V-5B** | Dense DiT | 5B | **Apache 2.0** | 1280x720 | 24 | ~23 GB (BF16) | fal.ai, WaveSpeed | ⭐⭐⭐⭐ (Local fallback) |
| **CogVideoX-1.5-5B** | 3D Causal DiT | 5B | Apache 2.0 | Up to 1360x768 | 16 | 9–24 GB | Moderate | ⭐⭐⭐⭐ |
| **LTX-Video 2.5** | Spatial DiT | 14B+ | Community Commercial Threshold | Up to 4K | 50 | 16–24 GB | Good | ⭐⭐⭐ (Exceeds POC scope) |
| **HunyuanVideo 1.5** | Dual-Stream DiT | 8.3B | Tencent Community (Geo-restricted) | 720p | Variable | 12–24 GB | Limited | ⭐⭐⭐ (Licensing risk) |
| **Open-Sora 2.0** | DiT | 11B | Apache 2.0 | 768p | Variable | 24 GB+ | Limited | ⭐⭐⭐ |
| **Mochi-1** | Asymmetric DiT | 10B | Apache 2.0 | 480p | 30 | 24–80 GB | Legacy | ⭐⭐ (Superseded) |

---

## 3. Key Observations & Findings

1. **Licensing Integrity is Paramount:** Models like HunyuanVideo provide impressive motion dynamics but carry terms excluding commercial deployment in specific geographic regions (UK/EU). Wan 2.2 provides an unencumbered **Apache 2.0** license.
2. **MoE Efficiency:** Wan 2.2's dual-expert MoE design allows active parameter scaling to 14B without incurring the computational latency of a monolithic 27B dense model.
3. **API Ecosystem Diversity:** Rather than depending on single-provider infrastructure, Wan 2.2 is hosted across multiple competitive cloud providers (fal.ai, WaveSpeedAI, Replicate), minimizing vendor lock-in.
