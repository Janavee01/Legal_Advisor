"""
validate_testcases.py — Sanity-checks eval.py's TEST_CASES against the actual
parsed corpus JSON files, BEFORE you trust any retrieval metric.

Catches:
  1. Section numbers in `preferred`/`acceptable` that don't exist in the
     corpus at all (silent, permanent misses — no retrieval fix can save these).
  2. Act-name strings that wouldn't match ANY act_name in the corpus even
     via substring match (i.e. citation_matches() would always be False),
     e.g. using "BNSS" as a short code when the real act_name is
     "Bharatiya Nagarik Suraksha Sanhita 2023" and "BNSS" is not a substring of it.
  3. Act-name strings that are ambiguous — i.e. they substring-match MORE
     THAN ONE act in the corpus (citation_matches() could silently match the
     wrong Act).
  4. Duplicate test case ids.
  5. (Optional/heuristic) Section title vs. query keyword sanity check --
     flags cases where none of the query's significant words appear in the
     matched section's title, as a "worth eyeballing" signal (NOT proof of
     an error, just a nudge to look closer, since many queries won't share
     literal vocabulary with the statute).

Usage:
    python validate_testcases.py --corpus-dir /path/to/parsed_json_root

The corpus dir is scanned recursively for *.json files, each expected to be
a list of section objects with at least:
    act_name, section_number, section_title

Run this from the same directory as eval.py, or point --eval-module at it.
"""

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from collections import defaultdict


def load_corpus(corpus_dir: Path):
    """
    Returns:
        act_sections: dict[act_name -> set(section_number as str)]
        act_titles:   dict[(act_name, section_number) -> section_title]
    """
    act_sections = defaultdict(set)
    act_titles = {}

    json_files = list(corpus_dir.rglob("*.json"))
    if not json_files:
        print(f"⚠ No JSON files found under {corpus_dir}")
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
            section_title = entry.get("section_title", "")
            if not act_name or not section_number:
                continue
            act_sections[act_name].add(section_number)
            act_titles[(act_name, section_number)] = section_title

    return act_sections, act_titles


def load_test_cases(testcase_module_path: Path):
    spec = importlib.util.spec_from_file_location(
        "retrieval_test_cases",
        testcase_module_path,
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.TEST_CASES


def find_matching_acts(expected_substr: str, act_sections: dict) -> list[str]:
    """Mimics citation_matches()'s substring logic against all known act_names."""
    exp = expected_substr.lower()
    return [a for a in act_sections if exp in a.lower()]


def significant_words(query: str) -> set[str]:
    STOPWORDS = {
        "the", "a", "an", "is", "am", "are", "was", "were", "be", "been",
        "to", "of", "in", "on", "for", "or", "and", "my", "me", "i", "what",
        "can", "do", "does", "did", "how", "if", "without", "with", "at",
        "by", "from", "this", "that", "it", "its", "not", "no", "any",
        "case", "legal", "action", "take", "happens", "who", "when",
    }
    return {w.strip(".,?!") for w in query.lower().split() if w.strip(".,?!") not in STOPWORDS and len(w) > 2}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus-dir", required=True, type=Path,
                         help="Root dir containing parsed *.json Act files (searched recursively).")
    parser.add_argument("--eval-module", default="eval.py", type=Path,
                         help="Path to eval.py containing TEST_CASES.")
    parser.add_argument("--show-title-mismatches", action="store_true",
                         help="Also print the heuristic keyword/title sanity check (noisy, opt-in).")
    parser.add_argument(
    "--testcase-module",
    default="ai_service/app/rag/retrieval_test_cases.py",
    type=Path,
    help="Path to retrieval_test_cases.py containing TEST_CASES.",
)
    args = parser.parse_args()

    act_sections, act_titles = load_corpus(args.corpus_dir)
    print(f"Loaded {len(act_sections)} acts, "
          f"{sum(len(v) for v in act_sections.values())} sections total.\n")

    test_cases = load_test_cases(args.testcase_module)
    print(f"Loaded {len(test_cases)} test cases from {args.eval_module}\n")

    errors = []       # hard problems: will always fail regardless of retrieval quality
    warnings = []      # ambiguous act-name matches
    title_flags = []   # heuristic nudges, not proof of error

    seen_ids = set()

    for case in test_cases:
        # 1. Duplicate ids
        if case.id in seen_ids:
            errors.append(f'[{case.id}] DUPLICATE test case id')
        seen_ids.add(case.id)

        all_citations = list(case.acceptable)
        if case.preferred and case.preferred not in all_citations:
            all_citations.append(case.preferred)

        for act_str, section in all_citations:
            matches = find_matching_acts(act_str, act_sections)

            if len(matches) == 0:
                errors.append(
                    f'[{case.id}] Act string "{act_str}" does not substring-match '
                    f'ANY act_name in corpus. citation_matches() will ALWAYS be False '
                    f'for this entry -> permanent miss regardless of retrieval quality.'
                )
                continue

            if len(matches) > 1:
                warnings.append(
                    f'[{case.id}] Act string "{act_str}" matches MULTIPLE acts: {matches}. '
                    f'citation_matches() may silently accept a hit from the WRONG act.'
                )

            # Check section exists in at least one matching act
            section_found_in = [a for a in matches if section in act_sections[a]]
            if not section_found_in:
                errors.append(
                    f'[{case.id}] Section "{section}" NOT FOUND in corpus for act(s) '
                    f'matching "{act_str}" ({matches}). This citation can never be retrieved '
                    f'-> permanent miss.'
                )
            elif args.show_title_mismatches:
                # heuristic keyword overlap check
                act = section_found_in[0]
                title = act_titles.get((act, section), "")
                q_words = significant_words(case.query)
                t_words = significant_words(title)
                if q_words and not (q_words & t_words):
                    title_flags.append(
                        f'[{case.id}] Query: "{case.query}"\n'
                        f'    -> {act} S.{section}: "{title}"\n'
                        f'    (no shared keywords -- verify manually, may still be correct)'
                    )

    print("=" * 78)
    print(f"HARD ERRORS ({len(errors)}) -- these WILL always fail retrieval eval:")
    print("=" * 78)
    for e in errors:
        print(f"✗ {e}")
    print()

    print("=" * 78)
    print(f"WARNINGS ({len(warnings)}) -- ambiguous act-name matching:")
    print("=" * 78)
    for w in warnings:
        print(f"⚠ {w}")
    print()

    if args.show_title_mismatches:
        print("=" * 78)
        print(f"TITLE/KEYWORD SANITY FLAGS ({len(title_flags)}) -- eyeball these, not necessarily wrong:")
        print("=" * 78)
        for t in title_flags:
            print(f"? {t}\n")

    print("=" * 78)
    print("SUMMARY")
    print("=" * 78)
    print(f"Test cases checked : {len(test_cases)}")
    print(f"Hard errors        : {len(errors)}")
    print(f"Warnings           : {len(warnings)}")
    if args.show_title_mismatches:
        print(f"Title flags        : {len(title_flags)}")

    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()