import json
import os

from benchmarks.verify_marathi_numbers import MARATHI_NUMS_0_100

def generate_golden():
    vectors = []
    
    # 1. Addition test vectors (100 cases)
    for a in range(1, 11):
        for b in range(1, 11):
            a_w = MARATHI_NUMS_0_100[a]
            b_w = MARATHI_NUMS_0_100[b]
            vectors.append({
                "id": f"add_word_{a}_{b}",
                "input": f"{a_w} अधिक {b_w}",
                "category": "addition",
                "expected_op": "ADD",
                "left_val": a,
                "right_val": b,
                "expected_ans": a + b,
                "is_ambiguous": False
            })
            vectors.append({
                "id": f"add_aani_{a}_{b}",
                "input": f"{a_w} आणि {b_w} किती",
                "category": "addition",
                "expected_op": "ADD",
                "left_val": a,
                "right_val": b,
                "expected_ans": a + b,
                "is_ambiguous": False
            })
            
    # 2. Subtraction test vectors (100 cases)
    for a in range(5, 15):
        for b in range(1, 6):
            a_w = MARATHI_NUMS_0_100[a]
            b_w = MARATHI_NUMS_0_100[b]
            vectors.append({
                "id": f"sub_vaja_{a}_{b}",
                "input": f"{a_w} वजा {b_w}",
                "category": "subtraction",
                "expected_op": "SUB",
                "left_val": a,
                "right_val": b,
                "expected_ans": a - b,
                "is_ambiguous": False
            })
            vectors.append({
                "id": f"sub_madhun_{a}_{b}",
                "input": f"{a_w} मधून {b_w} वजा केले",
                "category": "subtraction",
                "expected_op": "SUB",
                "left_val": a,
                "right_val": b,
                "expected_ans": a - b,
                "is_ambiguous": False
            })

    # 3. Multiplication test vectors (100 cases)
    for a in range(1, 11):
        for b in range(1, 11):
            a_w = MARATHI_NUMS_0_100[a]
            b_w = MARATHI_NUMS_0_100[b]
            vectors.append({
                "id": f"mul_gunile_{a}_{b}",
                "input": f"{a_w} गुणिले {b_w}",
                "category": "multiplication",
                "expected_op": "MUL",
                "left_val": a,
                "right_val": b,
                "expected_ans": a * b,
                "is_ambiguous": False
            })

    # 4. Division test vectors (50 cases)
    for b in range(1, 10):
        for q in range(1, 6):
            a = b * q
            a_w = MARATHI_NUMS_0_100[a]
            b_w = MARATHI_NUMS_0_100[b]
            vectors.append({
                "id": f"div_bhagile_{a}_{b}",
                "input": f"{a_w} भागिले {b_w}",
                "category": "division",
                "expected_op": "DIV",
                "left_val": a,
                "right_val": b,
                "expected_ans": q,
                "is_ambiguous": False
            })

    # 5. Digits (Devanagari & Western) (50 cases)
    deva_digits = ["०", "१", "२", "३", "४", "५", "६", "७", "८", "९"]
    for i in range(1, 26):
        d_str = "".join([deva_digits[int(c)] for c in str(i)])
        vectors.append({
            "id": f"deva_digit_{i}",
            "input": f"{d_str} अधिक ५",
            "category": "digits_deva",
            "expected_op": "ADD",
            "left_val": i,
            "right_val": 5,
            "expected_ans": i + 5,
            "is_ambiguous": False
        })
        vectors.append({
            "id": f"western_digit_{i}",
            "input": f"{i} + 5",
            "category": "digits_western",
            "expected_op": "ADD",
            "left_val": i,
            "right_val": 5,
            "expected_ans": i + 5,
            "is_ambiguous": False
        })

    # 6. Fractions & Money (50 cases)
    fractions = [("अर्धा", 0.5), ("पाव", 0.25), ("पाऊण", 0.75), ("सव्वा", 1.25), ("दीड", 1.5), ("अडीच", 2.5), ("दीडशे", 150), ("अडीचशे", 250)]
    for word, val in fractions:
        vectors.append({
            "id": f"frac_{word}",
            "input": word,
            "category": "fraction",
            "expected_op": "NUMBER_ONLY",
            "left_val": val,
            "right_val": None,
            "expected_ans": val,
            "is_ambiguous": False
        })

    for m in [10, 20, 50, 100, 500]:
        m_w = MARATHI_NUMS_0_100[m] if m in MARATHI_NUMS_0_100 else str(m)
        vectors.append({
            "id": f"money_{m}",
            "input": f"{m_w} रुपये अधिक ५ रुपये",
            "category": "money",
            "expected_op": "ADD",
            "left_val": m,
            "right_val": 5,
            "expected_ans": m + 5,
            "is_ambiguous": False
        })

    # 7. Ambiguous cases (20 cases)
    ambig_inputs = [
        ("सात अधिक", "ADD", "right"),
        ("पाच वजा", "SUB", "right"),
        ("दहा गुणिले", "MUL", "right"),
        ("वीस भागिले", "DIV", "right"),
        ("बेरीज करा", "ADD", "left_and_right"),
        ("वजाबाकी करा", "SUB", "left_and_right")
    ]
    for inp, op, miss in ambig_inputs:
        vectors.append({
            "id": f"ambig_{inp}",
            "input": inp,
            "category": "ambiguous",
            "expected_op": op,
            "left_val": None,
            "right_val": None,
            "expected_ans": None,
            "is_ambiguous": True
        })

    os.makedirs("tests/golden", exist_ok=True)
    out_path = "tests/golden/math_grammar_golden.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(vectors, f, indent=2, ensure_ascii=False)
        
    print(f"Generated {len(vectors)} golden test vectors saved to {out_path}!")

if __name__ == '__main__':
    generate_golden()
