# Technical Limitations & Boundary Analysis

**Module:** Member 5 — Text-to-Video POC  
**Author:** Srimanth  

---

## 1. Architectural & Duration Constraints

1. **Fixed Shot-Length Ceiling (~5 Seconds):**
   - Text-to-video diffusion natively generates short cinematic shots (81 frames at 16 FPS ≈ 5.0 seconds).
   - *Impact on Project:* T2V cannot directly render a complete 2-minute scene in a single inference call. It is designed to produce discrete, atomic shots that are later assembled on an editorial timeline.

2. **Inference Compute Profile:**
   - Full 14B parameter inference in unquantized precision requires substantial VRAM (>40 GB).
   - While FP8 quantization allows execution on 24GB consumer GPUs (RTX 3090/4090), high inference latencies (2–5 minutes per clip locally) make cloud serverless APIs (fal.ai, 30–45s) the recommended path for production workflows.

---

## 2. Semantic & Motion Limitations

1. **Multi-Vector Kinetic Conflicts:**
   - When a prompt specifies multiple conflicting directional vectors (e.g. Test Case `T2V_030`: *"A man walks left while the camera pans right, with a bird flying upward and rain falling sideways"*), diffusion transformers frequently average out conflicting vector fields, leading to motion blur, gliding physics, or directional drift.

2. **Multi-Subject Independence:**
   - Prompts requesting numerous distinct individuals performing unique, independent actions (e.g. Test Case `T2V_033`: *"Ten people in a circle each performing a different dance move simultaneously"*) push beyond current spatial cross-attention resolution, resulting in limb entanglement or identity bleeding.

3. **Incomplete / Ambiguous Prompts:**
   - When prompts lack descriptive grounding (e.g. `T2V_020` *"A person moves"*, `T2V_022` *"Nature."*), the model falls back to high-probability latent priors (often slow-motion stock footage aesthetics). While the generation succeeds technically, semantic specificity is low.

---

## 3. Scope Boundaries & Team Exclusions

The following capabilities are deliberately **out of scope** for Member 5:
- **Audio & Dialogue:** T2V models generate video frames only. Audio synthesis is handled by dedicated TTS/Foley modules.
- **Image-Conditioned Animation (I2V):** Image keyframing and character rigging belong to Member 6.
- **Multi-Shot Editorial Assembly:** Concatenating generated MP4 clips into continuous film sequences belongs to the assembly / timeline pipeline.
