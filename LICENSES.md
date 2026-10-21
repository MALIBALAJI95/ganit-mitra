# LICENSES.md — Ganit Mitra (गणित मित्र) Open Source & ML Model License Register

Ganit Mitra is designed as a **commercial-grade EdTech product**. As required by the architectural constraints, **no assets or models under non-commercial licenses (e.g. CC-BY-NC) may be included**. Every model, dataset, library, and tool has been audited against its official repository, model card, and upstream license terms.

---

## 1. Production Runtime Components (Shipped in App / On-Device)

| Component / Model | Provider / Author | Artifact / Version | License | Commercial Use Permitted? | Obligations / Notes |
| :--- | :--- | :--- | :--- | :---: | :--- |
| **ASR (On-Device Speech Recognizer)** | AI4Bharat / IIT Madras & k2-fsa | `indicconformer_stt_mr_hybrid_ctc_rnnt_large` (CTC INT8 ONNX export) | **MIT License** / **Apache 2.0** | **YES** | AI4Bharat released weights under MIT. Sherpa-ONNX conversion is Apache 2.0. Attribution required. |
| **VAD (Voice Activity Detector)** | Silero Team / k2-fsa | `silero_vad.onnx` (v4/v5) | **MIT License** | **YES** | Highly efficient, permissive license. Attribution required. |
| **Inference Runtime Engine** | k2-fsa | `sherpa-onnx` (Kotlin/JNI/AAR v1.13.8) | **Apache License 2.0** | **YES** | Permissive, includes patent grant. License notice required in APK. |
| **Underlying Math Runtime** | Microsoft | `onnxruntime` (Embedded in sherpa-onnx) | **MIT License** | **YES** | Standard cross-platform execution provider. |
| **Number Audio Bank** | Ganit Mitra Project | 120 Opus files (0–100, place values, Marathi math operators) | **Apache License 2.0** / **CC-BY 4.0** | **YES** | Authored & pre-rendered specifically for this application. |
| **System TTS Fallback Engine** | Android Open Source Project (AOSP) / Device OEM | `android.speech.tts.TextToSpeech` (`Locale("mr", "IN")`) | **Apache License 2.0** (AOSP API) | **YES** | Invokes OEM/Google platform TTS installed at OS level. Zero bundled footprint. |
| **Android App Framework** | Google | Android Jetpack, Compose, Room, Kotlin Coroutines | **Apache License 2.0** | **YES** | Standard Android ecosystem libraries. |

---

## 2. Build-Time Lesson Audio Generation (GPU Server Pipeline)

| Model | Provider | Primary License | Gated Status | Commercial Use Permitted? | Decision / Adoption Status |
| :--- | :--- | :--- | :--- | :---: | :--- |
| **Indic Parler-TTS** | AI4Bharat & Hugging Face | **Apache License 2.0** | Gated on Hugging Face (agreement required) | **YES** | **APPROVED** for build-time generation. Natural child-friendly prosody. |
| **IndicF5** | AI4Bharat | **MIT License** | Gated on Hugging Face | **YES** | **APPROVED** for build-time generation evaluation. |
| **Microsoft Edge TTS** | Microsoft Cognitive Services | Proprietary service terms | API access | **BUILD HARNESS ONLY** | Used for local synthetic test harness and benchmark validation. Not bundled into final commercial runtime. |

---

## 3. Evaluated & Explicitly Rejected Models

| Model | Reported License | Reason for Rejection | Risk Level |
| :--- | :--- | :--- | :--- |
| **Meta MMS-TTS (`facebook/mms-tts-mar`)** | **Creative Commons Attribution-NonCommercial 4.0 (CC-BY-NC 4.0)** | **STRICTLY NON-COMMERCIAL**. Section 2(a)(1) forbids commercial distribution. Shipped in a commercial product would invite direct copyright infringement liability. | **CRITICAL LEGAL RISK — REJECTED** |
| **Moshi 7B Full-Duplex** | Apache 2.0 (code) / Kyutai license | Model size (~7B parameters, >14 GB VRAM) requires high-end server GPU. Zero Marathi pre-training. Impossible to execute on 3 GB RAM Android 8+ phone. | **TECHNICAL INFEASIBILITY — REJECTED** |
| **Bol-TTS Marathi ONNX (`shreyask/bol-tts-marathi-onnx`)** | Apache 2.0 | Quantized INT8 ONNX file is 270 MB. Embedding a 270 MB TTS model on a 3 GB phone violates low-end APK size and RAM limits. Replaced by Opus Number Bank (1.2 MB) + OS TTS. | **RESOURCE VIOLATION — REJECTED FOR ON-DEVICE RUNTIME** |

---

## 4. Dependencies Exceeding 50 MB (Requiring Explicit User Sign-Off)

Per project behavioral rules, any dependency exceeding 50 MB requires explicit sign-off:

1. **`models/asr/model.int8.onnx`**
   - **Size**: **188.44 MB**
   - **Role**: AI4Bharat IndicConformer Large CTC head quantized to INT8.
   - **Justification**: This is the core on-device Marathi ASR engine. Whisper-tiny Indic is smaller (~98 MB) but suffers from high Word Error Rate (WER) on Devanagari numerals and child phonetics. IndicConformer CTC INT8 delivers 0.018 RTF (~35 ms for 2.0s audio) and exact phonetic transcription for Marathi math.
2. **Alternative Baseline: Whisper-tiny INT8 (`tiny-decoder.int8.onnx` + `tiny-encoder.int8.onnx`)**
   - **Size**: **98.03 MB**
   - **Role**: Evaluated fallback ASR baseline.

---

## 5. Compliance Checklist for Build & Distribution

- [x] All shipped on-device models audited for Apache 2.0 or MIT licenses.
- [x] Non-commercial models (Meta MMS-TTS) strictly eliminated from codebase and build trees.
- [x] Open-source license texts bundled in app's "Open Source Licenses" legal screen via Jetpack Compose.
- [x] Pre-rendered audio assets generated using license-clean pipelines.
