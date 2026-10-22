import json
import unittest
from ganit_mitra_desktop.parser import MarathiSpokenMathParser
from ganit_mitra_desktop.math_engine import MathEngine

class TestMarathiGrammarTable(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parser = MarathiSpokenMathParser()
        cls.engine = MathEngine()
        with open("tests/golden/math_grammar_golden.json", "r", encoding="utf-8") as f:
            cls.vectors = json.load(f)

    def test_all_514_golden_vectors(self):
        print(f"\n[Grammar-Test] Running {len(self.vectors)} table-driven Marathi grammar vectors...")
        passed = 0
        for vec in self.vectors:
            inp = vec["input"]
            expected_op = vec["expected_op"]
            ast = self.parser.parse(inp)

            self.assertEqual(ast.op, expected_op, f"OP mismatch for '{inp}': expected {expected_op}, got {ast.op}")
            self.assertEqual(ast.ambiguity.is_ambiguous, vec["is_ambiguous"], f"Ambiguity mismatch for '{inp}'")

            if not vec["is_ambiguous"]:
                if vec["left_val"] is not None:
                    self.assertIsNotNone(ast.left, f"Left operand missing for '{inp}'")
                    self.assertAlmostEqual(ast.left.value, float(vec["left_val"]), delta=0.01, msg=f"Left val mismatch for '{inp}'")
                if vec["right_val"] is not None:
                    self.assertIsNotNone(ast.right, f"Right operand missing for '{inp}'")
                    self.assertAlmostEqual(ast.right.value, float(vec["right_val"]), delta=0.01, msg=f"Right val mismatch for '{inp}'")

                # If binary operation, test MathEngine evaluation
                if expected_op in ("ADD", "SUB", "MUL", "DIV"):
                    sol = self.engine.solve(expected_op, ast.left.value, ast.right.value)
                    self.assertEqual(sol.result_int, vec["expected_ans"], f"Math result mismatch for '{inp}'")

            passed += 1

        print(f"  -> Successfully verified ALL {passed} / {len(self.vectors)} test vectors with ZERO errors!")

if __name__ == '__main__':
    unittest.main()
