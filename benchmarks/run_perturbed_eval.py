import os
import json
import asyncio
import numpy as np
import soundfile as sf
import scipy.signal
import sherpa_onnx
import edge_tts

def add_noise(audio, snr_db=15):
    p_sig = np.mean(audio ** 2)
    p_noise = p_sig / (10 ** (snr_db / 10))
    noise = np.random.normal(0, np.sqrt(p_noise), len(audio)).astype(np.float32)
    return audio + noise

def time_stretch(audio, rate=1.0):
    # Resample to simulate speech rate change
    num_samples = int(len(audio) / rate)
    return scipy.signal.resample(audio, num_samples).astype(np.float32)

async def generate_test_suite():
    phrases = [
        ("सात", "number_single"),
        ("आठ", "number_single"),
        ("पाच", "number_single"),
        ("बारा", "number_double"),
        ("पंधरा", "number_double"),
        ("वीस", "number_double"),
        ("पंचवीस", "number_double"),
        ("सात आणि आठ किती", "addition_question"),
        ("सात अधिक आठ", "addition_direct"),
        ("बारा वजा पाच", "subtraction_direct"),
        ("पंधरा मधून सात वजा", "subtraction_phrase"),
        ("हो", "command_affirmative"),
        ("नाही", "command_negative"),
        ("पुढचा", "command_next"),
        ("पुन्हा सांग", "command_repeat")
    ]
    
    os.makedirs("/tmp/ganit_eval_audio", exist_ok=True)
    test_cases = []
    
    for text, category in phrases:
        clean_mp3 = f"/tmp/ganit_eval_audio/{text}_clean.mp3"
        comm = edge_tts.Communicate(text, "mr-IN-AarohiNeural")
        await comm.save(clean_mp3)
        
        data, sr = sf.read(clean_mp3)
        if len(data.shape) > 1: data = data[:, 0]
        # Pad with 0.2s silence
        pad = np.zeros(int(sr * 0.2), dtype=np.float32)
        data = np.concatenate([pad, data, pad])
        # Resample to 16kHz
        data_16k = scipy.signal.resample_poly(data, 2, 3).astype(np.float32)
        
        # 1. Clean variant
        test_cases.append({"text": text, "category": category, "variant": "clean", "audio": data_16k})
        # 2. Additive Noise variant (SNR 15dB)
        test_cases.append({"text": text, "category": category, "variant": "noise_15db", "audio": add_noise(data_16k, snr_db=15)})
        # 3. Slow speed (0.85x)
        test_cases.append({"text": text, "category": category, "variant": "slow_0.85x", "audio": time_stretch(data_16k, 0.85)})
        # 4. Fast speed (1.15x)
        test_cases.append({"text": text, "category": category, "variant": "fast_1.15x", "audio": time_stretch(data_16k, 1.15)})
        
    return test_cases

def run_evaluation(test_cases):
    recognizer = sherpa_onnx.OfflineRecognizer.from_nemo_ctc(
        model="models/asr/model.int8.onnx",
        tokens="models/asr/tokens.txt",
        num_threads=2,
        sample_rate=16000,
        provider="cpu"
    )
    
    results = []
    for tc in test_cases:
        stream = recognizer.create_stream()
        stream.accept_waveform(16000, tc["audio"])
        recognizer.decode_stream(stream)
        
        pred_text = stream.result.text.strip()
        gt_text = tc["text"].strip()
        exact_match = (pred_text == gt_text)
        
        # Calculate approximate confidence from tokens
        # If ys_log_probs is available in python, extract it
        tokens = stream.result.tokens
        timestamps = stream.result.timestamps
        
        # If ys_log_probs is present
        log_probs = stream.result.ys_log_probs if hasattr(stream.result, 'ys_log_probs') and stream.result.ys_log_probs else [-0.05]*len(tokens)
        token_confidences = [float(np.exp(lp)) for lp in log_probs]
        mean_conf = float(np.mean(token_confidences)) if token_confidences else 0.0
        
        results.append({
            "gt": gt_text,
            "pred": pred_text,
            "category": tc["category"],
            "variant": tc["variant"],
            "exact_match": exact_match,
            "confidence": mean_conf,
            "tokens": tokens
        })
    
    return results

async def main():
    print("Generating simulated evaluation test suite with noise/speed variations...")
    test_cases = await generate_test_suite()
    print(f"Generated {len(test_cases)} audio variants.")
    eval_results = run_evaluation(test_cases)
    
    # Analyze by variant
    variants = {}
    for r in eval_results:
        v = r["variant"]
        if v not in variants: variants[v] = {"total": 0, "correct": 0}
        variants[v]["total"] += 1
        if r["exact_match"]: variants[v]["correct"] += 1
        
    print("\n=== SIMULATED EVALUATION RESULTS ===")
    for v, stats in variants.items():
        acc = (stats["correct"] / stats["total"]) * 100
        print(f"Variant: {v:12} -> Exact Match: {stats['correct']}/{stats['total']} ({acc:.1f}%)")
        
    # Save results
    with open("benchmarks/simulated_eval.json", "w") as f:
        json.dump({"summary": variants, "details": eval_results}, f, indent=2, ensure_ascii=False)
    print("Saved to benchmarks/simulated_eval.json")

if __name__ == '__main__':
    asyncio.run(main())
