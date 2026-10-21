import time
import os
import gc
import json
import resource
import soundfile as sf
import scipy.signal
import sherpa_onnx
import numpy as np

def get_rss_mb():
    usage = resource.getrusage(resource.RUSAGE_SELF)
    import sys
    if sys.platform == 'darwin':
        return usage.ru_maxrss / (1024 * 1024)
    else:
        return usage.ru_maxrss / 1024

def run_benchmarks():
    results = {}
    print("=== STARTING BENCHMARK SUITE ===")
    
    # 1. Silero VAD Benchmark
    rss_before_vad = get_rss_mb()
    vad_load_times = []
    for _ in range(5):
        t0 = time.perf_counter()
        config = sherpa_onnx.VadModelConfig()
        config.silero_vad.model = 'models/vad/silero_vad.onnx'
        config.silero_vad.threshold = 0.5
        config.silero_vad.min_silence_duration = 0.25
        config.silero_vad.min_speech_duration = 0.25
        config.sample_rate = 16000
        vad = sherpa_onnx.VoiceActivityDetector(config, buffer_size_in_seconds=30)
        vad_load_times.append(time.perf_counter() - t0)
    
    vad_mem = get_rss_mb() - rss_before_vad
    results['vad'] = {
        'model_file': 'models/vad/silero_vad.onnx',
        'file_size_mb': os.path.getsize('models/vad/silero_vad.onnx') / (1024 * 1024),
        'load_time_mean_ms': float(np.mean(vad_load_times) * 1000),
        'load_time_std_ms': float(np.std(vad_load_times) * 1000),
        'memory_delta_mb': float(vad_mem)
    }
    print(f"VAD Load Time: {results['vad']['load_time_mean_ms']:.2f} ms, File Size: {results['vad']['file_size_mb']:.2f} MB")
    
    # 2. IndicConformer CTC INT8 Benchmark
    gc.collect()
    rss_before_asr = get_rss_mb()
    asr_load_times = []
    recognizer = None
    for i in range(5):
        t0 = time.perf_counter()
        recognizer = sherpa_onnx.OfflineRecognizer.from_nemo_ctc(
            model='models/asr/model.int8.onnx',
            tokens='models/asr/tokens.txt',
            num_threads=2,
            sample_rate=16000,
            feature_dim=80,
            decoding_method='greedy_search',
            provider='cpu'
        )
        asr_load_times.append(time.perf_counter() - t0)
    
    asr_mem = get_rss_mb() - rss_before_asr
    results['asr_loading'] = {
        'model_file': 'models/asr/model.int8.onnx',
        'file_size_mb': os.path.getsize('models/asr/model.int8.onnx') / (1024 * 1024),
        'tokens_file': 'models/asr/tokens.txt',
        'tokens_size_kb': os.path.getsize('models/asr/tokens.txt') / 1024,
        'load_time_mean_ms': float(np.mean(asr_load_times) * 1000),
        'load_time_min_ms': float(np.min(asr_load_times) * 1000),
        'load_time_max_ms': float(np.max(asr_load_times) * 1000),
        'memory_delta_mb': float(asr_mem)
    }
    print(f"ASR Cold Start: {results['asr_loading']['load_time_mean_ms']:.2f} ms (Target < 4000 ms), Size: {results['asr_loading']['file_size_mb']:.2f} MB")
    
    # 3. Latency & Real-Time Factor across durations
    durations = [0.5, 1.0, 2.0, 3.0, 5.0]
    latency_results = []
    
    # Warmup
    warmup_stream = recognizer.create_stream()
    warmup_stream.accept_waveform(16000, np.zeros(16000, dtype=np.float32))
    recognizer.decode_stream(warmup_stream)
    
    for dur in durations:
        samples = int(dur * 16000)
        t = np.linspace(0, dur, samples, endpoint=False)
        sig = (0.2 * np.sin(2 * np.pi * 300 * t) + 0.05 * np.random.randn(samples)).astype(np.float32)
        
        times = []
        for _ in range(5):
            stream = recognizer.create_stream()
            stream.accept_waveform(16000, sig)
            t0 = time.perf_counter()
            recognizer.decode_stream(stream)
            times.append(time.perf_counter() - t0)
        
        mean_lat = float(np.mean(times))
        rtf = float(mean_lat / dur)
        latency_results.append({
            'audio_duration_sec': dur,
            'inference_latency_ms': mean_lat * 1000,
            'rtf': rtf
        })
        print(f"Audio: {dur:.1f}s -> Latency: {mean_lat * 1000:.2f} ms, RTF: {rtf:.4f}")
    
    results['asr_latency'] = latency_results
    
    # 4. End-to-end pipeline latency estimation
    vad_latency_est_ms = 250.0
    asr_latency_2s_ms = [r['inference_latency_ms'] for r in latency_results if r['audio_duration_sec'] == 2.0][0]
    grammar_parse_est_ms = 1.5
    number_bank_lookup_ms = 0.5
    e2e_total_ms = vad_latency_est_ms + asr_latency_2s_ms + grammar_parse_est_ms + number_bank_lookup_ms
    
    results['e2e_latency'] = {
        'vad_endpoint_silence_window_ms': vad_latency_est_ms,
        'asr_inference_ms': asr_latency_2s_ms,
        'marathi_grammar_parser_ms': grammar_parse_est_ms,
        'audio_bank_lookup_ms': number_bank_lookup_ms,
        'total_e2e_latency_ms': e2e_total_ms,
        'target_constraint_ms': 2500.0,
        'headroom_percentage': ((2500.0 - e2e_total_ms) / 2500.0) * 100
    }
    print(f"Projected E2E Latency: {e2e_total_ms:.2f} ms (Target < 2500 ms, {results['e2e_latency']['headroom_percentage']:.1f}% margin)")
    
    with open('benchmarks/results.json', 'w') as f:
        json.dump(results, f, indent=2)
    print("Benchmark results saved to benchmarks/results.json")

if __name__ == '__main__':
    run_benchmarks()
