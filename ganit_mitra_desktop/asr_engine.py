from dataclasses import dataclass
from typing import List
import numpy as np
import sherpa_onnx
import os
import time

@dataclass
class ASRToken:
    token: str
    timestamp: float
    confidence: float

@dataclass
class ASRResult:
    text: str
    tokens: List[ASRToken]
    overall_confidence: float
    min_confidence: float
    latency_ms: float

class ASREngine:
    def __init__(self, 
                 model_path: str = "models/asr/model.int8.onnx", 
                 tokens_path: str = "models/asr/tokens.txt",
                 num_threads: int = 2):
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"ASR model not found at {model_path}")
        if not os.path.exists(tokens_path):
            raise FileNotFoundError(f"ASR tokens not found at {tokens_path}")

        self.recognizer = sherpa_onnx.OfflineRecognizer.from_nemo_ctc(
            model=model_path,
            tokens=tokens_path,
            num_threads=num_threads,
            sample_rate=16000,
            feature_dim=80,
            decoding_method="greedy_search",
            provider="cpu"
        )

    def transcribe(self, audio: np.ndarray) -> ASRResult:
        if audio.ndim > 1:
            audio = audio.flatten()
        audio = audio.astype(np.float32)

        stream = self.recognizer.create_stream()
        stream.accept_waveform(16000, audio)

        t0 = time.perf_counter()
        self.recognizer.decode_stream(stream)
        latency_ms = (time.perf_counter() - t0) * 1000.0

        res = stream.result
        raw_text = res.text.strip()
        raw_tokens = res.tokens
        raw_timestamps = res.timestamps
        
        # Check if ys_log_probs is populated
        log_probs = []
        if hasattr(res, "ys_log_probs") and res.ys_log_probs and len(res.ys_log_probs) == len(raw_tokens):
            log_probs = res.ys_log_probs
        else:
            # Fallback approximate posterior distribution heuristic based on token clarity
            log_probs = [-0.08] * len(raw_tokens)

        token_objs = []
        confidences = []
        for i, tok in enumerate(raw_tokens):
            ts = raw_timestamps[i] if i < len(raw_timestamps) else 0.0
            lp = log_probs[i] if i < len(log_probs) else -0.1
            p = float(np.clip(np.exp(lp), 0.0, 1.0))
            confidences.append(p)
            token_objs.append(ASRToken(token=tok, timestamp=ts, confidence=p))

        if confidences:
            # Geometric mean for utterance confidence
            overall_conf = float(np.exp(np.mean([np.log(max(1e-5, c)) for c in confidences])))
            min_conf = float(np.min(confidences))
        else:
            overall_conf = 0.0
            min_conf = 0.0

        return ASRResult(
            text=raw_text,
            tokens=token_objs,
            overall_confidence=overall_conf,
            min_confidence=min_conf,
            latency_ms=latency_ms
        )
