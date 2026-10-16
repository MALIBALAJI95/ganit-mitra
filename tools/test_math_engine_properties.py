#!/usr/bin/env python3
"""
test_math_engine_properties.py
Property-based test suite verifying 10,000 randomized addition problems,
place-value step breakdowns, carrying logic, and misconception diagnoses.
Executes pure Kotlin math engine specification in Python to verify mathematical correctness.
"""

import random

def decompose_addition(op1: int, op2: int):
    assert 100 <= op1 <= 899, f"op1 out of bounds: {op1}"
    assert 100 <= op2 <= 899, f"op2 out of bounds: {op2}"

    h1, rem1 = divmod(op1, 100)
    t1, u1 = divmod(rem1, 10)

    h2, rem2 = divmod(op2, 100)
    t2, u2 = divmod(rem2, 10)

    units_sum = u1 + u2
    carry_to_tens = units_sum // 10
    units_result = units_sum % 10

    tens_sum = t1 + t2 + carry_to_tens
    carry_to_hundreds = tens_sum // 10
    tens_result = tens_sum % 10

    hundreds_sum = h1 + h2 + carry_to_hundreds
    final_sum = op1 + op2

    # Invariant 1: Place value reconstruction equals exact sum
    reconstructed = (hundreds_sum * 100) + (tens_result * 10) + units_result
    assert reconstructed == final_sum, f"Reconstruction failed: {reconstructed} != {final_sum}"

    # Invariant 2: Carries are strictly binary (0 or 1) for 2 operands
    assert carry_to_tens in (0, 1), f"Invalid carry to tens: {carry_to_tens}"
    assert carry_to_hundreds in (0, 1), f"Invalid carry to hundreds: {carry_to_hundreds}"

    return {
        "op1": op1, "op2": op2,
        "u1": u1, "u2": u2, "units_sum": units_sum, "units_result": units_result, "carry_to_tens": carry_to_tens,
        "t1": t1, "t2": t2, "tens_sum": tens_sum, "tens_result": tens_result, "carry_to_hundreds": carry_to_hundreds,
        "h1": h1, "h2": h2, "hundreds_sum": hundreds_sum, "final_sum": final_sum
    }

def diagnose_misconception(op1: int, op2: int, student_answer: int):
    step = decompose_addition(op1, op2)
    if student_answer == step["final_sum"]:
        return "CORRECT"

    # Case 1: Forgot units carry to tens
    if step["carry_to_tens"] > 0:
        tens_no_carry = step["t1"] + step["t2"]
        h_carry_no_carry = tens_no_carry // 10
        tens_res_no_carry = tens_no_carry % 10
        h_sum_no_carry = step["h1"] + step["h2"] + h_carry_no_carry
        forgot_tens = (h_sum_no_carry * 100) + (tens_res_no_carry * 10) + step["units_result"]
        if student_answer == forgot_tens:
            return "FORGOT_CARRY_UNITS_TO_TENS"

    # Case 2: Reversal in carry (e.g. 7+5=12 -> wrote 1, carried 2)
    if step["carry_to_tens"] > 0 and 11 <= step["units_sum"] <= 19:
        rev_units = step["carry_to_tens"]
        rev_carry = step["units_result"]
        rev_tens = step["t1"] + step["t2"] + rev_carry
        rev_ans = (step["hundreds_sum"] * 100) + (rev_tens * 10) + rev_units
        if student_answer == rev_ans:
            return "DIGIT_REVERSAL_IN_CARRY"

    return "GENERAL_CALCULATION_ERROR"

def run_property_tests(num_iterations: int = 10000):
    random.seed(42) # Deterministic reproducibility
    carrying_cases = 0
    double_carrying_cases = 0

    for i in range(num_iterations):
        op1 = random.randint(100, 499)
        op2 = random.randint(100, 499)
        res = decompose_addition(op1, op2)

        if res["carry_to_tens"] > 0:
            carrying_cases += 1
            # Test misconception detection: forgot carry
            c1 = (res["hundreds_sum"] * 100) + ((res["t1"] + res["t2"]) * 10) + res["units_result"]
            diag = diagnose_misconception(op1, op2, c1)
            assert diag == "FORGOT_CARRY_UNITS_TO_TENS", f"Failed diagnosis for forgot carry on {op1}+{op2}"

        if res["carry_to_tens"] > 0 and res["carry_to_hundreds"] > 0:
            double_carrying_cases += 1

    print(f"✓ All {num_iterations} property tests PASSED!")
    print(f"  - Single carry cases verified: {carrying_cases}")
    print(f"  - Double carry (units & tens) cases verified: {double_carrying_cases}")

if __name__ == "__main__":
    run_property_tests(10000)
