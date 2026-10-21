# DECISION_LOG.md — Ganit Mitra Architectural & Engineering Decisions

## DECISION-001: Selection of Primary On-Device ASR Engine
- **Decision**: Adopt **AI4Bharat IndicConformer Marathi** (`ai4bharat/indicconformer_stt_mr_hybrid_ctc_rnnt_large`, CTC branch), quantized to **INT8 ONNX** (188.44 MB) and executed via **`k2-fsa/sherpa-onnx`** on CPU using `OfflineRecognizer.from_nemo_ctc`.
- **Alternatives Considered**:
  1. *Whisper-tiny/small Indic fine-tunes* (e.g. vasista22, OpenAI Whisper-tiny):
     - *Evaluation*: Whisper-tiny INT8 is 98.03 MB. However, Whisper uses an autoregressive encoder-decoder architecture susceptible to hallucinations, loop repetitions on background noise, higher inference latency (~150-250 ms), and degradation on isolated Marathi numerals.
  2. *EkStep Vakyansh Marathi wav2vec2*:
     - *Evaluation*: Uses an older acoustic model architecture with higher Word Error Rate on colloquial Marathi dialect accents.
  3. *IndicConformer RNN-T Head*:
     - *Evaluation*: The RNN-T (transducer) head requires two separate ONNX models (encoder + decoder/joiner) and higher runtime memory than CTC.
- **Rationale**:
  - IndicConformer CTC INT8 provides deterministic non-autoregressive decoding (zero hallucination loops).
  - Measured Cold Start: **136 ms** (Target: < 4,000 ms).
  - Measured 2.0s Audio Latency: **35.09 ms** (Real-Time Factor: **0.0175** — over 55x faster than real-time!).
  - License: MIT License (fully permissive, commercially safe).
  - Framework: sherpa-onnx offers first-class Kotlin/Java Android bindings, zero-dependency C++ runtime, and zero cloud calls.

---

## DECISION-002: Rejection of Moshi-Style 7B Full-Duplex Models
- **Decision**: **REJECT** any Moshi-style 7B end-to-end full-duplex speech-to-speech model.
- **Rationale**:
  1. **Memory Budget**: A 7B parameter model (even with 4-bit quantization) requires ~4.5 GB of RAM just for model weights, plus ~1.5 GB for KV-caches and audio buffers. The target hardware is a low-end Android phone with **3 GB of total system RAM** (where the OS typically limits an individual app heap to 512 MB). Loading a 7B model would cause an immediate Out-Of-Memory (OOM) crash.
  2. **Compute Requirements**: Moshi and similar multi-modal models require high-end desktop GPU inference (e.g. NVIDIA RTX 3090/4090 or Apple M-series Max chips) to maintain conversational latency. Low-end ARM Cortex-A53/A55 CPUs cannot sustain real-time execution.
  3. **Linguistic Deficiency**: Moshi and comparable open full-duplex systems are trained almost exclusively on English and French. They possess near-zero training on Marathi vocabulary, let alone Balbharati curriculum math terminology.
  4. **Pedagogical Requirement**: The product differentiator mandates exact, deterministic parsing and step-by-step arithmetic explanations. LLMs are notoriously prone to arithmetic hallucinations (e.g. carrying errors, off-by-one errors). Arithmetic must be performed by deterministic Kotlin code.

---

## DECISION-003: Rejection of Meta MMS-TTS (License Hazard)
- **Decision**: **REJECT** Meta MMS-TTS (`facebook/mms-tts-mar`) from any runtime or distribution pipeline.
- **Rationale**:
  - Meta MMS-TTS is released under the **Creative Commons Attribution-NonCommercial 4.0 International License (CC-BY-NC 4.0)**.
  - Section 2(a)(1) explicitly prohibits using the model for commercial advantages or monetary compensation.
  - Shipping MMS-TTS in a commercial EdTech application introduces catastrophic copyright infringement liability.
  - Approved Alternative: High-quality build-time synthesis using Apache 2.0 licensed models (Indic Parler-TTS) and on-device Opus Number Bank + Android System TTS (`Locale("mr", "IN")`).

---

## DECISION-004: Dynamic Voice Synthesis Architecture (Opus Number Bank + System TTS)
- **Problem**: When a child speaks a problem (e.g., "पंधरा मधून सात वजा केले तर?"), the app must immediately read back: "तू विचारलंस: १५ मधून ७ वजा केले तर किती?". Generating Marathi speech on-device with neural TTS models (e.g. Bol-TTS ONNX) adds 270 MB to the APK and consumes 400+ MB of RAM, violating the 3 GB device constraint. Simple syllable concatenation fails because Marathi numerals 1–100 are lexical and irregular (e.g. 11 is "अकरा", 21 is "एकवीस", 99 is "नव्व्याण्णव").
- **Decision**: Implement a **Two-Tier Hybrid Dynamic Speech Architecture**:
  1. **Tier 1: Pre-Synthesized Opus Number Bank (Primary for Math Read-Back & Answers)**:
     - Store pre-rendered Opus clips for:
       - Every integer 0 to 100 (101 clips).
       - Hundreds units (200, 300, 400, 500, 600, 700, 800, 900) and scale units ("हजार", "लाख").
       - Math operators and dialogue anchors ("अधिक", "वजा", "गुणिले", "भागिले", "बरोबर", "तू विचारलंस", "किती", "उत्तर").
     - Total storage footprint: **~180 KB** in 24 kbps Opus format.
     - Latency: **< 1 ms** (instant audio buffer concatenation in memory).
     - Quality: Studio-grade native Marathi neural pronunciation without any runtime synthesis lag or distortion.
  2. **Tier 2: Android System `TextToSpeech` (Fallback for Unstructured Text)**:
     - Utilize the native Android OS speech engine (`android.speech.tts.TextToSpeech` configured with `Locale("mr", "IN")`).
     - Available on virtually all Indian-market Android 8+ devices through Google Speech Services.
     - Footprint: **0 MB added to APK**, executes in an isolated OS process outside the app's memory heap.

---

## DECISION-005: Authored Lessons Pre-Synthesis Pipeline (Build-Time GPU)
- **Decision**: Authored conceptual math lessons (classes 1–6) are generated **at build-time on a GPU server** using **Indic Parler-TTS** (Apache 2.0) and compressed to **Opus audio format** accompanied by JSON synchronized transcripts.
- **Rationale**:
  - Running heavy neural TTS models during runtime drains phone battery and takes seconds on low-end hardware.
  - Pre-synthesizing authored content at build time guarantees 100% fluent, warm, child-friendly Marathi audio with exact pedagogical inflection.
  - Synchronized JSON timestamps allow on-screen visuals (place-value blocks, number lines, apples/marbles) to highlight in exact lock-step with the spoken audio.

---

## DECISION-006: Confidence Gating via CTC Posteriors
- **Decision**: Extract frame-level CTC log-posteriors directly from the model's output tensor (`logprobs [batch, time, 5633]`) to compute:
  - **Per-Token Posterior**: $p(w_i) = \max_{t \in \text{align}(w_i)} \exp(\text{logprobs}[t, \text{id}(w_i)])$
  - **Utterance Confidence**: Geometric mean of token posteriors $\bar{C} = \left( \prod_{i=1}^N p(w_i) \right)^{1/N}$
  - **Minimum Token Confidence**: $C_{\min} = \min_{i} p(w_i)$ (specifically catches misheard single digits).
- **Gating Protocol**:
  - *Commands* ("हो", "नाही", "पुढचा", "पुन्हा"):
    - $\bar{C} \ge 0.85$: Immediate execution.
    - $0.60 \le \bar{C} < 0.85$: Confirm with one-tap dialogue ("'हो' म्हणायचं आहे का?").
    - $\bar{C} < 0.60$: Prompt "परत सांग" and illuminate tap buttons.
  - *Math Expressions & Numerical Answers*:
    - **MANDATORY READ-BACK**: Always read back what was understood ("तू विचारलंस: १२ + ५?") regardless of confidence score. Misheard numbers are mathematically critical; confirmation ensures 100% child agency and error prevention.
  - *Fallback*: Large, high-contrast touch keypad fallback is always visible on-screen. Voice failure never blocks progress.

---

## DECISION-007: Single-Model RAM Lifecycle (Strict Lazy Loading)
- **Constraint**: Low-end 3 GB RAM Android device; app heap limit ~512 MB.
- **Decision**: Enforce a strict single-model RAM lifecycle managed by a `SpeechEngineLifecycleManager`:
  - **During Listening/Speech Input**:
    1. Silero VAD runs continuously in memory (~1.8 MB RAM).
    2. Once speech is detected and buffered, IndicConformer CTC INT8 model is loaded / retained.
  - **During Playback/Audio Feedback**:
    - The ASR decoder is paused; raw audio buffers are released.
    - Audio Bank player reads compressed Opus buffers directly into Android `AudioTrack` or `MediaPlayer`.
  - Peak resident memory never exceeds **~210 MB** in native runtime.

---

## DECISION-008: Strict 100% Offline Enforcement
- **Decision**:
  - Remove all network permissions from `AndroidManifest.xml` (`android.permission.INTERNET` is strictly omitted).
  - No analytics SDKs (no Firebase, no telemetry, no tracking).
  - Automated CI airplane-mode instrumented tests and network socket monitoring tests to verify 0 open sockets.
  - Build flavor `offlineStrict` with network security config explicitly blocking cleartext and secure traffic.
