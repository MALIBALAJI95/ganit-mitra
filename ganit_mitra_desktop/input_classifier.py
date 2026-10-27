from dataclasses import dataclass
from typing import Dict, Any, List
import re
from ganit_mitra_desktop.audio_gate import AudioGateResult
from ganit_mitra_desktop.asr_engine import ASRResult

MARATHI_COMMANDS = {
    "हो": "yes",
    "होय": "yes",
    "नाही": "no",
    "नाहीं": "no",
    "परत सांग": "repeat",
    "पुन्हा सांग": "repeat",
    "हळू सांग": "slower",
    "हळू": "slower",
    "पुढे": "next",
    "पुढचा": "next",
    "पुढील": "next",
    "मदत": "help",
    "साहाय्य": "help",
    "थांब": "stop",
    "थांबा": "stop"
}

MARATHI_MATH_KEYWORDS = {
    # Addition
    "बेरीज", "आणि", "अधिक", "जमा", "मिळवले", "वाढवले", "प्लस", "plus",
    # Subtraction
    "वजा", "वजाबाकी", "मधून", "कमी", "गेले", "उरले", "मायनस", "minus",
    # Multiplication
    "गुणिले", "गुणाकार", "पट", "पाढे", "पाढा", "पाडा", "पाड", "पडा", "पाडे", "गुणि", "गुणले", "इंटू", "into", "times",
    # Division
    "भागिले", "भागाकार", "भागले", "वाटले", "समान", "डिवाइड", "divide",
    # Tables
    "टेबल", "table",
    # Shapes & Geometry
    "चौरस", "आयत", "क्षेत्रफळ", "परिमिती", "लांबी", "रुंदी", "बाजू", "square", "rectangle", "area", "perimeter",
    # Fractions & Units
    "अर्धा", "अर्था", "पाव", "पाऊण", "सव्वा", "दीड", "अडीच", "छेद", "अंश",
    "रुपये", "पैसे", "दशांश", "पूर्णांक"
}

MARATHI_DIGIT_WORDS = {
    "शून्य", "एक", "दोन", "तीन", "चार", "पाच", "सहा", "सात", "आठ", "नऊ", "दहा",
    "अकरा", "बारा", "तेरा", "चौदा", "पंधरा", "सोळा", "सतरा", "अठरा", "एकोणीस", "वीस",
    "एकवीस", "बावीस", "तेवीस", "चोवीस", "पंचवीस", "सव्वीस", "सत्तावीस", "अठ्ठावीस", "एकोणतीस", "तीस",
    "एकतीस", "बत्तीस", "तेहतीस", "चौतीस", "पस्तीस", "छत्तीस", "सदतीस", "अडतीस", "एकोणचाळीस", "चाळीस",
    "एक्केचाळीस", "बेचाळीस", "त्रेचाळीस", "चव्वेचाळीस", "पंचेचाळीस", "शेहेचाळीस", "सत्तेचाळीस", "अठ्ठेचाळीस", "एकोणपन्नास", "पन्नास",
    "एक्कावन्न", "बावन्न", "त्रेपन्न", "चौपन्न", "पंचावन्न", "छप्पन्न", "सत्तावन्न", "अठ्ठावन्न", "एकोणसाठ", "साठ",
    "एकसष्ठ", "बासष्ठ", "त्रेसष्ठ", "चौसष्ठ", "पासष्ठ", "सहासष्ठ", "सदुसष्ठ", "अडुसष्ठ", "एकोणसत्तर", "सत्तर",
    "एकाहत्तर", "बाहत्तर", "त्र्याहत्तर", "चौहत्तर", "पंच्याहत्तर", "शहात्तर", "सत्त्याहत्तर", "अठ्ठ्याहत्तर", "एकोणऐंशी", "ऐंशी",
    "एक्यांशी", "ब्यांशी", "त्र्यांशी", "चौऱ्यांशी", "पंच्यांशी", "शहांशी", "सत्त्यांशी", "अठ्ठ्यांशी", "एकोणनव्वद", "नव्वद",
    "एक्याण्णव", "ब्याण्णव", "त्र्याण्णव", "चौऱ्याण्णव", "पंच्याण्णव", "शहाण्णव", "सत्त्याण्णव", "अठ्ठ्याण्णव", "नव्व्याण्णव", "शंभर",
    "दोनशे", "तीनशे", "चारशे", "पाचशे", "सहाशे", "सातशे", "आठशे", "नऊशे", "हजार", "लाख"
}

# Add common dialect / ASR variants
MARATHI_VARIANTS = {
    "पाँच": "पाच", "बारह": "बारा", "ब्येचाळीस": "बेचाळीस", "दोन शे": "दोनशे",
    "तीन शे": "तीनशे", "चार शे": "चारशे", "पाच शे": "पाचशे", "सहा शे": "सहाशे",
    "सात शे": "सातशे", "आठ शे": "आठशे", "नऊ शे": "नऊशे", "अठ्ठरा": "अठरा",
    "सोळा": "सोळा", "गुढीले": "गुणिले", "अदक": "अधिक", "वीज": "वीस", "विस": "वीस",
    "विज": "वीस", "अर्था": "अर्धा", "तेहेतीस": "तेहतीस"
}

@dataclass
class StageResult:
    label: str
    confidence: float
    metadata: Dict[str, Any]

@dataclass
class ClassificationResult:
    audio_gate: StageResult
    language_check: StageResult
    intent: StageResult
    decision: StageResult
    reprompt_prompt: str = ""

class InputClassifier:
    def __init__(self,
                 cmd_accept_threshold: float = 0.80,
                 cmd_confirm_threshold: float = 0.55):
        self.cmd_accept_threshold = cmd_accept_threshold
        self.cmd_confirm_threshold = cmd_confirm_threshold

    def classify(self, gate_res: AudioGateResult, asr_res: ASRResult) -> ClassificationResult:
        # Stage 1: Audio Gate
        audio_stage = StageResult(
            label=gate_res.status,
            confidence=gate_res.confidence,
            metadata={
                "duration_sec": gate_res.duration,
                "rms": gate_res.rms_energy,
                "peak": gate_res.peak,
                "speech_ratio": gate_res.speech_ratio
            }
        )

        if gate_res.status != "speech":
            reprompt = "काही ऐकू आले नाही, कृपया पुन्हा बोल." if gate_res.status == "silence" else "आवाज स्पष्ट नव्हता, कृपया शांत जागेत बोला."
            if gate_res.status == "too_short":
                reprompt = "आवाज खूप लहान होता, पूर्ण वाक्य बोला."
            elif gate_res.status == "clipped":
                reprompt = "आवाज खूप मोठा होता, थोडे हळू बोला."

            return ClassificationResult(
                audio_gate=audio_stage,
                language_check=StageResult("unclear", 0.0, {}),
                intent=StageResult("unknown", 0.0, {}),
                decision=StageResult("REPROMPT", gate_res.confidence, {"reason": f"audio_gate_{gate_res.status}"}),
                reprompt_prompt=reprompt
            )

        # Stage 2: Language Check
        text = asr_res.text.strip()
        if not text:
            return ClassificationResult(
                audio_gate=audio_stage,
                language_check=StageResult("not_marathi_like", 0.95, {"char_count": 0}),
                intent=StageResult("unknown", 0.0, {}),
                decision=StageResult("REPROMPT", 0.95, {"reason": "empty_transcript"}),
                reprompt_prompt="काही ऐकू आले नाही, पुन्हा सांगशील?"
            )

        # Devanagari Unicode range: \u0900 - \u097F
        alpha_chars = [c for c in text if c.isalpha() or ('\u0900' <= c <= '\u097F')]
        deva_chars = [c for c in alpha_chars if '\u0900' <= c <= '\u097F']
        deva_ratio = len(deva_chars) / max(1, len(alpha_chars))

        words = [w for w in re.split(r"[\s,?!]+", text) if w]
        known_words = 0
        all_vocab = MARATHI_MATH_KEYWORDS | MARATHI_DIGIT_WORDS | set(MARATHI_COMMANDS.keys()) | set(MARATHI_VARIANTS.keys())
        for w in words:
            if w in all_vocab or w.isdigit() or any('\u0966' <= c <= '\u096F' for c in w):
                known_words += 1
        lexicon_match_rate = known_words / max(1, len(words))

        if deva_ratio >= 0.70 and (lexicon_match_rate >= 0.30 or asr_res.overall_confidence >= 0.65):
            lang_label = "marathi_like"
            lang_conf = min(0.99, (deva_ratio * 0.5) + (lexicon_match_rate * 0.3) + (asr_res.overall_confidence * 0.2))
        elif deva_ratio < 0.40:
            lang_label = "not_marathi_like"
            lang_conf = 0.90
        else:
            lang_label = "unclear"
            lang_conf = 0.60

        lang_stage = StageResult(
            label=lang_label,
            confidence=lang_conf,
            metadata={
                "devanagari_ratio": deva_ratio,
                "lexicon_match_rate": lexicon_match_rate,
                "asr_conf": asr_res.overall_confidence
            }
        )

        if lang_label == "not_marathi_like":
            return ClassificationResult(
                audio_gate=audio_stage,
                language_check=lang_stage,
                intent=StageResult("unknown", 0.0, {}),
                decision=StageResult("REPROMPT", lang_conf, {"reason": "language_not_marathi"}),
                reprompt_prompt="कृपया मराठीत बोला."
            )

        # Stage 3: Intent Classification
        cleaned_lower = text.strip()
        matched_command = None
        for cmd in MARATHI_COMMANDS:
            if cleaned_lower == cmd or cleaned_lower.startswith(cmd + " ") or cleaned_lower.endswith(" " + cmd):
                matched_command = cmd
                break

        has_math_keyword = any(kw in text for kw in MARATHI_MATH_KEYWORDS) or any(op in text for op in ['+', '-', '*', '/', '×', '÷'])
        has_numbers = any(nw in text for nw in MARATHI_DIGIT_WORDS) or any(c.isdigit() or ('\u0966' <= c <= '\u096F') for c in text)

        if matched_command and not (has_math_keyword and has_numbers):
            intent_label = "command"
            intent_conf = min(0.99, asr_res.overall_confidence * 1.1)
            intent_meta = {"command": MARATHI_COMMANDS[matched_command], "matched_word": matched_command}
        elif has_math_keyword:
            intent_label = "math_question"
            intent_conf = asr_res.overall_confidence
            intent_meta = {"has_numbers": has_numbers}
        elif has_numbers and not has_math_keyword:
            intent_label = "number_answer"
            intent_conf = asr_res.overall_confidence
            intent_meta = {"raw_number": text}
        else:
            intent_label = "unknown"
            intent_conf = 0.50
            intent_meta = {}

        intent_stage = StageResult(label=intent_label, confidence=intent_conf, metadata=intent_meta)

        # Stage 4: Decision (ACCEPT | CONFIRM | REPROMPT)
        # CRITICAL CONSTRAINT: Math questions and number answers ALWAYS go through CONFIRM!
        if intent_label in ("math_question", "number_answer"):
            decision_label = "CONFIRM"
            decision_conf = asr_res.overall_confidence
            reprompt = ""
            decision_reason = "mandatory_math_readback_protocol"
        elif intent_label == "command":
            if intent_conf >= self.cmd_accept_threshold:
                decision_label = "ACCEPT"
                decision_conf = intent_conf
                reprompt = ""
                decision_reason = f"high_confidence_command (>={self.cmd_accept_threshold})"
            elif intent_conf >= self.cmd_confirm_threshold:
                decision_label = "CONFIRM"
                decision_conf = intent_conf
                reprompt = f"'{matched_command}' म्हणायचं आहे का?"
                decision_reason = f"medium_confidence_command (>={self.cmd_confirm_threshold})"
            else:
                decision_label = "REPROMPT"
                decision_conf = 1.0 - intent_conf
                reprompt = "समजले नाही, परत सांगशील का?"
                decision_reason = f"low_confidence_command (<{self.cmd_confirm_threshold})"
        else:
            decision_label = "REPROMPT"
            decision_conf = 0.85
            reprompt = "मला समजले नाही. गणिताचा प्रश्न किंवा उत्तर पुन्हा सांगशील का?"
            decision_reason = "unknown_intent"

        decision_stage = StageResult(
            label=decision_label,
            confidence=decision_conf,
            metadata={"reason": decision_reason, "thresholds": {"cmd_accept": self.cmd_accept_threshold, "cmd_confirm": self.cmd_confirm_threshold}}
        )

        return ClassificationResult(
            audio_gate=audio_stage,
            language_check=lang_stage,
            intent=intent_stage,
            decision=decision_stage,
            reprompt_prompt=reprompt
        )
