from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict, Any
import re

# Comprehensive Marathi number word mappings
MARATHI_0_TO_100: Dict[str, int] = {
    "शून्य": 0, "एक": 1, "दोन": 2, "तीन": 3, "चार": 4, "पाच": 5, "सहा": 6, "सात": 7, "आठ": 8, "नऊ": 9, "दहा": 10,
    "अकरा": 11, "बारा": 12, "तेरा": 13, "चौदा": 14, "पंधरा": 15, "सोळा": 16, "सतरा": 17, "अठरा": 18, "एकोणीस": 19, "वीस": 20,
    "एकवीस": 21, "बावीस": 22, "तेवीस": 23, "चोवीस": 24, "पंचवीस": 25, "सव्वीस": 26, "सत्तावीस": 27, "अठ्ठावीस": 28, "एकोणतीस": 29, "तीस": 30,
    "एकतीस": 31, "बत्तीस": 32, "तेहतीस": 33, "चौतीस": 34, "पस्तीस": 35, "छत्तीस": 36, "सदतीस": 37, "अडतीस": 38, "एकोणचाळीस": 39, "चाळीस": 40,
    "एक्केचाळीस": 41, "बेचाळीस": 42, "त्रेचाळीस": 43, "चव्वेचाळीस": 44, "पंचेचाळीस": 45, "शेहेचाळीस": 46, "सत्तेचाळीस": 47, "अठ्ठेचाळीस": 48, "एकोणपन्नास": 49, "पन्नास": 50,
    "एक्कावन्न": 51, "बावन्न": 52, "त्रेपन्न": 53, "चौपन्न": 54, "पंचावन्न": 55, "छप्पन्न": 56, "सत्तावन्न": 57, "अठ्ठावन्न": 58, "एकोणसाठ": 59, "साठ": 60,
    "एकसष्ठ": 61, "बासष्ठ": 62, "त्रेसष्ठ": 63, "चौसष्ठ": 64, "पासष्ठ": 65, "सहासष्ठ": 66, "सदुसष्ठ": 67, "अडुसष्ठ": 68, "एकोणसत्तर": 69, "सत्तर": 70,
    "एकाहत्तर": 71, "बाहत्तर": 72, "त्र्याहत्तर": 73, "चौहत्तर": 74, "पंच्याहत्तर": 75, "शहात्तर": 76, "सत्त्याहत्तर": 77, "अठ्ठ्याहत्तर": 78, "एकोणऐंशी": 79, "ऐंशी": 80,
    "एक्यांशी": 81, "ब्यांशी": 82, "त्र्यांशी": 83, "चौऱ्यांशी": 84, "पंच्यांशी": 85, "शहांशी": 86, "सत्त्यांशी": 87, "अठ्ठ्यांशी": 88, "एकोणनव्वद": 89, "नव्वद": 90,
    "एक्याण्णव": 91, "ब्याण्णव": 92, "त्र्याण्णव": 93, "चौऱ्याण्णव": 94, "पंच्याण्णव": 95, "शहाण्णव": 96, "सत्त्याण्णव": 97, "अठ्ठ्याण्णव": 98, "नव्व्याण्णव": 99, "शंभर": 100
}

MARATHI_HUNDREDS: Dict[str, int] = {
    "शंभर": 100, "दोनशे": 200, "तीनशे": 300, "चारशे": 400, "पाचशे": 500,
    "सहाशे": 600, "सातशे": 700, "आठशे": 800, "नऊशे": 900
}

FRACTION_WORDS: Dict[str, float] = {
    "पाव": 0.25,
    "अर्धा": 0.5,
    "अर्धी": 0.5,
    "पाऊण": 0.75,
    "सव्वा": 1.25,
    "दीड": 1.5,
    "अडीच": 2.5,
    "सव्वाशे": 125.0,
    "दीडशे": 150.0,
    "पावणेदोनशे": 175.0,
    "अडीचशे": 250.0
}

# Devanagari digit translation table
DEVA_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")

# Normalization dictionary for dialect variants & ASR phonetics
LEXICON_REPLACEMENTS = {
    "बारह": "बारा",
    "पाँच": "पाच",
    "पंद्र": "पंधरा",
    "ब्येचाळीस": "बेचाळीस",
    "दोन शे": "दोनशे",
    "तीन शे": "तीनशे",
    "चार शे": "चारशे",
    "पाच शे": "पाचशे",
    "सहा शे": "सहाशे",
    "सात शे": "सातशे",
    "आठ शे": "आठशे",
    "नऊ शे": "नऊशे",
    "अदक": "अधिक",
    "गुढीले": "गुणिले",
    "गुणे": "गुणिले",
    "भागे": "भागिले"
}

@dataclass
class ParsedNumber:
    value: float
    raw_str: str
    is_fraction: bool = False
    numerator: Optional[int] = None
    denominator: Optional[int] = None

@dataclass
class Ambiguity:
    is_ambiguous: bool
    missing_operand: Optional[str] = None  # 'left' | 'right' | 'operator'
    clarification_question: Optional[str] = None

@dataclass
class MathAST:
    op: str  # 'ADD' | 'SUB' | 'MUL' | 'DIV' | 'NUMBER_ONLY'
    left: Optional[ParsedNumber] = None
    right: Optional[ParsedNumber] = None
    unit: str = "NONE"  # 'NONE' | 'CURRENCY_INR'
    ambiguity: Ambiguity = field(default_factory=lambda: Ambiguity(is_ambiguous=False))
    raw_text: str = ""

class MarathiSpokenMathParser:
    def __init__(self):
        pass

    def normalize_text(self, text: str) -> str:
        s = text.strip()
        # Apply known replacements
        for k, v in LEXICON_REPLACEMENTS.items():
            s = re.sub(r'\b' + re.escape(k) + r'\b', v, s)
        # Normalize spaces
        s = re.sub(r'\s+', ' ', s)
        return s

    def parse_single_number(self, token_str: str) -> Optional[ParsedNumber]:
        token_str = token_str.strip()
        if not token_str:
            return None

        # 1. Fraction words
        if token_str in FRACTION_WORDS:
            val = FRACTION_WORDS[token_str]
            return ParsedNumber(value=val, raw_str=token_str, is_fraction=True)

        # 2. Devanagari or Western digits
        t_latin = token_str.translate(DEVA_DIGITS)
        try:
            if "." in t_latin:
                return ParsedNumber(value=float(t_latin), raw_str=token_str)
            elif t_latin.isdigit():
                return ParsedNumber(value=float(int(t_latin)), raw_str=token_str)
        except ValueError:
            pass

        # 3. Marathi words (0–100, hundreds)
        if token_str in MARATHI_0_TO_100:
            return ParsedNumber(value=float(MARATHI_0_TO_100[token_str]), raw_str=token_str)
        if token_str in MARATHI_HUNDREDS:
            return ParsedNumber(value=float(MARATHI_HUNDREDS[token_str]), raw_str=token_str)

        # 4. Multi-word phrases like "दोनशे पन्नास", "एक हजार पाचशे"
        words = token_str.split()
        if len(words) > 1:
            total = 0.0
            idx = 0
            has_match = False
            
            # Check thousands
            if len(words) >= 2 and words[1] == "हजार":
                mult = MARATHI_0_TO_100.get(words[0], None)
                if mult is not None:
                    total += mult * 1000
                    idx = 2
                    has_match = True

            # Check hundreds
            if idx < len(words) and words[idx] in MARATHI_HUNDREDS:
                total += MARATHI_HUNDREDS[words[idx]]
                idx += 1
                has_match = True
            elif idx + 1 < len(words) and words[idx+1] == "शे":
                mult = MARATHI_0_TO_100.get(words[idx], None)
                if mult is not None:
                    total += mult * 100
                    idx += 2
                    has_match = True

            # Remainder 0-99
            if idx < len(words) and words[idx] in MARATHI_0_TO_100:
                total += MARATHI_0_TO_100[words[idx]]
                idx += 1
                has_match = True

            if has_match and idx == len(words):
                return ParsedNumber(value=total, raw_str=token_str)

        return None

    def extract_numbers_and_spans(self, text: str) -> List[Tuple[ParsedNumber, int, int]]:
        words = text.split()
        results = []
        n = len(words)
        i = 0
        while i < n:
            matched = None
            matched_len = 0
            # Greedily match 3 words, then 2, then 1
            for k in range(min(3, n - i), 0, -1):
                candidate = " ".join(words[i : i + k])
                num = self.parse_single_number(candidate)
                if num is not None:
                    matched = num
                    matched_len = k
                    break
            if matched is not None:
                results.append((matched, i, i + matched_len))
                i += matched_len
            else:
                i += 1
        return results

    def parse(self, text: str) -> MathAST:
        norm_text = self.normalize_text(text)
        
        # Check units (currency)
        is_money = "रुपये" in norm_text or "रुपया" in norm_text or "पैसे" in norm_text
        unit = "CURRENCY_INR" if is_money else "NONE"

        # Check explicit fractions like "पाच छेद सात" (5/7)
        frac_match = re.search(r"(\S+)\s+छेद\s+(\S+)", norm_text)
        if frac_match:
            num_left = self.parse_single_number(frac_match.group(1))
            num_right = self.parse_single_number(frac_match.group(2))
            if num_left and num_right and num_right.value != 0:
                val = num_left.value / num_right.value
                p = ParsedNumber(value=val, raw_str=norm_text, is_fraction=True,
                                 numerator=int(num_left.value), denominator=int(num_right.value))
                return MathAST(op="NUMBER_ONLY", left=p, unit=unit, raw_text=norm_text)

        # Subtraction patterns: "A मधून B वजा" or "B मधून A गेले"
        madhun_match = re.search(r"(.+?)\s+मधून\s+(.+?)\s+(?:वजा|कमी|गेले|काढले)", norm_text)
        if madhun_match:
            left_part = madhun_match.group(1).strip()
            right_part = madhun_match.group(2).strip()
            num_left = self.parse_single_number(left_part)
            num_right = self.parse_single_number(right_part)
            if num_left and num_right:
                return MathAST(op="SUB", left=num_left, right=num_right, unit=unit, raw_text=norm_text)

        # Standard operator detection
        detected_op = None
        op_words = []
        if any(w in norm_text for w in ["अधिक", "आणि", "बेरीज", "जमा", "मिळवले", "+"]):
            detected_op = "ADD"
            op_words = ["अधिक", "आणि", "बेरीज", "जमा", "मिळवले", "+"]
        elif any(w in norm_text for w in ["वजा", "वजाबाकी", "कमी", "गेले", "-"]):
            detected_op = "SUB"
            op_words = ["वजा", "वजाबाकी", "कमी", "गेले", "-"]
        elif any(w in norm_text for w in ["गुणिले", "गुणाकार", "पट", "पाढे", "गुणले", "*", "×"]):
            detected_op = "MUL"
            op_words = ["गुणिले", "गुणाकार", "पट", "पाढे", "गुणले", "*", "×"]
        elif any(w in norm_text for w in ["भागिले", "भागाकार", "वाटले", "/", "÷"]):
            detected_op = "DIV"
            op_words = ["भागिले", "भागाकार", "वाटले", "/", "÷"]

        # Extract all numbers in text
        nums_with_spans = self.extract_numbers_and_spans(norm_text)
        nums = [n[0] for n in nums_with_spans]

        # Case 1: Binary Operation with 2 numbers
        if detected_op and len(nums) >= 2:
            return MathAST(op=detected_op, left=nums[0], right=nums[1], unit=unit, raw_text=norm_text)

        # Case 2: Only 1 number detected
        if len(nums) == 1:
            if detected_op:
                # Ambiguous: e.g. "सात अधिक" (missing right operand)
                question = f"{nums[0].raw_str} मध्ये किती मिळवायचे आहेत?" if detected_op == "ADD" else f"{nums[0].raw_str} मधून किती वजा करायचे आहेत?"
                return MathAST(
                    op=detected_op,
                    left=nums[0],
                    unit=unit,
                    ambiguity=Ambiguity(is_ambiguous=True, missing_operand="right", clarification_question=question),
                    raw_text=norm_text
                )
            else:
                # Isolated number answer: e.g. "१५" or "पंधरा"
                return MathAST(op="NUMBER_ONLY", left=nums[0], unit=unit, raw_text=norm_text)

        # Case 3: Operator detected but no numbers: e.g. "बेरीज कर" or "वजा केले"
        if detected_op and len(nums) == 0:
            return MathAST(
                op=detected_op,
                ambiguity=Ambiguity(is_ambiguous=True, missing_operand="left_and_right", clarification_question="कोणत्या संख्यांची क्रिया करायची आहे?"),
                raw_text=norm_text
            )

        # Case 4: No operators and no numbers
        return MathAST(
            op="UNKNOWN",
            ambiguity=Ambiguity(is_ambiguous=True, missing_operand="all", clarification_question="गणिताचा प्रश्न पुन्हा सांगशील का?"),
            raw_text=norm_text
        )
