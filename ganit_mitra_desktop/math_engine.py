from dataclasses import dataclass
from typing import List, Optional, Tuple, Dict, Any
from fractions import Fraction
from decimal import Decimal
import math

from benchmarks.verify_marathi_numbers import number_to_marathi

def get_place_value_breakdown_mr(n: int) -> str:
    """Format full Marathi place value breakdown: हजार, शतक, दशक, एकक."""
    if n == 0:
        return "० एकक"
    val = abs(n)
    parts = []
    if val >= 1000:
        th = val // 1000
        parts.append(f"{th} हजार ({th * 1000})")
        val %= 1000
    if val >= 100:
        h = val // 100
        parts.append(f"{h} शतक ({h * 100})")
        val %= 100
    if val >= 10:
        tens = val // 10
        parts.append(f"{tens} दशक ({tens * 10})")
        val %= 10
    if val > 0 or not parts:
        parts.append(f"{val} एकक ({val})")
    return " + ".join(parts)

@dataclass
class ExplanationStep:
    step_num: int
    title_mr: str
    explanation_mr: str
    visual_type: str  # 'PLACE_VALUE' | 'NUMBER_LINE' | 'OBJECT_GROUPS'
    visual_text: str

@dataclass
class MathSolution:
    result_val: float
    result_int: Optional[int]
    result_str_mr: str
    steps: List[ExplanationStep]
    full_speech_mr: str

@dataclass
class Misconception:
    detected: bool
    code: str  # 'CORRECT' | 'FORGOT_CARRY' | 'FORGOT_BORROW' | 'OFF_BY_ONE' | 'OPERATION_SWAP' | 'REVERSED_DIGITS' | 'UNKNOWN_ERROR'
    hint_mr: str

class MathEngine:
    def __init__(self):
        pass

    def solve(self, op: str, left_val: Optional[float] = None, right_val: Optional[float] = None, sub_type: str = "AREA") -> MathSolution:
        if op == "TABLE":
            n = int(left_val) if left_val is not None else 5
            return self._solve_table(n)

        if op == "SHAPE_SQUARE":
            return self._solve_square(left_val, sub_type)

        if op == "SHAPE_RECTANGLE":
            return self._solve_rectangle(left_val, right_val, sub_type)

        if op == "NUMBER_ONLY":
            if left_val is None:
                raise ValueError("left_val required for NUMBER_ONLY")
            int_val = int(left_val) if left_val.is_integer() else None
            mr_word = number_to_marathi(int_val) if int_val is not None and 0 <= int_val <= 10000 else str(left_val)
            pv = get_place_value_breakdown_mr(int_val) if int_val is not None else ""
            step = ExplanationStep(
                step_num=1,
                title_mr="स्थानिक किंमत व वाचन",
                explanation_mr=f"दिलेली संख्या {int_val if int_val is not None else left_val} आहे, म्हणजे '{mr_word}'. स्थानिक किंमत: {pv}",
                visual_type="PLACE_VALUE",
                visual_text=f"[ {int_val if int_val is not None else left_val} ] = {pv}"
            )
            return MathSolution(
                result_val=left_val,
                result_int=int_val,
                result_str_mr=mr_word,
                steps=[step],
                full_speech_mr=f"ही संख्या {mr_word} आहे. यात {pv} आहेत."
            )

        if right_val is None:
            raise ValueError(f"Operation {op} requires both left and right operands")

        if op == "ADD":
            return self._solve_addition(int(left_val), int(right_val))
        elif op == "SUB":
            return self._solve_subtraction(int(left_val), int(right_val))
        elif op == "MUL":
            return self._solve_multiplication(int(left_val), int(right_val))
        elif op == "DIV":
            return self._solve_division(int(left_val), int(right_val))
        else:
            raise ValueError(f"Unknown operation: {op}")

    def _solve_table(self, n: int) -> MathSolution:
        n_mr = number_to_marathi(n) if 0 <= n <= 10000 else str(n)
        suffixes = [
            (1, "एके"), (2, "दुणे"), (3, "त्रिक"), (4, "चोक"), (5, "पाचा"),
            (6, "सक"), (7, "सात्ता"), (8, "अठ्ठे"), (9, "नव्वे"), (10, "दाहे")
        ]
        steps = []
        speech_lines = []
        table_grid = []
        for mult, suf in suffixes:
            ans = n * mult
            ans_mr = number_to_marathi(ans) if 0 <= ans <= 10000 else str(ans)
            line_mr = f"{n_mr} {suf} {ans_mr}"
            speech_lines.append(line_mr)
            table_grid.append(f"{n} × {mult} = {ans} ({line_mr})")
            steps.append(ExplanationStep(
                step_num=mult,
                title_mr=f"{n} × {mult} = {ans}",
                explanation_mr=f"{line_mr} (म्हणजे {n} ची {mult} वेळा बेरीज = {ans})",
                visual_type="TABLE_GRID",
                visual_text=f"{n} × {mult} = {ans}"
            ))

        full_speech = f"हा आहे {n_mr}चा पाढा: " + ", ".join(speech_lines)
        return MathSolution(
            result_val=float(n),
            result_int=n,
            result_str_mr=f"{n_mr}चा पाढा",
            steps=steps,
            full_speech_mr=full_speech
        )

    def _solve_square(self, side: Optional[float], sub_type: str) -> MathSolution:
        steps = []
        is_perimeter = (sub_type == "PERIMETER")
        if side is not None:
            s = float(side)
            s_int = int(s) if s.is_integer() else s
            s_mr = number_to_marathi(s_int) if isinstance(s_int, int) and 0 <= s_int <= 10000 else str(s_int)
            if is_perimeter:
                ans = 4 * s
                ans_int = int(ans) if ans.is_integer() else ans
                ans_mr = number_to_marathi(ans_int) if isinstance(ans_int, int) and 0 <= ans_int <= 10000 else str(ans_int)
                steps.append(ExplanationStep(
                    step_num=1,
                    title_mr="सूत्र (Formula)",
                    explanation_mr="चौरसाच्या चारही बाजू समान असतात. चौरसाची परिमिती = ४ × बाजू.",
                    visual_type="SHAPE_SVG",
                    visual_text=f"चौरस बाजू = {s_int}"
                ))
                steps.append(ExplanationStep(
                    step_num=2,
                    title_mr="किंमत ठेवून सोडवणे",
                    explanation_mr=f"परिमिती = ४ × {s_int} = {ans_int} एकक.",
                    visual_type="SHAPE_SVG",
                    visual_text=f"४ × {s_int} = {ans_int}"
                ))
                speech = f"बाजू {s_mr} असलेल्या चौरसाची परिमिती {ans_mr} ({ans_int}) एकक आहे."
                return MathSolution(result_val=ans, result_int=ans_int if isinstance(ans_int, int) else None,
                                    result_str_mr=f"{ans_mr} एकक", steps=steps, full_speech_mr=speech)
            else:
                ans = s * s
                ans_int = int(ans) if ans.is_integer() else ans
                ans_mr = number_to_marathi(ans_int) if isinstance(ans_int, int) and 0 <= ans_int <= 10000 else str(ans_int)
                steps.append(ExplanationStep(
                    step_num=1,
                    title_mr="सूत्र (Formula)",
                    explanation_mr="चौरसाचे क्षेत्रफळ = बाजू × बाजू (बाजूचा वर्ग).",
                    visual_type="SHAPE_SVG",
                    visual_text=f"चौरस बाजू = {s_int}"
                ))
                steps.append(ExplanationStep(
                    step_num=2,
                    title_mr="किंमत ठेवून सोडवणे",
                    explanation_mr=f"क्षेत्रफळ = {s_int} × {s_int} = {ans_int} चौरस एकक.",
                    visual_type="SHAPE_SVG",
                    visual_text=f"{s_int} × {s_int} = {ans_int}"
                ))
                speech = f"बाजू {s_mr} असलेल्या चौरसाचे क्षेत्रफळ {ans_mr} ({ans_int}) चौरस एकक आहे."
                return MathSolution(result_val=ans, result_int=ans_int if isinstance(ans_int, int) else None,
                                    result_str_mr=f"{ans_mr} चौरस एकक", steps=steps, full_speech_mr=speech)
        else:
            # General formula explanation
            steps.append(ExplanationStep(
                step_num=1,
                title_mr="चौरसाची व्याख्या व सूत्रे",
                explanation_mr="ज्या चौकोनाच्या चारही बाजू समान आणि चारही कोन ९०° असतात, त्याला चौरस म्हणतात.\\n१. क्षेत्रफळ = बाजू × बाजू\\n२. परिमिती = ४ × बाजू.",
                visual_type="SHAPE_SVG",
                visual_text="चौरस: चारही बाजू समान"
            ))
            return MathSolution(result_val=0.0, result_int=None, result_str_mr="चौरसाचे सूत्र",
                                steps=steps, full_speech_mr="चौरसाचे क्षेत्रफळ बाजू गुणिले बाजू असते, आणि परिमिती चार गुणिले बाजू असते.")

    def _solve_rectangle(self, length: Optional[float], width: Optional[float], sub_type: str) -> MathSolution:
        steps = []
        is_perimeter = (sub_type == "PERIMETER")
        if length is not None and width is not None:
            l = float(length)
            w = float(width)
            l_int = int(l) if l.is_integer() else l
            w_int = int(w) if w.is_integer() else w
            l_mr = number_to_marathi(l_int) if isinstance(l_int, int) and 0 <= l_int <= 10000 else str(l_int)
            w_mr = number_to_marathi(w_int) if isinstance(w_int, int) and 0 <= w_int <= 10000 else str(w_int)

            if is_perimeter:
                ans = 2 * (l + w)
                ans_int = int(ans) if ans.is_integer() else ans
                ans_mr = number_to_marathi(ans_int) if isinstance(ans_int, int) and 0 <= ans_int <= 10000 else str(ans_int)
                steps.append(ExplanationStep(
                    step_num=1,
                    title_mr="सूत्र (Formula)",
                    explanation_mr="आयताची समोरासमोरील बाजू समान असते. आयताची परिमिती = २ × (लांबी + रुंदी).",
                    visual_type="SHAPE_SVG",
                    visual_text=f"आयत: लांबी={l_int}, रुंदी={w_int}"
                ))
                steps.append(ExplanationStep(
                    step_num=2,
                    title_mr="किंमत ठेवून सोडवणे",
                    explanation_mr=f"परिमिती = २ × ({l_int} + {w_int}) = २ × {l_int + w_int} = {ans_int} एकक.",
                    visual_type="SHAPE_SVG",
                    visual_text=f"२ × ({l_int} + {w_int}) = {ans_int}"
                ))
                speech = f"लांबी {l_mr} आणि रुंदी {w_mr} असलेल्या आयताची परिमिती {ans_mr} ({ans_int}) एकक आहे."
                return MathSolution(result_val=ans, result_int=ans_int if isinstance(ans_int, int) else None,
                                    result_str_mr=f"{ans_mr} एकक", steps=steps, full_speech_mr=speech)
            else:
                ans = l * w
                ans_int = int(ans) if ans.is_integer() else ans
                ans_mr = number_to_marathi(ans_int) if isinstance(ans_int, int) and 0 <= ans_int <= 10000 else str(ans_int)
                steps.append(ExplanationStep(
                    step_num=1,
                    title_mr="सूत्र (Formula)",
                    explanation_mr="आयताचे क्षेत्रफळ = लांबी × रुंदी.",
                    visual_type="SHAPE_SVG",
                    visual_text=f"आयत: लांबी={l_int}, रुंदी={w_int}"
                ))
                steps.append(ExplanationStep(
                    step_num=2,
                    title_mr="किंमत ठेवून सोडवणे",
                    explanation_mr=f"क्षेत्रफळ = {l_int} × {w_int} = {ans_int} चौरस एकक.",
                    visual_type="SHAPE_SVG",
                    visual_text=f"{l_int} × {w_int} = {ans_int}"
                ))
                speech = f"लांबी {l_mr} आणि रुंदी {w_mr} असलेल्या आयताचे क्षेत्रफळ {ans_mr} ({ans_int}) चौरस एकक आहे."
                return MathSolution(result_val=ans, result_int=ans_int if isinstance(ans_int, int) else None,
                                    result_str_mr=f"{ans_mr} चौरस एकक", steps=steps, full_speech_mr=speech)
        else:
            steps.append(ExplanationStep(
                step_num=1,
                title_mr="आयताची व्याख्या व सूत्रे",
                explanation_mr="ज्या चौकोनाच्या समोरासमोरील बाजू समान आणि चारही कोन काटकोन असतात, त्याला आयत म्हणतात.\\n१. क्षेत्रफळ = लांबी × रुंदी\\n२. परिमिती = २ × (लांबी + रुंदी).",
                visual_type="SHAPE_SVG",
                visual_text="आयत: लांबी व रुंदी"
            ))
            return MathSolution(result_val=0.0, result_int=None, result_str_mr="आयताचे सूत्र",
                                steps=steps, full_speech_mr="आयताचे क्षेत्रफळ लांबी गुणिले रुंदी असते, आणि परिमिती दोन गुणिले लांबी अधिक रुंदी असते.")

    def _solve_addition(self, a: int, b: int) -> MathSolution:
        ans = a + b
        ans_mr = number_to_marathi(ans) if 0 <= ans <= 10000 else str(ans)
        a_mr = number_to_marathi(a) if 0 <= a <= 10000 else str(a)
        b_mr = number_to_marathi(b) if 0 <= b <= 10000 else str(b)

        steps = []
        u_a = a % 10
        u_b = b % 10
        u_sum = u_a + u_b
        carry = u_sum // 10

        # Step 1: Units addition
        step1_txt = f"प्रथम एकक स्थानाची बेरीज करू: {u_a} + {u_b} = {u_sum}."
        if carry > 0:
            step1_txt += f" यात एकक स्थानी {u_sum % 10} राहिले आणि हातचा {carry} आला."
        steps.append(ExplanationStep(
            step_num=1,
            title_mr="एकक स्थानाची बेरीज",
            explanation_mr=step1_txt,
            visual_type="PLACE_VALUE",
            visual_text=f"  एकक: {u_a} + {u_b} = {u_sum}"
        ))

        # Step 2: Tens addition if 2-digit numbers
        if a >= 10 or b >= 10:
            t_a = (a // 10) % 10
            t_b = (b // 10) % 10
            t_sum = t_a + t_b + carry
            step2_txt = f"आता दशक स्थानाची बेरीज करू: {t_a} + {t_b}"
            if carry > 0:
                step2_txt += f" + हातचा {carry} = {t_sum}."
            else:
                step2_txt += f" = {t_sum}."
            steps.append(ExplanationStep(
                step_num=2,
                title_mr="दशक स्थानाची बेरीज",
                explanation_mr=step2_txt,
                visual_type="PLACE_VALUE",
                visual_text=f"  दशक: {t_a} + {t_b} + (हातचा {carry}) = {t_sum}"
            ))

        # Step 3: Final Answer & Place Value
        pv_ans = get_place_value_breakdown_mr(ans)
        steps.append(ExplanationStep(
            step_num=len(steps) + 1,
            title_mr="एकूण उत्तर व स्थानिक किंमत",
            explanation_mr=f"{a} आणि {b} यांची एकूण बेरीज {ans} ({ans_mr}) झाली. स्थानिक किंमत: {pv_ans}.",
            visual_type="NUMBER_LINE",
            visual_text=f"0 ---[{a}]---> {a} ---[+{b}]---> {ans} = {pv_ans}"
        ))

        full_speech = f"{a_mr} अधिक {b_mr} बरोबर {ans_mr}. " + " ".join([s.explanation_mr for s in steps])
        return MathSolution(
            result_val=float(ans),
            result_int=ans,
            result_str_mr=ans_mr,
            steps=steps,
            full_speech_mr=full_speech
        )

    def _solve_subtraction(self, a: int, b: int) -> MathSolution:
        ans = a - b
        ans_mr = number_to_marathi(ans) if 0 <= ans <= 10000 else str(ans)
        a_mr = number_to_marathi(a) if 0 <= a <= 10000 else str(a)
        b_mr = number_to_marathi(b) if 0 <= b <= 10000 else str(b)

        steps = []
        if a < b:
            # Negative result note
            steps.append(ExplanationStep(
                step_num=1,
                title_mr="लहान संख्येतून मोठी संख्या",
                explanation_mr=f"{a} मधून {b} वजा केल्यास उत्तर ऋण {abs(ans)} येते.",
                visual_type="NUMBER_LINE",
                visual_text=f"{ans} <---[-{b}]--- {a}"
            ))
        else:
            u_a = a % 10
            u_b = b % 10
            if u_a < u_b and a >= 10:
                # Borrowing required
                steps.append(ExplanationStep(
                    step_num=1,
                    title_mr="हातचा / उसना घेणे",
                    explanation_mr=f"एकक स्थानी {u_a} मधून {u_b} वजा होत नाहीत. म्हणून दशकातून १ उसना घेतला. एकक झाले {u_a + 10}.",
                    visual_type="PLACE_VALUE",
                    visual_text=f"  एकक: 10 + {u_a} = {u_a + 10} -> {u_a + 10} - {u_b} = {(u_a + 10) - u_b}"
                ))
            else:
                steps.append(ExplanationStep(
                    step_num=1,
                    title_mr="एकक स्थानाची वजाबाकी",
                    explanation_mr=f"एकक स्थानी {u_a} मधून {u_b} वजा केले: {u_a - u_b}.",
                    visual_type="PLACE_VALUE",
                    visual_text=f"  एकक: {u_a} - {u_b} = {u_a - u_b}"
                ))

            steps.append(ExplanationStep(
                step_num=len(steps) + 1,
                title_mr="अंतिम उत्तर",
                explanation_mr=f"{a} मधून {b} वजा केल्यावर {ans} ({ans_mr}) उरतात.",
                visual_type="NUMBER_LINE",
                visual_text=f"0 <---[-{b}]--- {a} (शिल्लक: {ans})"
            ))

        full_speech = f"{a_mr} वजा {b_mr} बरोबर {ans_mr}. " + " ".join([s.explanation_mr for s in steps])
        return MathSolution(
            result_val=float(ans),
            result_int=ans,
            result_str_mr=ans_mr,
            steps=steps,
            full_speech_mr=full_speech
        )

    def _solve_multiplication(self, a: int, b: int) -> MathSolution:
        ans = a * b
        ans_mr = number_to_marathi(ans) if 0 <= ans <= 10000 else str(ans)
        a_mr = number_to_marathi(a) if 0 <= a <= 10000 else str(a)
        b_mr = number_to_marathi(b) if 0 <= b <= 10000 else str(b)

        steps = []
        # Repeated addition concept
        rep_expr = " + ".join([str(a)] * min(b, 5))
        if b > 5:
            rep_expr += f" ... ({b} वेळा)"
        steps.append(ExplanationStep(
            step_num=1,
            title_mr="गुणाकार म्हणजे पुन्हा पुन्हा बेरीज",
            explanation_mr=f"{a} ची {b} वेळा बेरीज करणे म्हणजे {a} × {b}. उदा: {rep_expr} = {ans}.",
            visual_type="OBJECT_GROUPS",
            visual_text=f"  [{b} गट, प्रत्येकी {a} वस्तू] = {ans}"
        ))

        # Step 2: Place Value of Product
        pv_ans = get_place_value_breakdown_mr(ans)
        steps.append(ExplanationStep(
            step_num=2,
            title_mr="स्थानिक किंमत व एकूण उत्तर",
            explanation_mr=f"{a} × {b} चे एकूण उत्तर {ans} ({ans_mr}) आले. स्थानिक किंमत: {pv_ans}.",
            visual_type="PLACE_VALUE",
            visual_text=f"{ans} = {pv_ans}"
        ))

        full_speech = f"{a_mr} गुणिले {b_mr} बरोबर {ans_mr}. यात {pv_ans} आहेत. {steps[0].explanation_mr}"
        return MathSolution(
            result_val=float(ans),
            result_int=ans,
            result_str_mr=ans_mr,
            steps=steps,
            full_speech_mr=full_speech
        )

    def _solve_division(self, a: int, b: int) -> MathSolution:
        if b == 0:
            raise ZeroDivisionError("शून्याने भागता येत नाही (Division by zero)")

        q = a // b
        r = a % b
        q_mr = number_to_marathi(q) if 0 <= q <= 10000 else str(q)
        a_mr = number_to_marathi(a) if 0 <= a <= 10000 else str(a)
        b_mr = number_to_marathi(b) if 0 <= b <= 10000 else str(b)

        steps = []
        if r == 0:
            step_txt = f"{a} वस्तू {b} जणांमध्ये समान वाटल्यास प्रत्येकाला {q} ({q_mr}) मिळतील आणि बाकी शून्य राहील."
        else:
            step_txt = f"{a} ला {b} ने भागल्यास भागाकार {q} येतो आणि बाकी {r} उरते."

        steps.append(ExplanationStep(
            step_num=1,
            title_mr="समान वाटणी (भागाकार)",
            explanation_mr=step_txt,
            visual_type="OBJECT_GROUPS",
            visual_text=f"  {a} ÷ {b} = {q} (बाकी: {r})"
        ))

        full_speech = f"{a_mr} भागिले {b_mr} बरोबर भागाकार {q_mr}. {step_txt}"
        return MathSolution(
            result_val=float(q),
            result_int=q,
            result_str_mr=q_mr,
            steps=steps,
            full_speech_mr=full_speech
        )

    def diagnose_misconception(self, op: str, a: int, b: int, child_ans: int) -> Misconception:
        correct_ans = 0
        if op == "ADD":
            correct_ans = a + b
        elif op == "SUB":
            correct_ans = a - b
        elif op == "MUL":
            correct_ans = a * b
        elif op == "DIV":
            correct_ans = a // b if b != 0 else 0

        if child_ans == correct_ans:
            return Misconception(detected=False, code="CORRECT", hint_mr="छान! अगदी बरोबर उत्तर आहे!")

        # 1. Off by one error
        if abs(child_ans - correct_ans) == 1:
            return Misconception(
                detected=True,
                code="OFF_BY_ONE",
                hint_mr=f"अगदी जवळ पोहोचलास! फक्त एकाने उत्तर चुकले आहे. मोजणी पुन्हा करून बघ."
            )

        # 2. Addition: Forgot carry
        if op == "ADD":
            u_sum = (a % 10) + (b % 10)
            if u_sum >= 10:
                t_sum_no_carry = ((a // 10) % 10) + ((b // 10) % 10)
                ans_no_carry = (t_sum_no_carry * 10) + (u_sum % 10)
                if child_ans == ans_no_carry:
                    return Misconception(
                        detected=True,
                        code="FORGOT_CARRY",
                        hint_mr="लक्ष दे: एकक स्थानाची बेरीज १० पेक्षा जास्त झाल्यावर दशकात हातचा १ मिळवायला विसरलास!"
                    )

        # 3. Subtraction: Subtracted smaller from larger (Forgot borrow)
        if op == "SUB":
            u_a = a % 10
            u_b = b % 10
            if u_a < u_b and a >= 10:
                # E.g. 42 - 17 -> 7 - 2 = 5, 4 - 1 = 3 -> 35
                ans_no_borrow = (((a // 10) - (b // 10)) * 10) + (u_b - u_a)
                if child_ans == ans_no_borrow:
                    return Misconception(
                        detected=True,
                        code="FORGOT_BORROW",
                        hint_mr="लक्षात ठेव: एकक स्थानी लहान संख्येतून मोठी संख्या वजा होत नाही. दशकातून १ उसना घ्यावा लागेल!"
                    )

        # 4. Swapped operation
        if op == "ADD" and child_ans == (a - b):
            return Misconception(detected=True, code="OPERATION_SWAP", hint_mr="तू बेरीज ऐवजी वजाबाकी केली आहेस. अधिक (+) करायचे आहे.")
        if op == "SUB" and child_ans == (a + b):
            return Misconception(detected=True, code="OPERATION_SWAP", hint_mr="तू वजाबाकी ऐवजी बेरीज केली आहेस. वजा (-) करायचे आहे.")
        if op == "MUL" and child_ans == (a + b):
            return Misconception(detected=True, code="OPERATION_SWAP", hint_mr="तू गुणाकार ऐवजी बेरीज केली आहेस. गुणिले (×) करायचे आहे.")

        # 5. Transposition error (reversed digits)
        str_c = str(correct_ans)
        str_child = str(child_ans)
        if len(str_c) == len(str_child) == 2 and str_c[::-1] == str_child:
            return Misconception(
                detected=True,
                code="REVERSED_DIGITS",
                hint_mr=f"तू अंकांचे स्थान उलट लिहिले आहेस का? एकक आणि दशक स्थान तपासून बघ."
            )

        return Misconception(
            detected=True,
            code="UNKNOWN_ERROR",
            hint_mr="पुन्हा एकदा पायरीनुसार विचार कर आणि उत्तर शोध."
        )
