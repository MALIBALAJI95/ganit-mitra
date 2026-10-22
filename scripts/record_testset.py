import os
import time
import csv
import sounddevice as sd
import soundfile as sf
import numpy as np

PROMPTS = [
    # 1. Numbers (10)
    ("num_01", "पाच", "number", "5"),
    ("num_02", "सात", "number", "7"),
    ("num_03", "बारा", "number", "12"),
    ("num_04", "पंधरा", "number", "15"),
    ("num_05", "पंचवीस", "number", "25"),
    ("num_06", "चाळीस", "number", "40"),
    ("num_07", "शंभर", "number", "100"),
    ("num_08", "दोनशे पन्नास", "number", "250"),
    ("num_09", "अर्धा", "number", "0.5"),
    ("num_10", "दीड", "number", "1.5"),

    # 2. Addition (10)
    ("add_01", "सात आणि आठ किती", "addition", "7 + 8"),
    ("add_02", "पाच अधिक तीन", "addition", "5 + 3"),
    ("add_03", "बारा अधिक सात", "addition", "12 + 7"),
    ("add_04", "वीस आणि पंधरा", "addition", "20 + 15"),
    ("add_05", "दहा अधिक दहा किती", "addition", "10 + 10"),
    ("add_06", "पंचवीस आणि पंचवीस", "addition", "25 + 25"),
    ("add_07", "एक अधिक चार", "addition", "1 + 4"),
    ("add_08", "दोनशे अधिक तीनशे", "addition", "200 + 300"),
    ("add_09", "पन्नास रुपये अधिक वीस रुपये", "addition", "50 + 20"),
    ("add_10", "आठ अधिक नऊ किती होतात", "addition", "8 + 9"),

    # 3. Subtraction (10)
    ("sub_01", "पंधरा मधून सात वजा", "subtraction", "15 - 7"),
    ("sub_02", "दहा वजा चार", "subtraction", "10 - 4"),
    ("sub_03", "वीस मधून पाच गेले", "subtraction", "20 - 5"),
    ("sub_04", "बारा वजा सहा", "subtraction", "12 - 6"),
    ("sub_05", "पन्नास मधून पंचवीस वजा केले", "subtraction", "50 - 25"),
    ("sub_06", "आठ वजा तीन", "subtraction", "8 - 3"),
    ("sub_07", "शंभर मधून चाळीस वजा", "subtraction", "100 - 40"),
    ("sub_08", "सात वजा दोन", "subtraction", "7 - 2"),
    ("sub_09", "चाळीस रुपये मधून दहा रुपये कमी केले", "subtraction", "40 - 10"),
    ("sub_10", "नऊ मधून पाच गेले तर किती", "subtraction", "9 - 5"),

    # 4. Multiplication (5)
    ("mul_01", "बारा गुणिले पाच", "multiplication", "12 * 5"),
    ("mul_02", "चार गुणिले तीन", "multiplication", "4 * 3"),
    ("mul_03", "पाच ची तीन पट किती", "multiplication", "5 * 3"),
    ("mul_04", "सहा गुणिले चार", "multiplication", "6 * 4"),
    ("mul_05", "दहा गुणिले दहा", "multiplication", "10 * 10"),

    # 5. Division (5)
    ("div_01", "वीस भागिले चार", "division", "20 / 4"),
    ("div_02", "बारा भागिले तीन", "division", "12 / 3"),
    ("div_03", "पंधरा चे तीन समान भाग", "division", "15 / 3"),
    ("div_04", "दहा भागिले दोन", "division", "10 / 2"),
    ("div_05", "सोळा भागिले चार", "division", "16 / 4"),

    # 6. Commands (10)
    ("cmd_01", "हो", "command", "yes"),
    ("cmd_02", "होय", "command", "yes"),
    ("cmd_03", "नाही", "command", "no"),
    ("cmd_04", "परत सांग", "command", "repeat"),
    ("cmd_05", "पुन्हा सांग", "command", "repeat"),
    ("cmd_06", "हळू सांग", "command", "slower"),
    ("cmd_07", "पुढे", "command", "next"),
    ("cmd_08", "पुढचा प्रश्न", "command", "next"),
    ("cmd_09", "मदत", "command", "help"),
    ("cmd_10", "थांब", "command", "stop"),

    # 7. Silence (10)
    ("sil_01", "[शांत राहा / silence]", "silence", "silence"),
    ("sil_02", "[शांत राहा / silence]", "silence", "silence"),
    ("sil_03", "[शांत राहा / silence]", "silence", "silence"),
    ("sil_04", "[शांत राहा / silence]", "silence", "silence"),
    ("sil_05", "[शांत राहा / silence]", "silence", "silence"),
    ("sil_06", "[शांत राहा / silence]", "silence", "silence"),
    ("sil_07", "[शांत राहा / silence]", "silence", "silence"),
    ("sil_08", "[शांत राहा / silence]", "silence", "silence"),
    ("sil_09", "[शांत राहा / silence]", "silence", "silence"),
    ("sil_10", "[शांत राहा / silence]", "silence", "silence"),

    # 8. Noise-Only (10)
    ("noi_01", "[टेबल वाजवणे / tapping]", "noise", "noise"),
    ("noi_02", "[टाळ्या / clapping]", "noise", "noise"),
    ("noi_03", "[खोकला / cough]", "noise", "noise"),
    ("noi_04", "[हसणे / laugh]", "noise", "noise"),
    ("noi_05", "[कागद चुरगळणे / paper rustle]", "noise", "noise"),
    ("noi_06", "[पंख्याचा आवाज / fan hum]", "noise", "noise"),
    ("noi_07", "[शिट्टी / whistle]", "noise", "noise"),
    ("noi_08", "[पेन आपटणे / pen click]", "noise", "noise"),
    ("noi_09", "[खुर्ची सरकवणे / chair scrape]", "noise", "noise"),
    ("noi_10", "[श्वास / breath/sigh]", "noise", "noise"),
]

def main():
    out_dir = "dataset/user_recordings"
    os.makedirs(out_dir, exist_ok=True)
    labels_csv = os.path.join(out_dir, "labels.csv")

    print("=" * 70)
    print("   गणित मित्र — REAL-VOICE TESTSET RECORDER")
    print("   Total prompts: 70 (Speech: 50, Silence: 10, Noise: 10)")
    print("   Target format: 16 kHz, 16-bit Mono PCM float32 WAV")
    print("=" * 70)
    print(f"Recordings will be saved to: {out_dir}/")
    input("\nPress ENTER when ready to begin recording...")

    records = []
    duration = 3.0

    for idx, (utt_id, text, category, ground_truth) in enumerate(PROMPTS, 1):
        print("\n" + "-" * 70)
        print(f"[{idx}/{len(PROMPTS)}] Prompt: \"{text}\"")
        print(f"Category: {category} | Ground Truth: {ground_truth}")
        input("Press ENTER to record (3.0s)...")
        print(">>> 3...")
        time.sleep(0.3)
        print(">>> 2...")
        time.sleep(0.3)
        print(">>> 1... [SPEAK NOW!]")
        
        audio = sd.rec(int(duration * 16000), samplerate=16000, channels=1, dtype='float32')
        sd.wait()
        print("[*] Captured!")

        fn = f"{utt_id}.wav"
        fpath = os.path.join(out_dir, fn)
        sf.write(fpath, audio.flatten(), 16000)

        records.append({
            "filename": fn,
            "prompt_text": text,
            "category": category,
            "ground_truth": ground_truth,
            "duration": duration
        })

    with open(labels_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["filename", "prompt_text", "category", "ground_truth", "duration"])
        writer.writeheader()
        writer.writerows(records)

    print("\n" + "=" * 70)
    print(f"Testset recording complete! {len(records)} recordings saved.")
    print(f"Labels saved to: {labels_csv}")
    print("=" * 70)

if __name__ == '__main__':
    main()
