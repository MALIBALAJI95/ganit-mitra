import os
import asyncio
import numpy as np
import soundfile as sf
import sounddevice as sd
import scipy.signal
import edge_tts

from benchmarks.verify_marathi_numbers import MARATHI_NUMS_0_100, HUNDREDS

BANK_DIR = "assets/audio/bank"

PHRASES = {
    # Operations
    "अधिक": "अधिक",
    "आणि": "आणि",
    "जमा": "जमा",
    "वजा": "वजा",
    "गुणिले": "गुणिले",
    "भागिले": "भागिले",
    "बरोबर": "बरोबर",
    # Prompts & Feedback
    "तू_विचारलंस": "तू विचारलंस",
    "बरोबर_आहे_का": "बरोबर आहे का?",
    "उत्तर_आहे": "उत्तर आहे",
    "छान_अगदी_बरोबर": "छान! अगदी बरोबर उत्तर आहे!",
    "पुन्हा_प्रयत्न_कर": "पुन्हा प्रयत्न कर.",
    "हो": "हो",
    "नाही": "नाही",
    "किती": "किती"
}

class NumberAudioBank:
    def __init__(self, cache_dir: str = BANK_DIR):
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)
        self.audio_cache = {}
        self.load_cache()

    def load_cache(self):
        for fn in os.listdir(self.cache_dir):
            if fn.endswith(".wav"):
                key = fn[:-4]
                path = os.path.join(self.cache_dir, fn)
                data, sr = sf.read(path)
                if len(data.shape) > 1: data = data[:, 0]
                self.audio_cache[key] = data.astype(np.float32)

    async def pregenerate_all(self):
        """Generate all prototype number bank clips (PROTOTYPE_ONLY)."""
        print("[AudioBank] Pre-generating and caching Number Bank audio files...")
        
        # 1. 0 to 100
        for num, word in MARATHI_NUMS_0_100.items():
            key = f"num_{num}"
            path = os.path.join(self.cache_dir, f"{key}.wav")
            if not os.path.exists(path):
                await self._synthesize_clip(word, path)

        # 2. Hundreds (200 - 900)
        for num, word in HUNDREDS.items():
            if num == 100: continue
            key = f"num_{num}"
            path = os.path.join(self.cache_dir, f"{key}.wav")
            if not os.path.exists(path):
                await self._synthesize_clip(word, path)

        # 3. Fixed phrases & Operations
        for key, text in PHRASES.items():
            path = os.path.join(self.cache_dir, f"{key}.wav")
            if not os.path.exists(path):
                await self._synthesize_clip(text, path)

        print("[AudioBank] Number Bank pre-generation complete! Loading cache...")
        self.load_cache()

    async def _synthesize_clip(self, text: str, output_path: str):
        temp_mp3 = output_path + ".tmp.mp3"
        comm = edge_tts.Communicate(text, "mr-IN-AarohiNeural")
        await comm.save(temp_mp3)
        
        data, sr = sf.read(temp_mp3)
        if len(data.shape) > 1: data = data[:, 0]
        # Pad with 0.05s silence
        pad = np.zeros(int(sr * 0.05), dtype=np.float32)
        data = np.concatenate([pad, data, pad])
        # Resample to 16kHz
        data_16k = scipy.signal.resample_poly(data, 2, 3).astype(np.float32)
        
        # Write WAV with PROTOTYPE_ONLY header metadata
        sf.write(output_path, data_16k, 16000)
        if os.path.exists(temp_mp3):
            os.remove(temp_mp3)

    def get_number_keys(self, n: int) -> list:
        """Decompose any integer 0 to 99,999 into exact audio bank keys."""
        if n == 0:
            return ["num_0"]
        if n < 0:
            return ["वजा"] + self.get_number_keys(-n)
        if n <= 100:
            return [f"num_{n}"]

        keys = []
        # Thousands (1,000 - 99,999)
        if n >= 1000:
            th = n // 1000
            keys.extend(self.get_number_keys(th))
            if "हजार" in self.audio_cache:
                keys.append("हजार")
            n %= 1000

        # Hundreds (100 - 900)
        if n >= 100:
            h = n // 100
            if h == 1:
                keys.append("num_100")
            else:
                keys.append(f"num_{h * 100}")
            n %= 100

        # Remaining 1 - 99
        if n > 0:
            keys.append(f"num_{n}")

        return keys

    def assemble_readback(self, op: str, a: int, b: int) -> np.ndarray:
        """
        Assemble read-back audio: 'तू विचारलंस: [a] [op] [b] किती? बरोबर आहे का?'
        """
        keys = ["तू_विचारलंस"]
        keys.extend(self.get_number_keys(a))
        if op == "ADD":
            keys.append("अधिक")
        elif op == "SUB":
            keys.append("वजा")
        elif op == "MUL":
            keys.append("गुणिले")
        elif op == "DIV":
            keys.append("भागिले")
        keys.extend(self.get_number_keys(b))
        keys.append("किती")
        keys.append("बरोबर_आहे_का")

        return self.stitch_keys(keys)

    def assemble_answer(self, ans: int) -> np.ndarray:
        """
        Assemble answer audio for any integer 0-99,999: 'उत्तर आहे: [ans]'
        """
        keys = ["उत्तर_आहे"]
        keys.extend(self.get_number_keys(ans))
        return self.stitch_keys(keys)

    def synthesize_sentence(self, text: str) -> np.ndarray:
        """
        Offline fallback on macOS for full dynamic Marathi sentences (tables, geometry).
        Uses native say -v Lekha into a clean 16kHz float32 buffer.
        """
        import subprocess
        tmp_aiff = f"/tmp/speech_lekha_{os.getpid()}.aiff"
        # Sanitize text
        clean = text.replace('"', '').replace("'", "").replace("`", "")
        cmd = ["say", "-v", "Lekha", clean, "-o", tmp_aiff]
        try:
            res = subprocess.run(cmd, capture_output=True, timeout=5)
            if res.returncode == 0 and os.path.exists(tmp_aiff):
                data, sr = sf.read(tmp_aiff)
                if len(data.shape) > 1: data = data[:, 0]
                if sr != 16000:
                    num_samples = int(len(data) * 16000 / sr)
                    data = scipy.signal.resample(data, num_samples).astype(np.float32)
                if os.path.exists(tmp_aiff):
                    os.remove(tmp_aiff)
                return data.astype(np.float32)
        except Exception as e:
            pass
        return np.zeros(16000, dtype=np.float32)

    def stitch_keys(self, keys: list) -> np.ndarray:
        buffers = []
        silence_gap = np.zeros(int(16000 * 0.08), dtype=np.float32) # 80ms natural pause
        for k in keys:
            if k in self.audio_cache:
                buffers.append(self.audio_cache[k])
                buffers.append(silence_gap)
        if buffers:
            return np.concatenate(buffers)
        return np.zeros(16000, dtype=np.float32)

    def play(self, audio: np.ndarray):
        sd.play(audio, samplerate=16000)
        sd.wait()
