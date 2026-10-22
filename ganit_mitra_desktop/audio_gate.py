from dataclasses import dataclass
import numpy as np
import sherpa_onnx
import os

@dataclass
class AudioGateResult:
    status: str          # 'speech' | 'silence' | 'noise' | 'too_short' | 'too_long' | 'clipped'
    confidence: float    # 0.0 to 1.0
    duration: float      # seconds
    rms_energy: float    # RMS level
    peak: float          # Peak amplitude
    speech_duration: float
    speech_ratio: float

class AudioGate:
    def __init__(self, vad_model_path: str = "models/vad/silero_vad.onnx", sample_rate: int = 16000):
        if not os.path.exists(vad_model_path):
            raise FileNotFoundError(f"VAD model not found at {vad_model_path}")
        
        self.sample_rate = sample_rate
        self.config = sherpa_onnx.VadModelConfig()
        self.config.silero_vad.model = vad_model_path
        self.config.silero_vad.threshold = 0.35
        self.config.silero_vad.min_silence_duration = 0.20
        self.config.silero_vad.min_speech_duration = 0.08
        self.config.silero_vad.window_size = 512
        self.config.sample_rate = sample_rate
        
        self.vad = sherpa_onnx.VoiceActivityDetector(self.config, buffer_size_in_seconds=30)

    def analyze(self, audio: np.ndarray) -> AudioGateResult:
        if audio.ndim > 1:
            audio = audio.flatten()
        audio = audio.astype(np.float32)
        
        duration = len(audio) / float(self.sample_rate)
        if duration < 0.25:
            return AudioGateResult(
                status="too_short",
                confidence=0.99,
                duration=duration,
                rms_energy=0.0,
                peak=0.0,
                speech_duration=0.0,
                speech_ratio=0.0
            )
            
        if duration > 12.0:
            return AudioGateResult(
                status="too_long",
                confidence=0.99,
                duration=duration,
                rms_energy=float(np.sqrt(np.mean(audio ** 2))),
                peak=float(np.max(np.abs(audio))),
                speech_duration=0.0,
                speech_ratio=0.0
            )

        peak = float(np.max(np.abs(audio))) if len(audio) > 0 else 0.0
        rms = float(np.sqrt(np.mean(audio ** 2))) if len(audio) > 0 else 0.0
        
        # Check clipping
        if peak > 0.98:
            clipped_ratio = float(np.mean(np.abs(audio) > 0.97))
            if clipped_ratio > 0.01:
                return AudioGateResult(
                    status="clipped",
                    confidence=min(0.99, clipped_ratio * 20),
                    duration=duration,
                    rms_energy=rms,
                    peak=peak,
                    speech_duration=0.0,
                    speech_ratio=0.0
                )

        # Check silence via energy
        if rms < 0.004:
            return AudioGateResult(
                status="silence",
                confidence=max(0.70, 1.0 - (rms / 0.004)),
                duration=duration,
                rms_energy=rms,
                peak=peak,
                speech_duration=0.0,
                speech_ratio=0.0
            )

        # Run Silero VAD over 512-sample windows
        window_size = 512
        speech_samples = 0
        self.vad.reset()
        
        for i in range(0, len(audio), window_size):
            chunk = audio[i : i + window_size]
            if len(chunk) < window_size:
                chunk = np.pad(chunk, (0, window_size - len(chunk)))
            self.vad.accept_waveform(chunk)
            if self.vad.is_speech_detected():
                speech_samples += window_size

        speech_duration = speech_samples / float(self.sample_rate)
        speech_ratio = min(1.0, speech_duration / duration)

        if speech_duration < 0.08:
            # Not enough speech detected by neural VAD
            if rms > 0.025:
                status = "noise"
                conf = min(0.95, rms * 10)
            else:
                status = "silence"
                conf = 0.90
            return AudioGateResult(
                status=status,
                confidence=conf,
                duration=duration,
                rms_energy=rms,
                peak=peak,
                speech_duration=speech_duration,
                speech_ratio=speech_ratio
            )

        # Sufficient speech verified
        return AudioGateResult(
            status="speech",
            confidence=min(0.99, max(0.60, speech_ratio * 1.5)),
            duration=duration,
            rms_energy=rms,
            peak=peak,
            speech_duration=speech_duration,
            speech_ratio=speech_ratio
        )
