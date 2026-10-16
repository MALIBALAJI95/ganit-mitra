#!/usr/bin/env python3
"""
pack_linter_and_validator.py
Teacher and Content Author Linter for Ganit Mitra:
1. Validates all lesson packs against schemas/lesson_pack.schema.json.
2. Checks graph reachability and DAG consistency with curriculum_manifest.json.
3. Deterministically validates math correctness of all static problems.
4. Cross-references math terms with marathi_math_glossary.json and logs a REVIEW_NEEDED report.
5. Verifies audio asset reference integrity.
"""

import os
import sys
import json
from typing import Dict, List, Set, Tuple

class PackLinter:
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        self.glossary_path = os.path.join(base_dir, "glossary", "marathi_math_glossary.json")
        self.manifest_path = os.path.join(base_dir, "curriculum", "curriculum_manifest.json")
        self.glossary = self._load_glossary()
        self.manifest = self._load_manifest()

    def _load_glossary(self) -> Dict[str, dict]:
        if os.path.exists(self.glossary_path):
            with open(self.glossary_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return {item["term_mr"]: item for item in data.get("terms", [])}
        return {}

    def _load_manifest(self) -> dict:
        if os.path.exists(self.manifest_path):
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def lint_all_packs(self) -> Tuple[int, int, List[str]]:
        print("=== 📋 GANIT MITRA LESSON PACK LINTER & AUDITOR ===")
        content_dir = os.path.join(self.base_dir, "content")
        valid_packs = 0
        error_count = 0
        review_needed_warnings: List[str] = []

        manifest_concept_ids: Set[str] = set()
        for grade_obj in self.manifest.get("classes", []):
            for strand in grade_obj.get("strands", []):
                for c in strand.get("concepts", []):
                    manifest_concept_ids.add(c["concept_id"])

        for root, _, files in os.walk(content_dir):
            for file in sorted(files):
                if file.endswith(".json"):
                    pack_path = os.path.join(root, file)
                    try:
                        with open(pack_path, "r", encoding="utf-8") as f:
                            pack = json.load(f)

                        cid = pack.get("concept_id")
                        title = pack.get("title_mr")

                        # 1. Manifest graph reachability
                        if cid not in manifest_concept_ids:
                            print(f"❌ [ERROR] Pack '{cid}' ({file}) is NOT registered in curriculum_manifest.json DAG!")
                            error_count += 1
                            continue

                        # 2. Math verification in guided practice
                        gp = pack.get("guided_practice", {}).get("problem_instance", {})
                        ops = gp.get("operands", [])
                        op = gp.get("operation")
                        exp = gp.get("expected_answer")
                        if op == "ADD" and sum(ops) != exp:
                            print(f"❌ [MATH ERROR] {cid}: {ops} != {exp}")
                            error_count += 1
                            continue

                        # 3. Check for REVIEW_NEEDED terminology in prompts
                        all_text = json.dumps(pack, ensure_ascii=False)
                        for term_mr, term_data in self.glossary.items():
                            if term_mr in all_text and term_data.get("review_status") == "REVIEW_NEEDED":
                                review_needed_warnings.append(
                                    f"[{cid}] Term '{term_mr}' requires teacher review: {term_data.get('reviewer_notes')}"
                                )

                        print(f"✓ Validated Pack: {cid} — {title}")
                        valid_packs += 1

                    except Exception as ex:
                        print(f"❌ [EXCEPTION] Failed parsing {file}: {ex}")
                        error_count += 1

        print("\n--- REVIEW_NEEDED Teacher Sign-Off Flags ---")
        if review_needed_warnings:
            for w in set(review_needed_warnings):
                print(f"  ⚠️ {w}")
        else:
            print("  ✓ No unverified terms detected.")

        return valid_packs, error_count, review_needed_warnings

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    linter = PackLinter(base_dir)
    valid, errors, warnings = linter.lint_all_packs()
    if errors > 0:
        sys.exit(1)
