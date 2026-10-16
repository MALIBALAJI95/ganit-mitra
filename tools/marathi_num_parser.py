#!/usr/bin/env python3
"""
marathi_num_parser.py
Deterministic Marathi number words to integer parser.
Converts spoken Marathi number words (० ते १०००) and dialect variants into integers.
Zero-dependency, pure algorithmic implementation.
"""

from typing import Optional, Dict

# Single-digit and 1-99 words in standard Marathi
MARATHI_1_TO_99: Dict[str, int] = {
    "शून्य": 0, "झिरो": 0,
    "एक": 1, "दोन": 2, "दो": 2, "तीन": 3, "चार": 4, "पाच": 5,
    "सहा": 6, "सात": 7, "आठ": 8, "नऊ": 9, "दहा": 10,
    "अकरा": 11, "बारा": 12, "तेरा": 13, "चौदा": 14, "पंधरा": 15,
    "सोळा": 16, "सतरा": 17, "अठरा": 18, "एकोणीस": 19, "वीस": 20,
    "एकवीस": 21, "बावीस": 22, "तेवीस": 23, "चोवीस": 24, "पंचवीस": 25,
    "सव्वीस": 26, "सत्तावीस": 27, "अठ्ठावीस": 28, "एकोणतीस": 29, "तीस": 30,
    "एकतीस": 31, "बत्तीस": 32, "तेहेतीस": 33, "तेतीस": 33, "चौतीस": 34, "पस्तीस": 35,
    "छत्तीस": 36, "सदतीस": 37, "अडतीस": 38, "एकोणचाळीस": 39, "चाळीस": 40,
    "एक्केचाळीस": 41, "एक्केचाळीस": 41, "बेचाळीस": 42, "त्रेचाळीस": 43, "तेहेचाळीस": 43,
    "चव्वेचाळीस": 44, "पंचेचाळीस": 45, "पंचेचाळीस": 45, "शेहेचाळीस": 46, "सत्तेचाळीस": 47,
    "अठ्ठेचाळीस": 48, "एकोणपन्नास": 49, "पन्नास": 50,
    "एक्कावन्न": 51, "बावन्न": 52, "त्रेपन्न": 53, "तेप्पन्न": 53, "चौपन्न": 54, "पंचावन्न": 55,
    "छप्पन्न": 56, "सत्तावन्न": 57, "अठ्ठावन्न": 58, "एकोणसाठ": 59, "साठ": 60,
    "एकसष्ठ": 61, "बासष्ठ": 62, "त्रेसष्ठ": 63, "तेसष्ठ": 63, "चौसष्ठ": 64, "पासष्ठ": 65,
    "सहासष्ठ": 66, "सदुसष्ठ": 67, "सडसष्ठ": 67, "अडुसष्ठ": 68, "अडसष्ठ": 68, "एकोणसत्तर": 69, "सत्तर": 70,
    "एकाहत्तर": 71, "बाहत्तर": 72, "बहात्तर": 72, "त्र्याहत्तर": 73, "चौर्‍याहत्तर": 74, "चौऱ्याहत्तर": 74, "पंच्याहत्तर": 75,
    "शहात्तर": 76, "सत्त्याहत्तर": 77, "अठ्ठ्याहत्तर": 78, "एकोणऐंशी": 79, "ऐंशी": 80,
    "एक्याऐंशी": 81, "ब्याऐंशी": 82, "त्र्याऐंशी": 83, "चौऱ्याऐंशी": 84, "पंच्याऐंशी": 85,
    "शहाऐंशी": 86, "सत्त्याऐंशी": 87, "अठ्ठ्याऐंशी": 88, "एकोणनव्वद": 89, "नव्वद": 90,
    "एक्याण्णव": 91, "ब्याण्णव": 92, "त्र्याण्णव": 93, "चौऱ्याण्णव": 94, "पंच्याण्णव": 95,
    "शहाण्णव": 96, "सत्त्याण्णव": 97, "अठ्ठ्याण्णव": 98, "नव्व्याण्णव": 99, "शंभर": 100
}

# Hundred words
MARATHI_HUNDREDS: Dict[str, int] = {
    "शंभर": 100,
    "एकशे": 100,
    "दोनशे": 200,
    "तीनशे": 300,
    "चारशे": 400,
    "पाचशे": 500,
    "सहाशे": 600,
    "सातशे": 700,
    "आठशे": 800,
    "नऊशे": 900
}

# Special rural / colloquial fractional and compound terms
SPECIAL_COMPOUNDS: Dict[str, int] = {
    "दीडशे": 150,
    "अडीचशे": 250,
    "हजार": 1000,
    "एक हजार": 1000
}

def parse_marathi_number_text(text: str) -> Optional[int]:
    """
    Parse a Marathi spoken number string into an integer.
    Supports single words, compound phrases (उदा. 'दोनशे पस्तीस' -> 235),
    and common dialect spellings.
    """
    cleaned = text.strip()
    if not cleaned:
        return None

    # Direct match in special compounds
    if cleaned in SPECIAL_COMPOUNDS:
        return SPECIAL_COMPOUNDS[cleaned]

    # Direct match in 1-100
    if cleaned in MARATHI_1_TO_99:
        return MARATHI_1_TO_99[cleaned]

    # Direct match in hundreds
    if cleaned in MARATHI_HUNDREDS:
        return MARATHI_HUNDREDS[cleaned]

    # Multi-token matching (e.g. "दोनशे पस्तीस", "एकशे पाच", "तीन शतक")
    tokens = cleaned.split()
    if len(tokens) == 2:
        h_part, rem_part = tokens[0], tokens[1]
        val = 0
        if h_part in MARATHI_HUNDREDS:
            val += MARATHI_HUNDREDS[h_part]
        elif h_part in MARATHI_1_TO_99 and rem_part in ["शतक", "शे"]:
            return MARATHI_1_TO_99[h_part] * 100
        else:
            return None

        if rem_part in MARATHI_1_TO_99:
            val += MARATHI_1_TO_99[rem_part]
            return val
        return None

    if len(tokens) == 3:
        # e.g., "एक हजार पाच" -> 1005, "दोन शतक पाच"
        if tokens[0] == "एक" and tokens[1] == "हजार":
            if tokens[2] in MARATHI_1_TO_99:
                return 1000 + MARATHI_1_TO_99[tokens[2]]
        if tokens[1] == "शतक" and tokens[0] in MARATHI_1_TO_99 and tokens[2] in MARATHI_1_TO_99:
            return (MARATHI_1_TO_99[tokens[0]] * 100) + MARATHI_1_TO_99[tokens[2]]

    return None

if __name__ == "__main__":
    test_cases = [
        ("पाच", 5),
        ("बारा", 12),
        ("पंचवीस", 25),
        ("पंचेचाळीस", 45),
        ("शंभर", 100),
        ("दीडशे", 150),
        ("अडीचशे", 250),
        ("एकशे पाच", 105),
        ("दोनशे पस्तीस", 235),
        ("सातशे चाळीस", 740),
        ("नऊशे नव्व्याण्णव", 999),
        ("हजार", 1000)
    ]
    passed = 0
    for text, expected in test_cases:
        res = parse_marathi_number_text(text)
        assert res == expected, f"Failed for {text}: got {res}, expected {expected}"
        passed += 1
    print(f"All {passed} Marathi number parsing tests passed successfully!")
