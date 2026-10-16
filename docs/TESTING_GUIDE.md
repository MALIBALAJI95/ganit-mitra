# गणित मित्र (Ganit Mitra) — Comprehensive Testing Manual

This guide explains how to test every component of **गणित मित्र** across 4 different levels:
1. **Instant In-Browser Interactive Testing** (Zero setup, runs immediately).
2. **Automated Command-Line Test Suites** (10,000 property-based math tests, latency/RAM profiles).
3. **Android Physical Phone & Emulator Testing** (Airplane-mode verification on budget devices).
4. **Speech Input & Misconception Diagnosis Testing** (Child voice, noise, and tap fallback).

---

## 1. Instant In-Browser Testing (Zero Setup)

You can test the entire app, voice recognition, manipulatives, and teacher tools directly in your browser:

### A. Student Master App (`ganit_mitra_master_app.html`)
- **Location**: Open `ganit_mitra_master_app.html` in Chrome, Edge, or Safari.
- **What to Test**:
  1. **Voice Input (Web Speech API)**: Tap the **"बोला" (🎙️)** button and speak in Marathi (e.g., *"पुढे"*, *"मदत"*, *"तीनशे ब्याऐंशी"*). Observe the mic dot and speech feedback.
  2. **Voice Simulation Panel**: If no microphone is available, click the simulated command buttons on the right panel (*"पुढे"*, *"मागे"*, *"तीनशे ब्याऐंशी"*, *"तीनशे बहात्तर"*).
  3. **Place-Value Manipulative**: In Stage 2, tap *"✨ १० नाण्यांचा १ दशक हातचा करा"* to watch 10 coins bundle into a ₹10 note with the red carry badge (*हातचा +१*).
  4. **Misconception Diagnosis**: In Stage 5, type or click `३७२` (forgetting the carry). Verify the app gives a kind place-value hint instead of saying "wrong".
  5. **Devanagari vs Western Toggle**: Tap **"१ २ ३"** and **"1 2 3"** in the top bar to verify all keypad digits, operands, and displays convert in real-time.
  6. **Multi-Grade Switcher**: Select Class 1 through 6 from the top dropdown to test different rural contexts.
  7. **QR Code Generation**: Finish Stage 6 to see the live Canvas QR code generated for the teacher to scan.

### B. Teacher Dashboard & QR Sync (`teacher_dashboard.html`)
- **Location**: Open `teacher_dashboard.html` in your browser.
- **What to Test**:
  1. Click **"+ गण्याचा QR स्कॅन करा"** or **"+ मीनाचा QR स्कॅन करा"**.
  2. Observe the student roster update immediately without network access.
  3. Inspect the **Misconception Heatmap** to see carrying error clusters.
  4. Click **"स्थानिक CSV अहवाल डाऊनलोड"** to verify offline grade export.

---

## 2. Automated Command-Line Test Suite (Terminal)

Open your terminal, navigate to the `ganit-mitra` folder, and run:

```bash
cd /Users/balajimali/Developer/WebDevelopment/ganit-mitra
```

### Test 1: Run 10,000 Property-Based Math Tests
```bash
python3 tools/test_math_engine_properties.py
```
- **What it tests**: 10,000 randomized 3-digit addition problems, zero-place edge cases, cascading carries, and misconception diagnoses.
- **Expected Output**: `✓ All 10000 property tests PASSED!`

### Test 2: Run Full Low-End Device Profile & Accessibility Audit
```bash
python3 tools/run_full_phase_3_test_suite.py
```
- **What it tests**:
  - Cold start breakdown on Cortex-A53 (< 4.0s).
  - Peak heap RAM (< 200 MB).
  - Touch target sizes (>= 56dp).
  - WCAG AAA contrast ratios.
  - 132 Marathi number words coverage.
  - Airplane-mode zero-network audit.
- **Expected Output**: `🏆 ALL PHASE 3 TEST SUITES, PROFILES & AUDITS PASSED WITH 100% COMPLIANCE!`

### Test 3: Run 7-Stage Vertical Slice End-to-End Test
```bash
python3 tools/test_phase_2_vertical_slice.py
```
- **What it tests**: Traverses all 7 stages from rural hook to Room DB mastery persistence and spaced repetition scheduling.
- **Expected Output**: `🎉 ALL 7 PHASES OF THE MVP VERTICAL SLICE PASSED 100% SUCCESFULLY!`

### Test 4: Run Curriculum DAG & Schema Validator
```bash
python3 tools/validate_curriculum_and_packs.py
python3 tools/pack_linter_and_validator.py
```
- **What it tests**: Validates all JSON packs across Classes 1–6, verifies 0 cyclic dependencies, checks math correctness, and scans for glossary flags.

### Test 5: Run Bulk Audio Generator & Incremental Cache
```bash
python3 tools/bulk_audio_generator.py
```
- **What it tests**: Extracts all Marathi speech lines and compiles them to 32 kbps Ogg Opus, verifying SHA-256 caching.

---

## 3. Physical Android Phone & Emulator Testing (Airplane Mode)

### A. Android Emulator Setup (Matching ₹8,000 Budget Phone)
In Android Studio's Device Manager, create an Android Virtual Device (AVD):
- **Hardware Profile**: 5.5" HD+ Screen (720 × 1440, ~320 dpi).
- **CPU**: 4 Cores (Cortex-A53 emulation).
- **RAM**: **3072 MB (3 GB)**.
- **VM Heap**: **192 MB** (standard low-end device heap).
- **Internal Storage**: 32 GB.
- **System Image**: Android 8.1 Oreo (API 27) or Android 10 (API 29) x86_64.

### B. Building & Sideloading the APK
```bash
cd /Users/balajimali/Developer/WebDevelopment/ganit-mitra
./gradlew assembleDebug
```
Install to the emulator or connected phone via USB:
```bash
adb install -r app/build/outputs/apk/debug/app-debug.apk
```

### C. The Non-Negotiable Airplane Mode Test
1. Disconnect Wi-Fi and Cellular data on the device.
2. Turn **Airplane Mode ON** (`Settings -> Network & Internet -> Airplane Mode`).
3. Open **"गणित मित्र"**.
4. **Pass Criteria**:
   - Cold start under 4 seconds.
   - All voice and mascot dialogue plays clearly from local Ogg Opus assets.
   - Speech recognition (Mode A & Mode B) functions without network connection.
   - Tap keypad operates without any dropped frames (60 FPS).
   - Progress is saved locally in SQLite Room DB.
   - Open logcat to confirm 0 network requests:
     ```bash
     adb logcat | grep -E "HttpClient|Retrofit|Volley|Socket"
     ```
     (Must show 0 network calls).

---

## 4. How to Test Speech & Misconceptions

| Test Scenario | Input Method | Test Action | Expected Behavior |
| :--- | :--- | :--- | :--- |
| **Mode A Navigation** | Voice | Speak *"पुढे"* | Immediately advances to the next stage (< 200ms). |
| **Mode A Help** | Voice | Speak *"मदत"* | Triggers Level 1 scaffolded hint. |
| **Mode B Correct Answer** | Voice | Speak *"तीनशे ब्याऐंशी"* | Recognized as `382`; mascot cheers and advances to explain-back. |
| **Misconception: Forgot Carry** | Voice or Tap | Enter `372` (*"तीनशे बहात्तर"*) | Flags `FORGOT_CARRY_UNITS_TO_TENS`; mascot explains: *"एककातून आलेला हातचा १ मिळवायला विसरलात का? १ + ४ + ३ = ८ दशक."* |
| **Misconception: Digit Reversal** | Voice or Tap | Enter `381` | Flags `DIGIT_REVERSAL_IN_CARRY`; mascot explains place-value roles of 12 (2 units, 1 ten). |
| **Noisy Background / Silence** | Noise | Stay silent or make noise | App kindly reprompts; on 2nd attempt, highlights the big 56dp tap keypad so child is never blocked. |
