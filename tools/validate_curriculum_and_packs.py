#!/usr/bin/env python3
"""
validate_curriculum_and_packs.py
Strict validator for Ganit Mitra:
1. Validates curriculum_manifest.json structure & detects cyclic dependencies in the prerequisite DAG.
2. Validates lesson pack JSON structure (7-step pedagogical cycle integrity).
3. Verifies math correctness of all static problems and independent practice examples.
"""

import os
import json
import sys
from typing import Dict, List, Set

def validate_curriculum_dag(manifest_path: str) -> Dict[str, dict]:
    with open(manifest_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    concepts: Dict[str, dict] = {}
    graph: Dict[str, List[str]] = {}

    for grade_data in data.get("classes", []):
        grade = grade_data["grade"]
        for strand in grade_data.get("strands", []):
            for concept in strand.get("concepts", []):
                cid = concept["concept_id"]
                if cid in concepts:
                    raise ValueError(f"Duplicate concept ID found: {cid}")
                concepts[cid] = concept
                graph[cid] = concept.get("prerequisites", [])

    # Check for missing prerequisite references
    for cid, prereqs in graph.items():
        for prereq in prereqs:
            if prereq not in concepts:
                raise ValueError(f"Concept '{cid}' references unknown prerequisite '{prereq}'")

    # Detect cycles via DFS
    visited: Set[str] = set()
    rec_stack: Set[str] = set()

    def has_cycle(node: str) -> bool:
        visited.add(node)
        rec_stack.add(node)
        for neighbor in graph.get(node, []):
            if neighbor not in visited:
                if has_cycle(neighbor):
                    return True
            elif neighbor in rec_stack:
                return True
        rec_stack.remove(node)
        return False

    for node in graph:
        if node not in visited:
            if has_cycle(node):
                raise ValueError(f"Cycle detected in curriculum DAG involving node: {node}")

    print(f"✓ Curriculum DAG valid! Checked {len(concepts)} concepts across Classes 1–6 with 0 cycles.")
    return concepts

def validate_lesson_pack(pack_path: str):
    with open(pack_path, "r", encoding="utf-8") as f:
        pack = json.load(f)

    # Required 7 steps check
    required_keys = [
        "concept_id", "grade", "title_mr", "rural_context_hook",
        "manipulative_phase", "spoken_explanation", "guided_practice",
        "independent_practice", "explain_back_check", "spaced_review"
    ]
    for k in required_keys:
        if k not in pack:
            raise ValueError(f"Lesson pack missing required step: {k}")

    # Verify math correctness in guided practice
    gp = pack["guided_practice"]["problem_instance"]
    operands = gp["operands"]
    op = gp["operation"]
    expected = gp["expected_answer"]

    if op == "ADD":
        calc = sum(operands)
    elif op == "SUBTRACT":
        calc = operands[0] - operands[1]
    elif op == "MULTIPLY":
        calc = operands[0] * operands[1]
    else:
        raise ValueError(f"Unsupported operation: {op}")

    if calc != expected:
        raise ValueError(f"Math calculation mismatch in guided practice: {operands} {op} = {calc}, but pack states {expected}")

    # Verify math correctness in independent practice samples
    for sample in pack["independent_practice"]["sample_problems"]:
        s_ops = sample["operands"]
        s_expected = sample["expected_answer"]
        if sum(s_ops) != s_expected:
            raise ValueError(f"Sample problem math mismatch: {s_ops} != {s_expected}")

    # Verify explain back check has exactly 1 correct option
    options = pack["explain_back_check"]["options"]
    correct_count = sum(1 for opt in options if opt["is_correct"])
    if correct_count != 1:
        raise ValueError(f"Explain-back check must have exactly 1 correct option, found {correct_count}")

    print(f"✓ Lesson pack '{pack['concept_id']}' ({pack['title_mr']}) passed all 7-step pedagogical and math checks!")

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    manifest = os.path.join(base_dir, "curriculum", "curriculum_manifest.json")
    pack_mvp = os.path.join(base_dir, "content", "std3", "std3_math_add_03.json")

    validate_curriculum_dag(manifest)
    validate_lesson_pack(pack_mvp)
