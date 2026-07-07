"""
inspect_testcase_sections.py

For every TestCase in ai_service/app/rag/retrieval_test_cases.py:
    - Takes the act_name from `preferred` and from each entry in `acceptable`.
    - Searches every parsed JSON under datasets/parsed/**/*.json for a
      section matching that act_name + section_number.
    - Prints the full section block for each one.

Usage:
    python inspect_testcase_sections.py
    python inspect_testcase_sections.py --only PA_004 BNSS_001
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # adjust if needed

from .retrieval_test_cases import TEST_CASES  

DEFAULT_PARSED_DIR = Path(__file__).resolve().parents[3] / "datasets" / "parsed"

def build_section_index(parsed_dir: Path):
    index = {}       # (act_name, section_number) -> section dict
    act_names = set()

    json_files = list(parsed_dir.rglob("*.json"))
    if not json_files:
        print(f"⚠ No JSON files found under {parsed_dir}")
        sys.exit(1)

    for jf in json_files:
        try:
            data = json.loads(jf.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"⚠ Could not parse {jf}: {e}")
            continue
        if not isinstance(data, list):
            continue
        for entry in data:
            act_name = entry.get("act_name")
            section_number = str(entry.get("section_number", ""))
            if not act_name or not section_number:
                continue
            index[(act_name, section_number)] = entry
            act_names.add(act_name)

    return index, sorted(act_names)


def find_section_block(act_str: str, section_number: str, index: dict, act_names: list[str]):
    matches = [a for a in act_names if act_str.lower() in a.lower()]
    for act in matches:
        block = index.get((act, str(section_number)))
        if block:
            return block, matches
    return None, matches


def print_section_block(label: str, act_str: str, section_number: str, index: dict, act_names: list[str]):
    block, matches = find_section_block(act_str, section_number, index, act_names)
    print(f"  [{label}] {act_str} § {section_number}")

    if block is None:
        if not matches:
            print(f"      ✗ NOT FOUND -- '{act_str}' doesn't match any act_name in corpus.")
        else:
            print(f"      ✗ NOT FOUND -- act matched ({matches}) but section '{section_number}' doesn't exist.")
        print()
        return

    print(f"      Act        : {block.get('act_name')}")
    print(f"      Chapter    : {block.get('chapter')}")
    print(f"      Section #  : {block.get('section_number')}")
    print(f"      Title      : {block.get('section_title')}")
    print(f"      Citation   : {block.get('citation')}")
    print(f"      ---- TEXT ----")
    print(f"      {block.get('text', '').strip()}")
    print(f"      --------------\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", nargs="*", default=None)
    parser.add_argument("--parsed-dir", type=Path, default=DEFAULT_PARSED_DIR)
    args = parser.parse_args()

    index, act_names = build_section_index(args.parsed_dir)
    print(f"Indexed {len(act_names)} acts, {len(index)} sections total.\n")

    cases = TEST_CASES
    if args.only:
        cases = [c for c in cases if c.id in args.only]

    for case in cases:
        print("=" * 90)
        print(f"[{case.id}]")
        print(f"  Query : {case.query}")
        if case.notes:
            print(f"  Notes : {case.notes}")
        print()

        if case.preferred:
            act_str, sec = case.preferred
            print_section_block("PREFERRED", act_str, sec, index, act_names)

        for i, (act_str, sec) in enumerate(case.acceptable):
            print_section_block(f"ACCEPTABLE[{i}]", act_str, sec, index, act_names)


if __name__ == "__main__":
    main()