# गणित मित्र (Ganit Mitra)

> Fully Offline, Voice-First Marathi Math Learning App for Classes 1–6 (Rural Maharashtra)

## 📌 Project Overview
**गणित मित्र (Ganit Mitra)** is an ed-tech Android application designed for children aged 6–12 in rural Maharashtra. It bridges foundational numeracy gaps through context-rich, voice-enabled, manipulative-based learning, operating with zero internet connectivity.

### Non-Negotiable Constraints & Architecture Pillars
1. **100% Offline Runtime**: Zero network calls, no analytics SDKs, zero internet permission in `AndroidManifest.xml`.
2. **Strict Hardware Budget**: Target low-end Android (Android 8.0 Oreo / API 26+, 3 GB RAM, ~32 GB storage, ₹8,000 device class). APK + embedded offline models < 600 MB. Cold start < 4.0 s. Zero UI jank (60 FPS on low-end SoC).
3. **Marathi First & Only**: Authentic Devanagari script, Marathi numerals (१, २, ३...) with Western numerals (1, 2, 3...) toggle (default matching Balbharati syllabus).
4. **Child-Centric Pedagogy**:
   - Zero reading burden for Classes 1–2 (audio-guided, visual manipulatives, large touch targets ≥ 56dp).
   - 7-step pedagogical cycle: (1) Rural hook, (2) Manipulatives, (3) Spoken concept, (4) Scaffolded 3-level hints, (5) Independent practice, (6) Explain-back check, (7) Spaced repetition.
   - Deterministic verification: pure Kotlin math engines and property-based test suites.
5. **Speech System**:
   - Audio Output: Build-time pre-rendered Opus audio packs for static dialogue; lightweight on-device TTS fallback for dynamic numbers/names.
   - Audio Input: Constrained keyword-spotting (KWS) and small-vocabulary grammar recognition (numbers 0–1000 + control commands), with full tap fallback on every screen.

---
*Created as part of Phase 0 initiation. Detailed specifications and implementation roadmap are maintained in the implementation plan artifact.*
