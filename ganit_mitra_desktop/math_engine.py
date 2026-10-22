from dataclasses import dataclass
from typing import List, Optional, Tuple, Dict, Any
from fractions import Fraction
from decimal import Decimal
import math

from benchmarks.verify_marathi_numbers import number_to_marathi

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

    def solve(self, op: str, left_val: float, right_val: Optional[float] = None) -> MathSolution:
        if op == "NUMBER_ONLY":
            int_val = int(left_val) if left_val.is_integer() else None
            mr_word = number_to_marathi(int_val) if int_val is not None and 0 <= int_val <= 10000 else str(left_val)
            step = ExplanationStep(
                step_num=1,
                title_mr="संख्या वाचन",
                explanation_mr=f"दिलेली संख्या {int_val if int_val is not None else left_val} आहे, म्हणजे '{mr_word}'.",
                visual_type="PLACE_VALUE",
                visual_text=f"[ {int_val if int_val is not None else left_val} ]"
            )
            return MathSolution(
                result_val=left_val,
                result_int=int_val,
                result_str_mr=mr_word,
                steps=[step],
                full_speech_mr=f"ही संख्या {mr_word} आहे."
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

        # Step 3: Final Answer
        steps.append(ExplanationStep(
            step_num=len(steps) + 1,
            title_mr="एकूण उत्तर",
            explanation_mr=f"{a} आणि {b} यांची एकूण बेरीज {ans} ({ans_mr}) झाली.",
            visual_type="NUMBER_LINE",
            visual_text=f"0 ---[{a}]---> {a} ---[+{b}]---> {ans}"
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

        full_speech = f"{a_mr} गुणिले {b_mr} बरोबर {ans_mr}. {steps[0].explanation_mr}"
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
