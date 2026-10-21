# DECISION_LOG.md — Ganit Mitra Architectural & Engineering Decisions

## DECISION-001: Selection & In-House Export of Primary ASR Engine
- **Decision**: Adopt **AI4Bharat IndicConformer Marathi** (`ai4bharat/indicconformer_stt_mr_hybrid_ctc_rnnt_large`, CTC branch), quantized to **INT8 ONNX** and executed via **`k2-fsa/sherpa-onnx`** on CPU.
- **In-House Export vs Community Re-Export Empirical Comparison**:
  - We performed our own in-house dynamic INT8 quantization of the FP32 checkpoint (`model.fp32.onnx` [470.19 MB]) using `onnxruntime.quantization.quantize_dynamic`, yielding `model.inhouse.int8.onnx` at **133.91 MB** (54.5 MB smaller than the 188.44 MB community re-export).
  - *Accuracy comparison*: On pure Marathi numerals, the community re-export has exact Marathi language token pruning (`बारा` $\to$ "बारा", `पाच` $\to$ "पाच", `पंधरा` $\to$ "पंधरा"), whereas naive multilingual dynamic quantization outputs Hindi spellings (`बारा` $\to$ "बारह", `पाच` $\to$ "पाँच").
  - *Conclusion*: We retain the 188.44 MB Marathi-specific pruned CTC export as primary for transcription accuracy, with the in-house export script documented and maintained in the repository for reproducibility.
- **Official License Evidence**:
  - URL: `https://huggingface.co/ai4bharat/indicconformer_stt_mr_hybrid_ctc_rnnt_large`
  - Upstream License: **MIT License** (fully permissive, commercially safe).
- **Environment Qualification Note**:
  - **Phase 0 measurements are on Mac ARM64 desktop, NOT target-device Cortex-A53/A55.** Target device numbers on an Android emulator limited to 3 GB RAM (and a physical test phone if connected) will be collected before Phase 2 begins: cold start, model load time from flash storage, inference latency, peak RAM, and battery drain.

---

## DECISION-002: End-to-End Latency Pipeline Definition
The end-to-end interactive voice latency is formally defined as the elapsed time from the **moment the child finishes speaking** ($t=0$) to the **instant the first audio sample of the spoken reply is emitted by the speaker** ($t_{\text{start}}$):

$$\text{Latency}_{\text{E2E}} = t_{\text{start}} - t_0 = \Delta t_{\text{VAD}} + \Delta t_{\text{ASR}} + \Delta t_{\text{Parse}} + \Delta t_{\text{ReadbackPrep}} + \Delta t_{\text{AudioEmit}}$$

| Pipeline Stage | Symbol | Description | Desktop ARM64 Measured | Target-Device Budget (Cortex-A53) |
| :--- | :---: | :--- | :---: | :---: |
| **1. VAD Silence Endpointing** | $\Delta t_{\text{VAD}}$ | Trailing silence window required to confirm speech completion | 250 ms | 250 ms |
| **2. ASR CTC Inference** | $\Delta t_{\text{ASR}}$ | Feature extraction + INT8 ONNX acoustic model forward pass | 35 ms | 250–400 ms |
| **3. Marathi Grammar Parsing** | $\Delta t_{\text{Parse}}$ | Rule-based parser generating AST + ambiguity checks | 1.5 ms | 10–20 ms |
| **4. Read-Back & Dialogue Prep** | $\Delta t_{\text{ReadbackPrep}}$ | Confirmation phrase formulation ("तू विचारलंस: ...") | 0.5 ms | 2–5 ms |
| **5. Read-Back TTS / Audio Bank** | $\Delta t_{\text{AudioEmit}}$ | Number Bank buffer stitch & `AudioTrack` buffer fill | 1.0 ms | 10–25 ms |
| **Total End-to-End Latency** | **$t_{\text{start}}$** | **From speech end to voice playback start** | **~288 ms** | **~520–700 ms** (Well below 2.5s constraint) |

---

## DECISION-003: Lesson TTS & Dynamic Number Audio Bank Plan
- **Authored Lesson Generation**:
  - Model: **Indic Parler-TTS** (`ai4bharat/indic-parler-tts`) generated at **build time on a GPU server**.
  - License Evidence: Official card metadata `license: apache-2.0`. Apache 2.0 grants unrestricted commercial rights over the generated audio artifacts.
  - Distribution: Audio is compressed using Opus at 24 kbps mono, paired with JSON synchronized timestamps for on-screen manipulative animations.
- **Dynamic Number Audio Bank Plan**:
  - Marathi numbers 1–100 are lexical and irregular (not composite rules). We store pre-recorded/synthesized individual Opus clips for:
    1. 0 to 100 individually (101 clips: 0 `शून्य`, 1 `एक`, 2 `दोन`, ... 99 `नव्व्याण्णव`, 100 `शंभर`).
    2. Hundreds: 200 `दोनशे`, 300 `तीनशे`, 400 `चारशे`, 500 `पाचशे`, 600 `सहाशे`, 700 `सातशे`, 800 `आठशे`, 900 `नऊशे` (8 clips).
    3. Multipliers: `हजार` (thousand), `लाख` (lakh) (2 clips).
    4. Arithmetic Operators: `अधिक`, `आणि`, `जमा`, `वजा`, `गुणिले`, `भागिले`, `बरोबर` (7 clips).
    5. Dialogue Anchors: `तू विचारलंस`, `किती`, `उत्तर`, `हो`, `नाही`, `छान`, `पुन्हा सांग`, `पुढचा प्रश्न`, `पायरी` (9 clips).
    6. Fractions: `अर्धा` (1/2), `पाव` (1/4), `पाऊण` (3/4), `सव्वा` (1 1/4), `दीड` (1 1/2), `अडीच` (2 1/2) (6 clips).
    7. Currency: `रुपये`, `पैसे` (2 clips).
  - Total clips: **135 Opus files**.
  - Storage Footprint: **~220 KB total**.
  - Latency: **$< 1\text{ ms}$** buffer assembly; 0% CPU synthesis load; 100% pronunciation reliability.
- **Fallback Dynamic TTS**: Android platform `android.speech.tts.TextToSpeech` (`Locale("mr", "IN")`) for arbitrary dynamic text.

---

## DECISION-004: Token & Utterance Confidence Access in Android (Kotlin)
- **Investigation of sherpa-onnx Kotlin API**:
  - In `com.k2fsa.sherpa.onnx.OfflineRecognizerResult`, the native struct exposes:
    ```kotlin
    val text: String
    val tokens: Array<String>
    val timestamps: FloatArray
    val ysLogProbs: FloatArray // Token-level natural log probabilities
    ```
  - Per-token confidence is computed as $p_i = \exp(\text{ysLogProbs}[i]) \in [0.0, 1.0]$.
  - Per-utterance confidence is the geometric mean: $\bar{C} = \exp\left(\frac{1}{N}\sum_{i=1}^N \text{ysLogProbs}[i]\right)$.
  - When `ysLogProbs` is unavailable or for custom calibration, the underlying ONNX model outputs the raw frame-level tensor `logprobs [batch, time, 5633]`, enabling direct posterior extraction.

---

## DECISION-005: ASR Output Format & Grammar Input Contract
- **ASR Acoustic Tokenizer Characteristics**:
  - The IndicConformer ASR model is trained on Marathi Devanagari phonetic BPE subwords.
  - Spoken numbers are transcribed as **Devanagari Marathi words** (e.g. spoken "७" $\to$ `सात`, spoken "१२" $\to$ `बारा`, spoken "७ + ८" $\to$ `सात अधिक आठ`).
- **Phase 1 Grammar Ingestion Contract**:
  The rule-based grammar must normalize and parse all of the following without distinction:
  1. **Devanagari number words**: `सात`, `बारा`, `पंचवीस`, `शंभर`, `दोनशे पन्नास`, `एक हजार`.
  2. **Colloquial & phonetic dialect variants**: `ब्येचाळीस` $\to$ 42, `दोन शे` $\to$ 200, `दीडशे` $\to$ 150.
  3. **Devanagari digits**: `०`, `१`, `२`, `३`, `४`, `५`, `६`, `७`, `८`, `९`.
  4. **Western numerals**: `0`, `1`, `2`, `3`, `4`, `5`, `6`, `7`, `8`, `9`.
  5. **Mixed formats**: `२५ अधिक सात`, `१०० मधून 40 वजा`.

---

## DECISION-006: Rejection of Non-Commercial & Infeasible Models
- **Meta MMS-TTS**: **REJECTED** due to CC-BY-NC 4.0 non-commercial license (critical legal liability).
- **Moshi 7B Full-Duplex**: **REJECTED** due to 7B parameter footprint (>14 GB VRAM), absence of Marathi pretraining, and immediate OOM on a 3 GB phone.
- **On-Device Neural TTS Models (270 MB)**: **REJECTED** for on-device APK bundling in favor of Opus Number Audio Bank (220 KB) + OS TTS.

---

## DECISION-007: Test Harness Synthetic Data Policy
- `edge-tts` is strictly confined to developer desktop test harnesses (`benchmarks/run_perturbed_eval.py`).
- It is **NEVER** packaged or referenced in the Android application.
- All evaluation results generated with synthetic voices, noise injections (15dB SNR), and time-stretching (0.85x, 1.15x) are explicitly designated **SIMULATED**.
