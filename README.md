# गणित मित्र (Ganit Mitra) — Desktop Voice Prototype

> Fully offline, voice-first Marathi mathematics learning prototype for primary school children (Classes 1–6).

---

## Proven Interactive Loop

```
[Microphone] 
     │
     ▼
[Silero VAD] (1.7 MB ONNX, 8ms)
     │
     ▼
[IndicConformer ASR] (188 MB INT8 ONNX, ~45ms)
     │
     ▼
[4-Stage Classifier] (audio_gate ──► language_check ──► intent ──► decision)
     │
     ▼
[Marathi Math Parser] (Rule-based AST + Ambiguity Detection)
     │
     ▼
[READ-BACK + CONFIRM] ("तू विचारलंस: ७ अधिक ८ किती? बरोबर आहे का?")
     │
     ▼ (Child confirms "हो")
[Exact Math Engine] (Arithmetic + Place Value / Carrying / Borrowing Steps)
     │
     ▼
[Spoken Marathi Audio] (Zero-latency Number Audio Bank + On-Screen Text)
```

---

## Reproduction & Demo Commands

### 1. Run the Full End-to-End Session Test
Runs a complete 2-turn dialogue test (question $\to$ read-back $\to$ confirm "हो" $\to$ exact solve $\to$ step-by-step Marathi narration):
```bash
PYTHONPATH=. .venv/bin/python -m unittest tests/test_e2e_session.py
```

### 2. Run the 40,000 Property-Based Math Tests
Verifies 10,000 random cases each for addition, subtraction, multiplication, and division, plus misconception diagnostics:
```bash
PYTHONPATH=. .venv/bin/python -m unittest tests/test_math_property.py
```

### 3. Run the 514 Table-Driven Grammar Tests
Tests numbers, operations, fractions, currency, dialect forms, and ambiguity detection against `tests/golden/math_grammar_golden.json`:
```bash
PYTHONPATH=. .venv/bin/python -m unittest tests/test_grammar_table.py
```

### 4. Run the Interactive Push-to-Talk Terminal Loop (Live Microphone)
Starts the live desktop prototype with real-time debug panel logging for each utterance:
```bash
PYTHONPATH=. .venv/bin/python -m ganit_mitra_desktop.live_loop --interactive
```

### 5. Record Your Own 70-Utterance Voice Testset
Interactive prompt tool capturing numbers, operations, commands, silence, and noise:
```bash
PYTHONPATH=. .venv/bin/python scripts/record_testset.py
```
Outputs are stored in `dataset/user_recordings/` with a complete `labels.csv`.

---

## 2-Minute Demo Script

1. **Start the demo**:
   ```bash
   PYTHONPATH=. .venv/bin/python -m ganit_mitra_desktop.live_loop --interactive
   ```
2. **Turn 1 (Math Question)**:
   - Press **ENTER** and speak: *"सात आणि आठ किती"*
   - The Debug Panel immediately displays:
     - Audio Gate: `SPEECH` (duration, energy)
     - ASR: `"सात अधिक आठ"` (conf: 92.3%)
     - Classifier: `math_question`, decision: `CONFIRM`
     - Parser: `OP = ADD, Left = 7, Right = 8`
     - Audio Output: *"तू विचारलंस: सात अधिक आठ किती? बरोबर आहे का?"*
3. **Turn 2 (Affirmation)**:
   - Press **ENTER** and speak: *"हो"*
   - The Debug Panel immediately displays:
     - Classifier: `command: yes`, decision: `ACCEPT`
     - Math Engine: `Ans = 15 (पंधरा)`
     - Step 1: *"प्रथम एकक स्थानाची बेरीज करू: 7 + 8 = 15. यात एकक स्थानी 5 राहिले आणि हातचा 1 आला."*
     - Step 2: *"7 आणि 8 यांची एकूण बेरीज 15 (पंधरा) झाली."*
     - Audio Output: Plays studio Marathi voice answer.
4. **Turn 3 (Misconception & Help)**:
   - Type or speak an incorrect answer like *"सोळा"*
   - Math Engine diagnoses: `OFF_BY_ONE`
   - Spoken Hint: *"अगदी जवळ पोहोचलास! फक्त एकाने उत्तर चुकले आहे. मोजणी पुन्हा करून बघ."*
