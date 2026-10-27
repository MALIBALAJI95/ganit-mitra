import os
import io
import json
import base64
import time
import re
import traceback
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
import numpy as np
import soundfile as sf
import scipy.signal

from ganit_mitra_desktop.live_loop import GanitMitraSession

session: GanitMitraSession = None

HTML_PAGE = """<!DOCTYPE html>
<html lang="mr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>गणित मित्र (Ganit Mitra) — Voice Math Assistant for Kids</title>
  <style>
    :root {
      --bg: #090e17;
      --card-bg: #131c2e;
      --card-border: #24324a;
      --text: #f8fafc;
      --text-muted: #94a3b8;
      --primary: #38bdf8;
      --primary-glow: rgba(56, 189, 248, 0.35);
      --success: #22c55e;
      --success-glow: rgba(34, 197, 94, 0.35);
      --amber: #f59e0b;
      --accent: #818cf8;
      --danger: #ef4444;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: system-ui, -apple-system, sans-serif; }
    body {
      background: radial-gradient(circle at 50% 5%, #16243d 0%, var(--bg) 100%);
      color: var(--text); padding: 14px; min-height: 100vh;
      display: flex; flex-direction: column; align-items: center;
    }
    .app-container { max-width: 1200px; width: 100%; display: flex; flex-direction: column; gap: 14px; }

    /* Header */
    header { text-align: center; margin-top: 4px; }
    .brand-title {
      font-size: 2.2rem; font-weight: 800; color: #f8fafc;
      display: flex; align-items: center; justify-content: center; gap: 10px;
    }
    .brand-title span.highlight {
      background: linear-gradient(135deg, #38bdf8, #818cf8);
      -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .brand-subtitle { color: var(--text-muted); font-size: 1rem; margin-top: 2px; }

    /* Mascot Banner */
    .mascot-banner {
      background: #1e293b; border: 1.5px solid #334155; border-radius: 14px;
      padding: 10px 16px; display: flex; align-items: center; gap: 12px;
      box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    }
    .mascot-avatar { font-size: 2.2rem; line-height: 1; }
    .mascot-text { font-size: 0.98rem; color: #e2e8f0; line-height: 1.45; }
    .mascot-text strong { color: #facc15; }

    /* Split-Screen 2-Column Grid */
    .split-grid {
      display: grid; grid-template-columns: 1fr 1fr; gap: 16px; align-items: start;
    }
    @media (max-width: 860px) {
      .split-grid { grid-template-columns: 1fr; }
    }

    /* Column Cards */
    .studio-card {
      background: var(--card-bg); border: 1.5px solid var(--card-border);
      border-radius: 18px; padding: 18px; display: flex; flex-direction: column; gap: 14px;
      box-shadow: 0 8px 24px rgba(0,0,0,0.3);
    }
    .studio-header {
      display: flex; align-items: center; justify-content: space-between;
      border-bottom: 1px solid #1e293b; padding-bottom: 10px;
    }
    .studio-title {
      font-size: 1.15rem; font-weight: 700; color: #f1f5f9;
      display: flex; align-items: center; gap: 8px;
    }
    .studio-title span.en { font-size: 0.85rem; color: var(--text-muted); font-weight: 500; }

    /* Voice Centerpiece */
    .voice-centerpiece {
      display: flex; flex-direction: column; align-items: center; gap: 12px;
      padding: 8px 0;
    }
    .dialogue-tag {
      font-size: 0.9rem; font-weight: 700; padding: 5px 14px; border-radius: 30px;
      display: inline-flex; align-items: center; gap: 6px; transition: all 0.25s ease;
    }
    .tag-idle { background: #1e293b; color: #94a3b8; border: 1px solid #334155; }
    .tag-confirm { background: #78350f; color: #fef08a; border: 1px solid #f59e0b; animation: gentlePulse 2s infinite; }

    .mic-button {
      width: 124px; height: 124px; border-radius: 50%; border: none; cursor: pointer;
      background: linear-gradient(135deg, #0284c7, #6366f1); color: white;
      display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 5px;
      font-size: 1.1rem; font-weight: 700; box-shadow: 0 8px 24px var(--primary-glow);
      transition: all 0.2s cubic-bezier(0.34, 1.56, 0.64, 1);
      user-select: none; -webkit-user-select: none;
    }
    .mic-button:hover { transform: scale(1.05); }
    .mic-button:active { transform: scale(0.96); }
    .mic-button.recording {
      background: linear-gradient(135deg, #dc2626, #f43f5e);
      box-shadow: 0 10px 30px rgba(239, 68, 68, 0.55);
      animation: recordPulse 1.2s infinite;
    }
    @keyframes recordPulse { 0% { transform: scale(1); } 50% { transform: scale(1.06); } 100% { transform: scale(1); } }
    @keyframes gentlePulse { 0% { opacity: 0.85; } 50% { opacity: 1; } 100% { opacity: 0.85; } }

    .vu-meter-bar-container {
      width: 200px; height: 8px; background: #090e17; border-radius: 6px;
      overflow: hidden; border: 1px solid #334155;
    }
    .vu-meter-fill {
      width: 0%; height: 100%;
      background: linear-gradient(90deg, #22c55e, #38bdf8, #f59e0b);
      transition: width 0.05s ease;
    }
    .mic-hint { font-size: 0.9rem; color: var(--text-muted); text-align: center; }

    /* Preset Chips */
    .chips-section-title { font-size: 0.82rem; font-weight: 700; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px; }
    .preset-chips { display: flex; flex-wrap: wrap; gap: 7px; justify-content: flex-start; }
    .chip {
      background: #1e293b; border: 1px solid #334155; color: #f1f5f9;
      padding: 7px 11px; border-radius: 10px; font-size: 0.88rem; cursor: pointer;
      display: inline-flex; align-items: center; gap: 5px; transition: all 0.15s ease;
    }
    .chip:hover { background: #334155; transform: translateY(-1px); }
    .chip-yes { background: #14532d; border-color: #22c55e; color: #86efac; font-weight: 700; }
    .chip-no { background: #7f1d1d; border-color: #ef4444; color: #fca5a5; font-weight: 700; }
    .chip-table { border-color: #f59e0b; color: #fde68a; }
    .chip-shape { border-color: #38bdf8; color: #bae6fd; }

    /* Typing Input Row */
    .input-row { display: flex; gap: 8px; width: 100%; margin-top: 2px; }
    .input-row input {
      flex: 1; padding: 11px 14px; border-radius: 10px; border: 1px solid #334155;
      background: #090e17; color: white; font-size: 0.96rem;
    }
    .input-row input:focus { outline: none; border-color: var(--primary); }
    .btn-send {
      padding: 11px 16px; border-radius: 10px; border: none;
      background: var(--primary); color: #090e17; font-weight: 700; cursor: pointer;
      transition: background 0.15s; font-size: 0.92rem;
    }
    .btn-send:hover { background: #0284c7; }
    .btn-reset {
      padding: 11px 14px; border-radius: 10px; border: 1px solid #475569;
      background: #1e293b; color: #cbd5e1; font-weight: 600; cursor: pointer; font-size: 0.92rem;
    }
    .btn-reset:hover { background: #334155; }

    /* Right Column Result Cards */
    .result-section { display: flex; flex-direction: column; gap: 12px; }
    .box-card {
      background: #0d1524; border: 1px solid #1e293b; border-radius: 12px;
      padding: 12px 14px; display: flex; flex-direction: column; gap: 6px;
    }
    .box-header {
      font-size: 0.85rem; font-weight: 700; color: #94a3b8;
      display: flex; justify-content: space-between; align-items: center;
    }
    .transcript-text {
      font-size: 1.15rem; font-weight: 700; color: #38bdf8;
      line-height: 1.4; word-break: break-word;
    }
    .reply-text {
      font-size: 1.12rem; color: #f8fafc; line-height: 1.55;
      border-left: 3.5px solid var(--primary); padding-left: 10px;
    }

    /* Place Value Chips */
    .place-value-chips { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 6px; }
    .pv-chip {
      background: rgba(56, 189, 248, 0.12); border: 1px solid rgba(56, 189, 248, 0.35);
      color: #7dd3fc; border-radius: 6px; padding: 5px 10px; font-size: 0.88rem; font-weight: 600;
    }

    /* Step Items */
    .steps-list { display: flex; flex-direction: column; gap: 8px; margin-top: 4px; }
    .step-item {
      background: #131c2e; border: 1px solid #24324a; border-left: 3.5px solid var(--accent);
      border-radius: 8px; padding: 10px 12px; font-size: 0.95rem; line-height: 1.5;
    }
    .step-item strong { color: #c7d2fe; display: block; margin-bottom: 2px; font-size: 0.92rem; }

    /* Table Grid */
    .table-grid {
      display: grid; grid-template-columns: repeat(auto-fit, minmax(110px, 1fr));
      gap: 6px; margin-top: 8px;
    }
    .table-cell {
      background: #1e293b; border: 1px solid #334155; border-radius: 6px;
      padding: 6px; text-align: center; font-size: 0.88rem;
    }
    .table-cell span.highlight { color: #facc15; font-weight: 700; }

    .audio-replay-btn {
      align-self: flex-start; background: #1e293b; border: 1px solid #334155;
      color: #38bdf8; padding: 7px 12px; border-radius: 8px; cursor: pointer;
      font-size: 0.88rem; font-weight: 600; display: inline-flex; align-items: center; gap: 6px;
    }
    .audio-replay-btn:hover { background: #334155; }

    /* Developer Drawer */
    .dev-drawer {
      background: #090e17; border: 1px solid #1e293b; border-radius: 12px;
      padding: 10px 14px; margin-top: 6px;
    }
    .dev-drawer summary {
      cursor: pointer; color: #64748b; font-size: 0.85rem; font-weight: 600; user-select: none;
    }
    .dev-drawer summary:hover { color: #94a3b8; }
    .dev-log-box {
      margin-top: 8px; background: #05080f; border-radius: 6px; padding: 10px;
      font-family: ui-monospace, Menlo, monospace; font-size: 0.82rem; color: #cbd5e1;
      max-height: 180px; overflow-y: auto; white-space: pre-wrap; line-height: 1.35;
    }
  </style>
</head>
<body>
  <div class="app-container">
    <!-- Top Header -->
    <header>
      <div class="brand-title">
        <span>🦉</span>
        <span class="highlight">गणित मित्र</span>
        <span style="font-size:1.3rem; color:#94a3b8; font-weight:500;">(Ganit Mitra)</span>
      </div>
      <p class="brand-subtitle">100% Offline, Voice-First Marathi Math Assistant | इयत्ता १ ते ६</p>
    </header>

    <!-- Friendly Mascot Prompt -->
    <div class="mascot-banner">
      <div class="mascot-avatar">🦉</div>
      <div class="mascot-text" id="mascotText">
        नमस्कार! <strong>माइक दाबा आणि गणिताचा प्रश्न बोला (किंवा इंग्रजीत/मराठीत टाइप करा).</strong><br>
        मी तो अचूक वाचून दाखवेन आणि मग सोप्या पायऱ्यांत समजावून सांगेन!
      </div>
    </div>

    <!-- Main Split-Screen Grid -->
    <div class="split-grid">
      <!-- LEFT COLUMN: Voice & Input Controls -->
      <div class="studio-card">
        <div class="studio-header">
          <div class="studio-title">
            <span>🎙️</span>
            <span>आवाज इनपुट</span>
            <span class="en">(Voice & Input Studio)</span>
          </div>
          <div class="dialogue-tag tag-idle" id="dialogueStateBadge">
            <span id="stateDot">⚪</span> <span id="stateText">तयार (READY)</span>
          </div>
        </div>

        <div class="voice-centerpiece">
          <button id="recordBtn" class="mic-button" title="माइक दाबा आणि बोला">
            <svg width="36" height="36" fill="currentColor" viewBox="0 0 24 24"><path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/><path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/></svg>
            <span id="recordBtnLabel">बोला (Push)</span>
          </button>

          <div class="vu-meter-bar-container" title="माइक आवाज पातळी">
            <div id="vuMeter" class="vu-meter-fill"></div>
          </div>

          <p id="micHint" class="mic-hint">माइक सुरू करण्यासाठी बटण दाबा</p>
        </div>

        <!-- Quick 1-Tap Preset Chips -->
        <span class="chips-section-title">सोपी चाचणी बटणे / Quick Examples:</span>
        <div class="preset-chips">
          <button class="chip" onclick="sendPreset('सात अधिक आठ किती')">➕ ७ + ८ (7 + 8)</button>
          <button class="chip" onclick="sendPreset('एकोणीस गुणिले सात')">✖️ १९ × ७ (19 × 7)</button>
          <button class="chip" onclick="sendPreset('पंधरा मधून सात वजा')">➖ १५ - ७ (15 - 7)</button>
          <button class="chip chip-table" onclick="sendPreset('पाचचा पाढा सांग')">📖 ५ चा पाढा (Table 5)</button>
          <button class="chip chip-table" onclick="sendPreset('अठरा चा पाढा सांग')">📖 १८ चा पाढा (Table 18)</button>
          <button class="chip chip-table" onclick="sendPreset('वीस चा पाढा सांग')">📖 २० चा पाढा (Table 20)</button>
          <button class="chip chip-shape" onclick="sendPreset('बाजू ५ असलेल्या चौरसाचे क्षेत्रफळ')">📐 चौरस क्षेत्रफळ (Square)</button>
          <button class="chip chip-shape" onclick="sendPreset('लांबी ६ आणि रुंदी ४ असलेल्या आयताची परिमिती')">📐 आयत परिमिती (Rectangle)</button>
          <button class="chip chip-yes" onclick="sendPreset('हो')">👍 "हो" (Yes / Confirm)</button>
          <button class="chip chip-no" onclick="sendPreset('नाही')">🔄 "नाही" (No / Cancel)</button>
        </div>

        <!-- Bilingual Input Field -->
        <div class="input-row">
          <input type="text" id="keyboardInput" placeholder="English or Marathi (e.g. 19*7, table of 5, 100+33, yes)..." onkeydown="if(event.key==='Enter') sendTextInput()">
          <button class="btn-send" onclick="sendTextInput()">पाठवा</button>
          <button class="btn-reset" onclick="resetState()">रीसेट</button>
        </div>
      </div>

      <!-- RIGHT COLUMN: Transcription & Smart Results -->
      <div class="studio-card">
        <div class="studio-header">
          <div class="studio-title">
            <span>📋</span>
            <span>निकाल व स्पष्टीकरण</span>
            <span class="en">(Results & Solution)</span>
          </div>
          <button id="replayBtn" class="audio-replay-btn" style="display:none;" onclick="replayAudio()">
            <span>🔊</span> पुन्हा ऐका
          </button>
        </div>

        <div class="result-section">
          <!-- 1. What You Said (Transcript) -->
          <div class="box-card">
            <div class="box-header">
              <span>🗣️ तुम्ही काय बोललात (Recognized Input):</span>
              <span id="confBadge" style="color:#38bdf8; font-size:0.8rem;">-</span>
            </div>
            <div id="transcriptDisplay" class="transcript-text">—</div>
          </div>

          <!-- 2. App Spoken Response -->
          <div class="box-card">
            <div class="box-header">
              <span>🤖 ॲपचा प्रतिसाद (Spoken Reply):</span>
            </div>
            <div id="replyText" class="reply-text">प्रश्नाची वाट पाहत आहे... (Ask a question or tap a button)</div>
          </div>

          <!-- 3. Place Value & Steps -->
          <div class="box-card">
            <div class="box-header">
              <span>💡 स्थानिक किंमत व सोडवण्याच्या पायऱ्या (Place Value & Steps):</span>
            </div>
            <div id="placeValueContainer" class="place-value-chips"></div>
            <div id="stepsContainer" class="steps-list"></div>
          </div>
        </div>

        <audio id="audioPlayer" style="display:none;"></audio>
      </div>
    </div>

    <!-- Collapsible Developer Diagnostics -->
    <details class="dev-drawer">
      <summary>🔧 शिक्षक व तांत्रिक माहिती (Developer & Teacher Diagnostic Drawer)</summary>
      <div style="display:flex; justify-content:space-between; margin-top:6px; font-size:0.82rem; color:#94a3b8;">
        <div>VAD: <span id="mGate" style="color:#38bdf8;">-</span></div>
        <div>विश्वासार्हता: <span id="mConf" style="color:#38bdf8;">-</span></div>
        <div>इरादा: <span id="mIntent" style="color:#38bdf8;">-</span></div>
        <div>वेळ: <span id="mLatency" style="color:#38bdf8;">-</span></div>
      </div>
      <div id="debugLog" class="dev-log-box">सिस्टम पूर्णपणे ऑफलाइन आणि तयार आहे.</div>
    </details>
  </div>

  <script>
    let audioCtx = null;
    let micStream = null;
    let scriptNode = null;
    let audioBuffers = [];
    let isRecording = false;
    let maxRecordingTimeout = null;
    let currentAudioB64 = null;

    const recordBtn = document.getElementById('recordBtn');
    const recordBtnLabel = document.getElementById('recordBtnLabel');
    const micHint = document.getElementById('micHint');
    const vuMeter = document.getElementById('vuMeter');
    const transcriptDisplay = document.getElementById('transcriptDisplay');
    const replyText = document.getElementById('replyText');
    const stepsContainer = document.getElementById('stepsContainer');
    const placeValueContainer = document.getElementById('placeValueContainer');
    const audioPlayer = document.getElementById('audioPlayer');
    const replayBtn = document.getElementById('replayBtn');
    const debugLog = document.getElementById('debugLog');
    const dialogueStateBadge = document.getElementById('dialogueStateBadge');
    const stateText = document.getElementById('stateText');
    const stateDot = document.getElementById('stateDot');
    const mascotText = document.getElementById('mascotText');
    const confBadge = document.getElementById('confBadge');

    recordBtn.addEventListener('click', async () => {
      if (!isRecording) {
        await startRecording();
      } else {
        await stopRecording();
      }
    });

    async function startRecording() {
      try {
        audioBuffers = [];
        const stream = await navigator.mediaDevices.getUserMedia({
          audio: { channelCount: 1, echoCancellation: true, noiseSuppression: false, autoGainControl: true }
        });
        micStream = stream;

        audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        const source = audioCtx.createMediaStreamSource(stream);
        
        scriptNode = audioCtx.createScriptProcessor(4096, 1, 1);
        scriptNode.onaudioprocess = (e) => {
          if (!isRecording) return;
          const input = e.inputBuffer.getChannelData(0);
          audioBuffers.push(new Float32Array(input));
          
          let sum = 0;
          for (let i = 0; i < input.length; i++) sum += input[i] * input[i];
          const rms = Math.sqrt(sum / input.length);
          const pct = Math.min(100, Math.round(rms * 450));
          vuMeter.style.width = pct + "%";
        };

        source.connect(scriptNode);
        scriptNode.connect(audioCtx.destination);

        isRecording = true;
        recordBtn.classList.add('recording');
        recordBtnLabel.innerText = "थांबा (Stop)";
        micHint.innerText = "🎙️ मी ऐकत आहे... बोलणे संपल्यावर थांबा दाबा!";
        mascotText.innerHTML = "मी कान देऊन ऐकत आहे... <strong>तुझा गणिताचा प्रश्न सांगा!</strong>";

        clearTimeout(maxRecordingTimeout);
        maxRecordingTimeout = setTimeout(() => {
          if (isRecording) stopRecording();
        }, 8000);
      } catch (err) {
        alert("माइक वापरण्यास परवानगी आवश्यक आहे: " + err.message);
      }
    }

    async function stopRecording() {
      if (!isRecording) return;
      isRecording = false;
      clearTimeout(maxRecordingTimeout);

      recordBtn.classList.remove('recording');
      recordBtnLabel.innerText = "बोला (Push)";
      micHint.innerText = "⏳ गणित सोडवत आहे...";
      vuMeter.style.width = "0%";

      if (scriptNode) {
        scriptNode.disconnect();
        scriptNode = null;
      }
      if (micStream) {
        micStream.getTracks().forEach(t => t.stop());
        micStream = null;
      }

      const sampleRate = audioCtx ? audioCtx.sampleRate : 16000;
      if (audioCtx) {
        audioCtx.close();
        audioCtx = null;
      }

      if (audioBuffers.length === 0) {
        micHint.innerText = "आवाज ऐकू आला नाही. पुन्हा प्रयत्न करा.";
        return;
      }

      const wavBlob = encodeWAV(audioBuffers, sampleRate);
      await uploadAudio(wavBlob);
    }

    function encodeWAV(buffers, sampleRate) {
      let totalLength = 0;
      for (let i = 0; i < buffers.length; i++) totalLength += buffers[i].length;
      const merged = new Float32Array(totalLength);
      let offset = 0;
      for (let i = 0; i < buffers.length; i++) {
        merged.set(buffers[i], offset);
        offset += buffers[i].length;
      }

      const buffer = new ArrayBuffer(44 + merged.length * 2);
      const view = new DataView(buffer);

      function writeStr(offset, str) {
        for (let i = 0; i < str.length; i++) view.setUint8(offset + i, str.charCodeAt(i));
      }

      writeStr(0, 'RIFF');
      view.setUint32(4, 36 + merged.length * 2, true);
      writeStr(8, 'WAVE');
      writeStr(12, 'fmt ');
      view.setUint32(16, 16, true);
      view.setUint16(20, 1, true); // PCM
      view.setUint16(22, 1, true); // Mono
      view.setUint32(24, sampleRate, true);
      view.setUint32(28, sampleRate * 2, true);
      view.setUint16(32, 2, true);
      view.setUint16(34, 16, true);
      writeStr(36, 'data');
      view.setUint32(40, merged.length * 2, true);

      let idx = 44;
      for (let i = 0; i < merged.length; i++) {
        let s = Math.max(-1, Math.min(1, merged[i]));
        view.setInt16(idx, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
        idx += 2;
      }
      return new Blob([view], { type: 'audio/wav' });
    }

    async function uploadAudio(blob) {
      try {
        const res = await fetch('/api/process_audio', {
          method: 'POST',
          headers: { 'Content-Type': 'audio/wav' },
          body: blob
        });
        const data = await res.json();
        renderResult(data);
      } catch (err) {
        debugLog.innerText += "\\nError: " + err.message;
        micHint.innerText = "त्रुटी आली. कृपया पुन्हा प्रयत्न करा.";
      }
    }

    async function sendPreset(text) {
      debugLog.innerText += `\\n[इनपुट पाठवले]: "${text}"`;
      try {
        const res = await fetch('/api/text_input', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text })
        });
        const data = await res.json();
        renderResult(data);
      } catch (err) {
        debugLog.innerText += "\\nError: " + err.message;
      }
    }

    async function sendTextInput() {
      const inp = document.getElementById('keyboardInput');
      const text = inp.value.trim();
      if (!text) return;
      inp.value = '';
      sendPreset(text);
    }

    async function resetState() {
      await fetch('/api/reset', { method: 'POST' });
      updateBadge('IDLE');
      transcriptDisplay.innerText = "—";
      replyText.innerText = "स्थिती रीसेट झाली. नवीन प्रश्न विचारा किंवा बोला!";
      stepsContainer.innerHTML = "";
      placeValueContainer.innerHTML = "";
      replayBtn.style.display = "none";
      mascotText.innerHTML = "स्थिती रीसेट झाली. <strong>नवीन प्रश्न विचारा!</strong>";
      debugLog.innerText += "\\n[System]: Reset to IDLE.";
    }

    function updateBadge(state) {
      if (state === 'AWAITING_CONFIRMATION') {
        dialogueStateBadge.className = "dialogue-tag tag-confirm";
        stateDot.innerText = "🟡";
        stateText.innerText = "पुष्टी हवी (Confirm: हो / नाही?)";
        mascotText.innerHTML = "मी बरोबर ऐकलं का? <strong>'हो' म्हणा किंवा 'हो' बटण दाबा!</strong>";
      } else {
        dialogueStateBadge.className = "dialogue-tag tag-idle";
        stateDot.innerText = "⚪";
        stateText.innerText = "तयार (READY)";
      }
    }

    function replayAudio() {
      if (currentAudioB64) {
        audioPlayer.src = "data:audio/wav;base64," + currentAudioB64;
        audioPlayer.play().catch(e => console.log(e));
      }
    }

    function renderResult(data) {
      micHint.innerText = "माइक सुरू करण्यासाठी बटण दाबा";
      updateBadge(data.state || "IDLE");

      // 1. Transcript Display
      transcriptDisplay.innerText = data.transcript || "—";
      if (data.asr && data.asr.overall_confidence) {
        confBadge.innerText = "विश्वासार्हता: " + (data.asr.overall_confidence * 100).toFixed(0) + "%";
      } else {
        confBadge.innerText = "विश्वासार्हता: 100%";
      }

      // 2. Reply Text
      replyText.innerText = data.spoken_reply || "कोणताही प्रतिसाद नाही";

      // 3. Place Value Chips
      placeValueContainer.innerHTML = "";
      if (data.solution && data.solution.result_int !== null && data.solution.result_int !== undefined) {
        const val = data.solution.result_int;
        if (val >= 1000) {
          const th = Math.floor(val / 1000);
          placeValueContainer.innerHTML += `<div class="pv-chip">📦 ${th} हजार (${th*1000})</div>`;
        }
        if (val >= 100) {
          const h = Math.floor((val % 1000) / 100);
          if (h > 0) placeValueContainer.innerHTML += `<div class="pv-chip">💯 ${h} शतक (${h*100})</div>`;
        }
        const tens = Math.floor((val % 100) / 10);
        if (tens > 0) placeValueContainer.innerHTML += `<div class="pv-chip">🔟 ${tens} दशक (${tens*10})</div>`;
        const units = val % 10;
        placeValueContainer.innerHTML += `<div class="pv-chip">1️⃣ ${units} एकक (${units})</div>`;
      }

      // 4. Step-by-Step Breakdown
      stepsContainer.innerHTML = "";
      if (data.solution && data.solution.steps) {
        const isTable = data.solution.steps.some(s => s.visual_type === 'TABLE_GRID');
        if (isTable) {
          const gridDiv = document.createElement('div');
          gridDiv.className = 'table-grid';
          data.solution.steps.forEach(s => {
            const cell = document.createElement('div');
            cell.className = 'table-cell';
            cell.innerHTML = `<span class="highlight">${s.title_mr}</span><br><small style="color:#94a3b8;">${s.explanation_mr.split('(')[0]}</small>`;
            gridDiv.appendChild(cell);
          });
          stepsContainer.appendChild(gridDiv);
        } else {
          data.solution.steps.forEach(s => {
            const div = document.createElement('div');
            div.className = 'step-item';
            div.innerHTML = `<strong>पायरी ${s.step_num}: ${s.title_mr}</strong>${s.explanation_mr}`;
            stepsContainer.appendChild(div);
          });
        }
      }

      // 5. Audio Playback
      if (data.audio_b64) {
        currentAudioB64 = data.audio_b64;
        replayBtn.style.display = "inline-flex";
        replayAudio();
      } else {
        replayBtn.style.display = "none";
      }

      // 6. Diagnostics
      document.getElementById('mGate').innerText = data.gate ? data.gate.status : "READY";
      document.getElementById('mConf').innerText = data.asr ? (data.asr.overall_confidence * 100).toFixed(1) + "%" : "100%";
      document.getElementById('mIntent').innerText = data.classification ? data.classification.intent.label : "direct";
      document.getElementById('mLatency').innerText = data.timings_ms ? data.timings_ms.total.toFixed(1) + " ms" : "-";

      let logStr = "\\n" + "=".repeat(48) + "\\n";
      logStr += `[ऐकले/Input] : "${data.transcript || ''}"\\n`;
      logStr += `[स्थिती/State]: ${data.state}\\n`;
      if (data.timings_ms) logStr += `[वेळ/Latency]: ${data.timings_ms.total.toFixed(1)} ms\\n`;
      debugLog.innerText += logStr;
      debugLog.scrollTop = debugLog.scrollHeight;
    }
  </script>
</body>
</html>
"""

class WebHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        global session
        if self.path == "/api/reset":
            session.dialogue_state = "IDLE"
            session.pending_ast = None
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok"}).encode())
            return

        if self.path == "/api/text_input":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            req = json.loads(body.decode("utf-8"))
            text = req.get("text", "").strip()

            t_start = time.perf_counter()
            spoken_reply_text = ""
            solution_dict = None
            audio_b64 = None

            # Normalize confirmation text
            norm_word = session.parser.normalize_text(text)
            if norm_word in ("हो", "होय") and session.dialogue_state == "AWAITING_CONFIRMATION":
                if session.pending_ast:
                    ast = session.pending_ast
                    sol = None
                    if ast.op in ("ADD", "SUB", "MUL", "DIV"):
                        l_val = ast.left.value
                        r_val = ast.right.value
                        sol = session.math_engine.solve(ast.op, l_val, r_val)
                        spoken_reply_text = f"बरोबर! उत्तर आहे: {sol.result_str_mr} ({sol.result_int}). {sol.full_speech_mr}"
                        audio = session.audio_bank.assemble_answer(sol.result_int)
                        audio_b64 = self._encode_audio(audio)
                    elif ast.op == "TABLE":
                        l_val = ast.left.value if ast.left else 5
                        sol = session.math_engine.solve("TABLE", l_val)
                        spoken_reply_text = sol.full_speech_mr
                        audio = session.audio_bank.synthesize_sentence(sol.full_speech_mr[:180])
                        audio_b64 = self._encode_audio(audio)
                    elif ast.op == "SHAPE_SQUARE":
                        l_val = ast.left.value if ast.left else None
                        sol = session.math_engine.solve("SHAPE_SQUARE", l_val, sub_type=ast.unit)
                        spoken_reply_text = f"बरोबर! {sol.full_speech_mr}"
                        audio = session.audio_bank.synthesize_sentence(spoken_reply_text)
                        audio_b64 = self._encode_audio(audio)
                    elif ast.op == "SHAPE_RECTANGLE":
                        l_val = ast.left.value if ast.left else None
                        r_val = ast.right.value if ast.right else None
                        sol = session.math_engine.solve("SHAPE_RECTANGLE", l_val, r_val, sub_type=ast.unit)
                        spoken_reply_text = f"बरोबर! {sol.full_speech_mr}"
                        audio = session.audio_bank.synthesize_sentence(spoken_reply_text)
                        audio_b64 = self._encode_audio(audio)
                    elif ast.op == "NUMBER_ONLY":
                        l_val = ast.left.value if ast.left else 0
                        sol = session.math_engine.solve("NUMBER_ONLY", l_val)
                        spoken_reply_text = f"बरोबर! {sol.full_speech_mr}"
                        audio = session.audio_bank.assemble_answer(int(sol.result_val))
                        audio_b64 = self._encode_audio(audio)

                    if sol:
                        solution_dict = {
                            "result_int": sol.result_int,
                            "result_str_mr": sol.result_str_mr,
                            "steps": [{"step_num": s.step_num, "title_mr": s.title_mr, "explanation_mr": s.explanation_mr, "visual_type": s.visual_type} for s in sol.steps]
                        }
                session.dialogue_state = "IDLE"
                session.pending_ast = None
            elif norm_word in ("नाही", "नाहीं") and session.dialogue_state == "AWAITING_CONFIRMATION":
                spoken_reply_text = "काही हरकत नाही, प्रश्न पुन्हा सांगशील का?"
                session.dialogue_state = "IDLE"
                session.pending_ast = None
            else:
                ast = session.parser.parse(text)
                if ast.ambiguity.is_ambiguous:
                    spoken_reply_text = ast.ambiguity.clarification_question
                elif ast.op in ("ADD", "SUB", "MUL", "DIV"):
                    a = int(ast.left.value)
                    b = int(ast.right.value)
                    op_mr = {"ADD": "अधिक", "SUB": "वजा", "MUL": "गुणिले", "DIV": "भागिले"}.get(ast.op, ast.op)
                    spoken_reply_text = f"तू विचारलंस: {a} {op_mr} {b} किती? बरोबर आहे का? (हो / नाही म्हणा)"
                    audio = session.audio_bank.assemble_readback(ast.op, a, b)
                    audio_b64 = self._encode_audio(audio)
                    session.pending_ast = ast
                    session.dialogue_state = "AWAITING_CONFIRMATION"
                elif ast.op == "TABLE":
                    t_val = int(ast.left.value) if ast.left else 5
                    spoken_reply_text = f"तू विचारलंस: {t_val} चा पाढा. बरोबर आहे का? (हो / नाही म्हणा)"
                    audio = session.audio_bank.synthesize_sentence(spoken_reply_text)
                    audio_b64 = self._encode_audio(audio)
                    session.pending_ast = ast
                    session.dialogue_state = "AWAITING_CONFIRMATION"
                elif ast.op == "SHAPE_SQUARE":
                    sub_mr = "परिमिती" if ast.unit == "PERIMETER" else "क्षेत्रफळ"
                    s_txt = f"बाजू {int(ast.left.value)} असलेल्या " if ast.left else ""
                    spoken_reply_text = f"तू विचारलंस: {s_txt}चौरसाचे {sub_mr}. बरोबर आहे का? (हो / नाही म्हणा)"
                    audio = session.audio_bank.synthesize_sentence(spoken_reply_text)
                    audio_b64 = self._encode_audio(audio)
                    session.pending_ast = ast
                    session.dialogue_state = "AWAITING_CONFIRMATION"
                elif ast.op == "SHAPE_RECTANGLE":
                    sub_mr = "परिमिती" if ast.unit == "PERIMETER" else "क्षेत्रफळ"
                    l_txt = f"लांबी {int(ast.left.value)} व रुंदी {int(ast.right.value)} असलेल्या " if ast.left and ast.right else ""
                    spoken_reply_text = f"तू विचारलंस: {l_txt}आयताचे {sub_mr}. बरोबर आहे का? (हो / नाही म्हणा)"
                    audio = session.audio_bank.synthesize_sentence(spoken_reply_text)
                    audio_b64 = self._encode_audio(audio)
                    session.pending_ast = ast
                    session.dialogue_state = "AWAITING_CONFIRMATION"
                elif ast.op == "NUMBER_ONLY":
                    val = int(ast.left.value)
                    spoken_reply_text = f"तू संख्या सांगितलीस: {val}. बरोबर आहे का?"
                    audio = session.audio_bank.assemble_answer(val)
                    audio_b64 = self._encode_audio(audio)
                    session.pending_ast = ast
                    session.dialogue_state = "AWAITING_CONFIRMATION"
                else:
                    spoken_reply_text = "गणिताचा प्रश्न पुन्हा सांगशील का? (उदा: १९ गुणिले ७ किंवा ५ चा पाढा)"

            t_total = (time.perf_counter() - t_start) * 1000.0
            resp_data = {
                "transcript": text,
                "state": session.dialogue_state,
                "spoken_reply": spoken_reply_text,
                "solution": solution_dict,
                "audio_b64": audio_b64,
                "timings_ms": {"gate": 0.0, "asr": 0.0, "total": t_total}
            }

            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(resp_data, ensure_ascii=False).encode("utf-8"))
            return

        if self.path == "/api/process_audio":
            length = int(self.headers.get("Content-Length", 0))
            raw_body = self.rfile.read(length)

            content_type = self.headers.get("Content-Type", "")
            audio_bytes = raw_body
            if "boundary=" in content_type:
                boundary = content_type.split("boundary=")[1].strip('"').encode()
                parts = raw_body.split(b"--" + boundary)
                for p in parts:
                    if b"\r\n\r\n" in p:
                        header_part, data_part = p.split(b"\r\n\r\n", 1)
                        if b"filename=" in header_part:
                            audio_bytes = data_part.rsplit(b"\r\n", 1)[0]
                            break

            try:
                data, sr = sf.read(io.BytesIO(audio_bytes))
                if len(data.shape) > 1:
                    data = data[:, 0]
                if sr != 16000:
                    num_samples = int(len(data) * 16000 / sr)
                    data = scipy.signal.resample(data, num_samples).astype(np.float32)

                res = session.process_turn(data.astype(np.float32), source_name="WebMic", play_speech=False)

                audio_b64 = None
                if res.get("speech_audio") is not None and len(res["speech_audio"]) > 0:
                    audio_b64 = self._encode_audio(res["speech_audio"])

                solution_dict = None
                if res.get("solution"):
                    s = res["solution"]
                    solution_dict = {
                        "result_int": s.result_int,
                        "result_str_mr": s.result_str_mr,
                        "steps": [{"step_num": st.step_num, "title_mr": st.title_mr, "explanation_mr": st.explanation_mr, "visual_type": st.visual_type} for st in s.steps]
                    }

                resp = {
                    "transcript": res["transcript"],
                    "state": res["state"],
                    "spoken_reply": res["spoken_reply"],
                    "audio_b64": audio_b64,
                    "solution": solution_dict,
                    "timings_ms": {"gate": 8.0, "asr": 45.0, "total": res["latency_ms"]},
                    "gate": {"status": res["gate"].status, "confidence": res["gate"].confidence} if res.get("gate") else None,
                    "asr": {"overall_confidence": res["asr"].overall_confidence} if res.get("asr") else None,
                    "classification": {
                        "intent": {"label": res["classifier"].intent.label},
                        "decision": {
                            "label": res["classifier"].decision.label,
                            "metadata": {"reason": res["classifier"].decision.metadata.get("reason", "")}
                        }
                    } if res.get("classifier") else None
                }
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps(resp, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                traceback.print_exc()
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({
                    "error": str(e),
                    "state": session.dialogue_state if session else "IDLE",
                    "spoken_reply": f"आवाज प्रक्रिया त्रुटी: {str(e)}"
                }).encode())

    def _encode_audio(self, audio_data: np.ndarray) -> str:
        if audio_data is None or len(audio_data) == 0:
            return ""
        buf = io.BytesIO()
        sf.write(buf, audio_data, 16000, format='WAV')
        buf.seek(0)
        return base64.b64encode(buf.read()).decode('utf-8')

def run_server(port: int = 8765):
    global session
    session = GanitMitraSession()
    server = ThreadingHTTPServer(("0.0.0.0", port), WebHandler)
    print("\n" + "=" * 70)
    print(f"  🦉 गणित मित्र (GANIT MITRA) BILINGUAL STUDIO RUNNING!")
    print(f"  Open in your browser: http://localhost:{port}")
    print("=" * 70 + "\n")
    server.serve_forever()

if __name__ == '__main__':
    run_server(8765)
