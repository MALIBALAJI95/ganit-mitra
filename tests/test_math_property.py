import random
import unittest
from decimal import Decimal
from fractions import Fraction
from ganit_mitra_desktop.math_engine import MathEngine

class TestMathEnginePropertyBased(unittest.TestCase):
    def setUp(self):
        self.engine = MathEngine()

    def test_addition_10k_properties(self):
        print("\n[Property-Test] Running 10,000 random addition cases...")
        for i in range(10000):
            a = random.randint(0, 5000)
            b = random.randint(0, 5000)
            sol = self.engine.solve("ADD", a, b)
            self.assertEqual(sol.result_int, a + b, f"Mismatch in {a} + {b}")
            self.assertEqual(sol.result_val, float(a + b))
            self.assertTrue(len(sol.steps) >= 1)
        print("  -> Passed 10,000 addition cases with ZERO mismatches!")

    def test_subtraction_10k_properties(self):
        print("\n[Property-Test] Running 10,000 random subtraction cases...")
        for i in range(10000):
            a = random.randint(0, 5000)
            b = random.randint(0, 5000)
            sol = self.engine.solve("SUB", a, b)
            self.assertEqual(sol.result_int, a - b, f"Mismatch in {a} - {b}")
            self.assertEqual(sol.result_val, float(a - b))
            self.assertTrue(len(sol.steps) >= 1)
        print("  -> Passed 10,000 subtraction cases with ZERO mismatches!")

    def test_multiplication_10k_properties(self):
        print("\n[Property-Test] Running 10,000 random multiplication cases...")
        for i in range(10000):
            a = random.randint(0, 100)
            b = random.randint(0, 100)
            sol = self.engine.solve("MUL", a, b)
            self.assertEqual(sol.result_int, a * b, f"Mismatch in {a} * {b}")
            self.assertEqual(sol.result_val, float(a * b))
            self.assertTrue(len(sol.steps) >= 1)
        print("  -> Passed 10,000 multiplication cases with ZERO mismatches!")

    def test_division_10k_properties(self):
        print("\n[Property-Test] Running 10,000 random division cases...")
        for i in range(10000):
            a = random.randint(0, 5000)
            b = random.randint(1, 100)  # non-zero
            sol = self.engine.solve("DIV", a, b)
            self.assertEqual(sol.result_int, a // b, f"Mismatch in {a} // {b}")
            self.assertEqual(sol.result_val, float(a // b))
            self.assertTrue(len(sol.steps) >= 1)
            
        # Test zero division error
        with self.assertRaises(ZeroDivisionError):
            self.engine.solve("DIV", 10, 0)
        print("  -> Passed 10,000 division cases with ZERO mismatches!")

    def test_misconception_diagnostics(self):
        print("\n[Property-Test] Verifying Misconception Classification rules...")
        # Forgot carry: 47 + 28 = 75, child gave 65
        d1 = self.engine.diagnose_misconception("ADD", 47, 28, 65)
        self.assertEqual(d1.code, "FORGOT_CARRY")

        # Forgot borrow: 42 - 17 = 25, child gave 35
        d2 = self.engine.diagnose_misconception("SUB", 42, 17, 35)
        self.assertEqual(d2.code, "FORGOT_BORROW")

        # Off by one: 7 + 8 = 15, child gave 16
        d3 = self.engine.diagnose_misconception("ADD", 7, 8, 16)
        self.assertEqual(d3.code, "OFF_BY_ONE")

        # Operation swap: 10 + 5 = 15, child gave 5 (subtracted)
        d4 = self.engine.diagnose_misconception("ADD", 10, 5, 5)
        self.assertEqual(d4.code, "OPERATION_SWAP")

        # Reversed digits: 12 * 4 = 48, child gave 84
        d5 = self.engine.diagnose_misconception("MUL", 12, 4, 84)
        self.assertEqual(d5.code, "REVERSED_DIGITS")
        print("  -> Passed all Misconception Diagnostic rules!")

if __name__ == '__main__':
    unittest.main()
