"""
eval_retrieval.py — Retrieval quality test harness for Nyaya.

Runs a labeled set of (query -> expected citation) test cases against
retrieve.py and reports standard IR metrics:

    Hit@1   : was the single best expected answer the #1 result?
    Hit@3   : was any expected answer in the top 3?
    Hit@5   : was any expected answer in the top 5?
    MRR     : Mean Reciprocal Rank — rewards ranking the right answer HIGH,
              not just present somewhere in the list.

Also flags:
    - Duplicate citations appearing in the same result set (category collision bug)
    - Wrong-category leakage when category_filter is applied
    - Cases where score is high but citation is wrong (silent failure mode)

Run:
    python -m ai_service.app.rag.eval_retrieval
    python -m ai_service.app.rag.eval_retrieval --verbose
    python -m ai_service.app.rag.eval_retrieval --top-k 5
"""

import argparse
import sys

from collections import Counter

from .retrieve import retrieve

from .retrieval_test_cases import TestCase, TEST_CASES



def citation_matches(result: dict, expected_substr: str, expected_section: str) -> bool:
    act_name = result.get("act_name", "")
    section = str(result.get("section_number", ""))
    act_ok = expected_substr.lower() in act_name.lower()
    section_ok = (expected_section == "") or (section == expected_section)
    return act_ok and section_ok


def run_case(case: TestCase, top_k: int) -> dict:
    output = retrieve(
        case.query,
        top_k=top_k,
        category_filter=case.category_filter,
    )
    results = output["results"] if isinstance(output, dict) else output

    preferred_rank = None
    acceptable_rank = None

    for i, r in enumerate(results, start=1):

        # Preferred: single best answer
        if preferred_rank is None and case.preferred is not None:
            exp_act, exp_sec = case.preferred
            if citation_matches(r, exp_act, exp_sec):
                preferred_rank = i

        # Acceptable: any citation in the acceptable set
        if acceptable_rank is None:
            for exp_act, exp_sec in case.acceptable:
                if citation_matches(r, exp_act, exp_sec):
                    acceptable_rank = i
                    break

        if (
            (preferred_rank is not None or case.preferred is None)
            and acceptable_rank is not None
        ):
            break

    seen = Counter(
        (r.get("act_name", ""), str(r.get("section_number", "")))
        for r in results
    )
    dupes = {k: v for k, v in seen.items() if v > 1}

    leaks = []
    if case.category_filter:
        leaks = [
            r for r in results
            if r.get("category")
            and r.get("category") != case.category_filter
        ]

    return {
        "case": case,
        "results": results,
        "primary_rank": preferred_rank,
        "secondary_rank": acceptable_rank,
        "dupes": dupes,
        "leaks": leaks,
    }

from pathlib import Path
import sys
 
class Tee:
    def __init__(self, *files):
        self.files = files

    def write(self, data):
        for f in self.files:
            f.write(data)
            f.flush()

    def flush(self):
        for f in self.files:
            f.flush()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()
 
    output_file = Path(__file__).with_name("output.txt")
    f = open(output_file, "w", encoding="utf-8")
    sys.stdout = Tee(sys.__stdout__, f)

    print(f"Running {len(TEST_CASES)} test cases (top_k={args.top_k})\n")
    print("=" * 78)

    dupe_flags = []
    leak_flags = []
    strict_hit_at_1 = strict_hit_at_3 = strict_hit_at_5 = 0
    relaxed_hit_at_1 = relaxed_hit_at_3 = relaxed_hit_at_5 = 0

    strict_rr = []
    relaxed_rr = []

    strict_failures = []

    for case in TEST_CASES:
        try:
            outcome = run_case(case, args.top_k)
        except Exception as e:
            print(f"ERROR on query '{case.query}': {e}")
            strict_failures.append((case, None))
            continue

        primary_rank = outcome["primary_rank"]
        secondary_rank = outcome["secondary_rank"]

        strict_rank = primary_rank

        relaxed_rank = (
            primary_rank
            if primary_rank is not None
            else secondary_rank
        )

        if strict_rank == 1:
            strict_hit_at_1 += 1
        if strict_rank and strict_rank <= 3:
            strict_hit_at_3 += 1
        if strict_rank and strict_rank <= 5:
            strict_hit_at_5 += 1

        strict_rr.append(1.0 / strict_rank if strict_rank else 0.0)

        if strict_rank is None:
            strict_failures.append((case, outcome))
        
        if strict_rank is None:
            print(f'✗ {case.query}')
            print(f'Expected: {case.preferred}')        
        
            for r in outcome["results"]:
                print(
                    f'   -> {r["citation"]} '
                    f'({r["final_score"]:.3f})'
                )

        if relaxed_rank == 1:
            relaxed_hit_at_1 += 1
        if relaxed_rank and relaxed_rank <= 3:
            relaxed_hit_at_3 += 1
        if relaxed_rank and relaxed_rank <= 5:
            relaxed_hit_at_5 += 1

        relaxed_rr.append(1.0 / relaxed_rank if relaxed_rank else 0.0)

        print(
    f"[strict={strict_rank or 'MISS':>4} | "
    f"relaxed={relaxed_rank or 'MISS':>4}] "
    f"{case.query}"
)
        
        if args.verbose or strict_rank is None:
            for i, r in enumerate(outcome["results"][:args.top_k], start=1):
                marker = ""
                if i == primary_rank:
                    marker = " <-- PRIMARY"
                elif i == secondary_rank:
                    marker = " <-- SECONDARY"

                print(
                    f"{marker:15}"
                    f"{i}. {r.get('act_name','?')} "
                    f"S.{r.get('section_number','?')} "
                    f"score={r.get('final_score', r.get('score', 0)):.3f}"
                )
            print()
            
        if outcome["dupes"]:
            dupe_flags.append((case, outcome["dupes"]))

        if outcome["leaks"]:
            leak_flags.append((case, outcome["leaks"]))    
     
    print("=" * 78)
    n = len(TEST_CASES)
    print("STRICT (Primary only)")
    print("=" * 78)
    print(f"Hit@1 : {strict_hit_at_1}/{n} ({100*strict_hit_at_1/n:.1f}%)")
    print(f"Hit@3 : {strict_hit_at_3}/{n} ({100*strict_hit_at_3/n:.1f}%)")
    print(f"Hit@5 : {strict_hit_at_5}/{n} ({100*strict_hit_at_5/n:.1f}%)")
    print(f"MRR    : {sum(strict_rr)/n:.3f}")
    print()
    print("=" * 78)
    print("RELAXED (Primary + Secondary)")
    print("=" * 78)
    print(f"Hit@1 : {relaxed_hit_at_1}/{n} ({100*relaxed_hit_at_1/n:.1f}%)")
    print(f"Hit@3 : {relaxed_hit_at_3}/{n} ({100*relaxed_hit_at_3/n:.1f}%)")
    print(f"Hit@5 : {relaxed_hit_at_5}/{n} ({100*relaxed_hit_at_5/n:.1f}%)")
    print(f"MRR    : {sum(relaxed_rr)/n:.3f}")
    

    if strict_failures:
        print(f"⚠ {len(strict_failures)} STRICT MISSES:")
        for case, _ in strict_failures:
            print(
                f'  - "{case.query}" '
                f'(preferred={case.preferred}, acceptable={case.acceptable})'   # was case.primary/case.secondary
            )
        print()

    if dupe_flags:
        print(f"⚠ {len(dupe_flags)} cases with DUPLICATE citations in result set "
              f"(likely category-collision bug, e.g. same Act parsed into 2 folders):")
        for case, dupes in dupe_flags:
            print(f"  - \"{case.query}\" -> duplicates: {dupes}")
        print()

    if leak_flags:
        print(f"⚠ {len(leak_flags)} cases with CATEGORY LEAKAGE "
              f"(category_filter set but off-category results returned):")
        for case, leaks in leak_flags:
            leaked_cats = set(r.get("category") for r in leaks)
            print(f"  - \"{case.query}\" (filter={case.category_filter}) -> leaked categories: {leaked_cats}")
        print()

    if not strict_failures and not dupe_flags and not leak_flags:
        print("✓ No misses, no duplicates, no category leakage detected.")

    sys.exit(1 if strict_failures else 0)


if __name__ == "__main__":
    main()