# गणित मित्र (Ganit Mitra)

> Fully offline, voice-first Marathi mathematics learning application for primary school children (Classes 1–6).

---

## Architecture Overview

Ganit Mitra is engineered to run **100% on-device** on resource-constrained Android smartphones (Android 8+, 3 GB RAM) with zero cloud dependencies, zero analytics, and zero network calls.

```
+-------------------------------------------------------------+
|                      Ganit Mitra App                        |
|                                                             |
|  [Silero VAD]  -->  [IndicConformer CTC INT8]  -->  [NLU]  |
|   (1.7 MB ONNX)          (188 MB ONNX)          (Grammar)   |
|                                                     |       |
|                                                     v       |
|  [Voice Read-Back] <-- [Number Audio Bank] <-- [Math Engine]|
|   (Confirm/Reject)      (Opus Audio Bank)      (Deterministic|
|                                                 Arithmetic) |
+-------------------------------------------------------------+
```

---

## Phase 0: Verification & Reproduction Guide

### Prerequisites
- macOS (Apple Silicon or Intel) or Linux (x86_64 or aarch64)
- Python 3.10+
- OpenJDK 17
- Android SDK Platform-Tools (`adb`)

### Step 1: Virtual Environment Setup
```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install sherpa-onnx onnxruntime numpy soundfile scipy requests huggingface_hub edge-tts
```

### Step 2: Download Models & Assets
Run the model download verification script:
```bash
# Downloads Silero VAD (1.7 MB) and IndicConformer Marathi INT8 ONNX (188 MB)
python -c "
from huggingface_hub import hf_hub_download
hf_hub_download(repo_id='csukuangfj/vad', filename='silero_vad.onnx', local_dir='models/vad')
hf_hub_download(repo_id='parismitaglobalsolutions/indicconformer-sherpa-onnx', filename='tokens.txt', local_dir='models/asr')
hf_hub_download(repo_id='parismitaglobalsolutions/indicconformer-sherpa-onnx', filename='mr/model.int8.onnx', local_dir='models/asr')
"
cp models/asr/mr/model.int8.onnx models/asr/model.int8.onnx
```

### Step 3: Execute Model Feasibility Benchmarks
```bash
python benchmarks/run_benchmarks.py
```
This tests:
1. Silero VAD initialization and cold-start time.
2. IndicConformer CTC INT8 initialization and cold-start time.
3. Inference latency and Real-Time Factor (RTF) across 0.5s, 1.0s, 2.0s, 3.0s, and 5.0s audio inputs.
4. End-to-end projected latency against the 2.5s constraint.

Output is stored in `benchmarks/results.json`.

### Step 4: Verify Marathi Number System (0 to 10,000)
```bash
python benchmarks/verify_marathi_numbers.py
```
Tests 10,001 Marathi numbers from 0 to 10,000 against Balbharati curriculum rules.

---

## Licenses & Commercial Safety
See [LICENSES.md](file:///Users/balajimali/Developer/WebDevelopment/LICENSES.md) for full audit.
- **ASR & VAD**: MIT / Apache 2.0 (Commercially safe)
- **Meta MMS-TTS**: REJECTED due to CC-BY-NC non-commercial restriction.
- **Moshi 7B**: REJECTED due to 7B parameter GPU memory footprint and absence of Marathi support.
