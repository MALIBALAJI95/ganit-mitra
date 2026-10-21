# LICENSES.md — Ganit Mitra (गणित मित्र) Open Source & ML Model License Register

Ganit Mitra is designed as a **commercial-grade EdTech product**. As required by the architectural constraints, **no assets or models under non-commercial licenses (e.g. CC-BY-NC) may be included in the product build or shipped in any form**. Every model, dataset, library, and tool has been audited against its official repository, model card, and upstream license terms.

---

## 1. Production Runtime Components (Shipped in App / On-Device)

| Component / Model | Provider / Author | Artifact / Version | Upstream License & Evidence URL | Commercial Use Permitted? | Obligations & Notes |
| :--- | :--- | :--- | :--- | :---: | :--- |
| **ASR (Primary Speech Model)** | AI4Bharat / IIT Madras | `indicconformer_stt_mr_hybrid_ctc_rnnt_large` (CTC head INT8 ONNX export) | **MIT License**<br>Official URL: [ai4bharat/indicconformer_stt_mr_hybrid_ctc_rnnt_large](https://huggingface.co/ai4bharat/indicconformer_stt_mr_hybrid_ctc_rnnt_large)<br>*Card metadata: `license: mit`* | **YES** | Converted to INT8 ONNX. Permissive license allows commercial use, modification, and bundling. Copyright notice preserved. |
| **VAD (Voice Activity Detector)** | Silero Team / k2-fsa | `silero_vad.onnx` (v4/v5) | **MIT License**<br>Official URL: [snakers4/silero-vad](https://github.com/snakers4/silero-vad) | **YES** | Permissive, low footprint. Attribution preserved. |
| **Inference Engine** | k2-fsa | `sherpa-onnx` (Android Kotlin/AAR v1.13.8) | **Apache License 2.0**<br>Official URL: [k2-fsa/sherpa-onnx](https://github.com/k2-fsa/sherpa-onnx) | **YES** | Permissive with patent grant. License notice included in App About/Legal section. |
| **Underlying Math Runtime** | Microsoft | `onnxruntime` (Embedded in sherpa-onnx) | **MIT License**<br>Official URL: [microsoft/onnxruntime](https://github.com/microsoft/onnxruntime) | **YES** | Standard cross-platform execution provider. |
| **Number Audio Bank** | Ganit Mitra Project | 135 Opus files (0–100 irregular words, place values, fractions, operators) | **Apache License 2.0** / **CC-BY 4.0** | **YES** | Project authored and pre-rendered. Shipped inside `assets/audio/bank/`. |
| **System TTS Engine Fallback** | Android Open Source Project (AOSP) / Device OEM | `android.speech.tts.TextToSpeech` (`Locale("mr", "IN")`) | **Apache License 2.0** (AOSP platform API) | **YES** | Zero bundled APK footprint. Calls OS-level Marathi voice installed on device. |
| **Android Framework & UI** | Google | Jetpack Compose, Room, Kotlin Coroutines | **Apache License 2.0** | **YES** | Standard modern Android runtime components. |

---

## 2. Build-Time Lesson Audio Generation (GPU Pipeline)

| Model | Provider | Primary License & URL | Gated Status | Commercial Terms on Audio Outputs | Decision & Adoption Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Indic Parler-TTS** | AI4Bharat & Hugging Face | **Apache License 2.0**<br>URL: [ai4bharat/indic-parler-tts](https://huggingface.co/ai4bharat/indic-parler-tts) | Gated on HF (requires accepting terms) | **Unrestricted commercial use of generated audio output.** Apache 2.0 applies to code/weights; no output copyright claimed by licensor. | **APPROVED PRIMARY** for build-time lesson generation. Highest naturalness on child-appropriate sentences. |
| **IndicF5** | AI4Bharat | **MIT License**<br>URL: [ai4bharat/IndicF5](https://huggingface.co/ai4bharat/IndicF5) | Gated on HF | **Unrestricted commercial use of generated audio output.** | **APPROVED ALTERNATIVE** for evaluation. |
| **Bol-TTS Marathi** | Shreyas Karnik | **Apache License 2.0**<br>URL: [shreyask/bol-tts-marathi](https://huggingface.co/shreyask/bol-tts-marathi) | Ungated | **Unrestricted commercial use of generated audio output.** | **APPROVED FALLBACK**. |

---

## 3. Desktop Test Harness Tooling (NEVER Shipped in App)

| Tool / Service | Purpose | Terms & Policy | Commercial Status |
| :--- | :--- | :--- | :--- |
| **Microsoft Edge TTS (`edge-tts`)** | Desktop test harness only: generates synthetic Marathi utterances to benchmark ASR with noise/speed variations. | Microsoft Online Services terms. | **STRICTLY NEVER SHIPPED**. Used solely on developer laptop for creating simulated test benches (`benchmarks/run_perturbed_eval.py`). All results labeled **SIMULATED**. Zero code or assets from edge-tts are packaged in the APK. |

---

## 4. Evaluated & Explicitly Rejected Models

| Model | Official License | Reason for Rejection | Risk Category |
| :--- | :--- | :--- | :--- |
| **Meta MMS-TTS (`facebook/mms-tts-mar`)** | **Creative Commons Attribution-NonCommercial 4.0 (CC-BY-NC 4.0)**<br>URL: [facebook/mms-tts-mar](https://huggingface.co/facebook/mms-tts-mar) | **STRICT NON-COMMERCIAL PROHIBITION**. Section 2(a)(1) forbids commercial distribution. Bundling or shipping this model in a commercial EdTech product would create severe copyright infringement liability. | **CRITICAL LEGAL RISK — REJECTED** |
| **Moshi 7B Full-Duplex** | Apache 2.0 (code) / Kyutai license | Model size (~7B parameters, $>14\text{ GB}$ VRAM) requires high-end server GPU. Zero Marathi language pretraining. Incompatible with target 3 GB RAM Android 8+ phone. | **TECHNICAL INFEASIBILITY — REJECTED** |
| **Bol-TTS Marathi ONNX (`shreyask/bol-tts-marathi-onnx`)** | Apache 2.0 | Quantized INT8 model is **270.07 MB**. Bundling a 270 MB TTS model on a budget phone violates memory and APK limits. Replaced by Opus Number Bank (220 KB) + OS TTS. | **RESOURCE VIOLATION — REJECTED FOR ON-DEVICE RUNTIME** |

---

## 5. Dependencies Exceeding 50 MB (Requiring Explicit Sign-Off)

Per project behavioral rules, dependencies exceeding 50 MB are logged and tracked:

1. **`models/asr/model.int8.onnx`**
   - **Size**: **188.44 MB** (or in-house export at **133.91 MB**)
   - **Role**: AI4Bharat IndicConformer Marathi CTC INT8 ONNX model.
   - **Sign-off Status**: **APPROVED by User** for Phase 1.
   - **Justification**: Minimum viable quantization delivering exact Marathi Devanagari numerals and math operators with RTF of 0.018.

---

## 6. Official License Verifications Recorded

### AI4Bharat IndicConformer STT Marathi
- **Model Card URL**: `https://huggingface.co/ai4bharat/indicconformer_stt_mr_hybrid_ctc_rnnt_large`
- **Official License Field**: `license: mit`
- **Text**: *"The model is licensed under the MIT License. Copyright (c) 2023 AI4Bharat, IIT Madras. Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files..."*

### AI4Bharat Indic Parler-TTS
- **Model Card URL**: `https://huggingface.co/ai4bharat/indic-parler-tts`
- **Official License Field**: `license: apache-2.0`
- **Text**: *"Licensed under the Apache License, Version 2.0 (the 'License'); you may not use this file except in compliance with the License..."*
