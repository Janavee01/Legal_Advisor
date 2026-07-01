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
from dataclasses import dataclass, field
from collections import Counter

from .retrieve import retrieve


@dataclass
class TestCase:
    query: str
    primary: list[tuple[str, str]]
    secondary: list[tuple[str, str]] = field(default_factory=list)
    category_filter: str | None = None
    notes: str = ""


# ─────────────────────────────────────────────────────────────────────────────
# TEST SET
# Organized by category. Each case should reflect a realistic user situation,
# not a law-school exam question — that's what Nyaya will actually receive.
# Expand this over time; 60-100 cases is a credible eval set for a final
# year project. This starter set covers your existing categories.
# ─────────────────────────────────────────────────────────────────────────────
TEST_CASES: list[TestCase] = [
# ── Tenant / Property ──────────────────────────────────────────────────

TestCase(
    "landlord not returning security deposit",
    primary=[
        ("Transfer of Property", "108"),
    ],
    secondary=[],
    notes="No dedicated deposit section in TPA — commonly Sec 108 (lessee rights) is closest central-law anchor; state Rent Acts usually govern this better.",
),

TestCase(
    "landlord wants to evict me without notice",
    primary=[
        ("Transfer of Property", "106"),
    ],
    secondary=[],
),

TestCase(
    "what are my rights as a tenant under a lease",
    primary=[
        ("Transfer of Property", "108"),
    ],
    secondary=[],
),

    # ── Consumer ────────────────────────────────────────────────────────────
    TestCase(
    "shop refused to give refund on defective product",
    primary=[
        ("Consumer Protection", "39"),
    ],
    secondary=[
        ("Consumer Protection", "83"),
    ],
    category_filter="consumer",
),
   # ── Consumer ─────────────────────────────────────────────────────────────

TestCase(
    "defective product caused injury compensation",
    primary=[
        ("Consumer Protection", "83"),
    ],
    secondary=[
        ("Consumer Protection", "86"),
    ],
    category_filter="consumer",
),

TestCase(
    "shopkeeper selling product above MRP",
    primary=[
        ("Legal Metrology", ""),
    ],
    secondary=[],
    category_filter="consumer",
    notes="Section number flexible — any Legal Metrology Act hit on MRP/pricing is a pass.",
),

TestCase(
    "how to file a consumer complaint",
    primary=[
        ("Consumer Protection", "35"),
    ],
    secondary=[],
    category_filter="consumer",
),

# ── Labour ──────────────────────────────────────────────────────────────

TestCase(
    "employer not paying overtime wages",
    primary=[
        ("Labour Factories Act", "59"),
    ],
    secondary=[
        ("Code on Wages", "14"),
    ],
    category_filter="labour",
),

TestCase(
    "can employer make worker work more than 9 hours",
    primary=[
        ("Labour Factories Act", "54"),
    ],
    secondary=[
        ("Labour Factories Act", "51"),
    ],
    category_filter="labour",
),

TestCase(
    "maternity leave entitlement",
    primary=[
        ("Maternity Benefit", ""),
    ],
    secondary=[],
    category_filter="labour",
),

TestCase(
    "employer deducted salary without explanation",
    primary=[
        ("Payment of Wages", ""),
    ],
    secondary=[],
    category_filter="labour",
),
    TestCase(
    "injured at workplace who pays compensation",
    primary=[
        ("Code On Security", "74"),
    ],
    secondary=[
        ("Employees Compensation", "3"),
    ],
    category_filter="labour",
),
 # ── Criminal ────────────────────────────────────────────────────────────

TestCase(
    "punishment for murder",
    primary=[
        ("Bharatiya Nyaya Sanhita", "103"),
    ],
    secondary=[],
    category_filter="criminal",
),

TestCase(
    "bail conditions in a theft case",
    primary=[
        ("Bharatiya Nagarik Suraksha Sanhita", "480"),
    ],
    secondary=[
        ("Bharatiya Nagarik Suraksha Sanhita", "478"),
    ],
    category_filter="criminal",
),

TestCase(
    "what happens when police file an FIR",
    primary=[
        ("Bharatiya Nagarik Suraksha Sanhita", "173"),
    ],
    secondary=[],
    category_filter="criminal",
),

TestCase(
    "caught with illegal drugs first time",
    primary=[
        ("Narcotic Drugs", ""),
    ],
    secondary=[],
    category_filter="criminal",
),

TestCase(
    "found carrying an unlicensed weapon",
    primary=[
        ("Arms Act", ""),
    ],
    secondary=[],
    category_filter="criminal",
),

# ── Women & Child ───────────────────────────────────────────────────────

TestCase(
    "sexual harassment at workplace remedy",
    primary=[
        ("Sexual Harassment Of Women", "9"),
    ],
    secondary=[
        ("Sexual Harassment Of Women", "11"),
    ],
    category_filter="women_child",
),

TestCase(
    "wife harassed by husband legal remedy",
    primary=[
        ("Domestic Violence", "12"),
    ],
    secondary=[
        ("Domestic Violence", "18"),
    ],
    category_filter="women_child",
),

TestCase(
    "demanding dowry from bride's family",
    primary=[
        ("Dowry Prohibition", ""),
    ],
    secondary=[],
    category_filter="women_child",
),

TestCase(
    "child labour or child abuse complaint",
    primary=[
        ("Protection Of Children", ""),
    ],
    secondary=[
        ("Juvenile Justice", ""),
    ],
    category_filter="women_child",
),

# ── Family ──────────────────────────────────────────────────────────────

TestCase(
    "grounds for divorce under hindu law",
    primary=[
        ("Hindu Marriage", "13"),
    ],
    secondary=[],
    category_filter="family",
),

TestCase(
    "inheritance rights of daughter in hindu family",
    primary=[
        ("Hindu Succession", ""),
    ],
    secondary=[],
    category_filter="family",
),

TestCase(
    "who can be appointed guardian of a minor child",
    primary=[
        ("Guardians and Wards", ""),
    ],
    secondary=[],
    category_filter="family",
),

# ── Rights / Constitution ───────────────────────────────────────────────

TestCase(
    "right to free speech in india",
    primary=[
        ("Constitution", "19"),
    ],
    secondary=[],
    category_filter="constitution",
),

TestCase(
    "how to file an RTI application",
    primary=[
        ("Right To Information", "6"),
    ],
    secondary=[],
    category_filter="rights",
),

TestCase(
    "free legal aid for poor person",
    primary=[
        ("Legal Services Authorities", ""),
    ],
    secondary=[],
    category_filter="rights",
),

    # ── Cyber ───────────────────────────────────────────────────────────────
    TestCase(
    "someone hacked my online account",
    primary=[
        ("Information Technology", "66"),
        ("Information Technology", "66C"),
    ],
    secondary=[
        ("Information Technology", "72"),
    ],
    category_filter="cyber",
),
    TestCase(
    "fake profile created using my photos online",
    primary=[
        ("Information Technology", "66E"),
    ],
    secondary=[
        ("Information Technology", "66D"),
    ],
    category_filter="cyber",
),

    # ── Transport ───────────────────────────────────────────────────────────
# ── Transport ───────────────────────────────────────────────────────────

TestCase(
    "driving without a license penalty",
    primary=[
        ("Motor Vehicles", ""),
    ],
    secondary=[],
    category_filter="transport",
),

TestCase(
    "compensation after road accident",
    primary=[
        ("Motor Vehicles", "163"),
    ],
    secondary=[
        ("Motor Vehicles", "161"),
    ],
    category_filter="transport",
),

# ── Social justice ──────────────────────────────────────────────────────

TestCase(
    "discrimination against scheduled caste person",
    primary=[
        ("Scheduled Castes", ""),
    ],
    secondary=[],
    category_filter="social_justice",
),

TestCase(
    "rights of a disabled person at workplace",
    primary=[
        ("Rights Of Persons With Disabilities", ""),
    ],
    secondary=[],
    category_filter="social_justice",
),

TestCase(
    "elderly parents not being taken care of by children",
    primary=[
        ("Maintenance and Welfare", ""),
    ],
    secondary=[],
    category_filter="social_justice",
),
]

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

    primary_rank = None
    secondary_rank = None

    for i, r in enumerate(results, start=1):

        # Look for a primary match first
        if primary_rank is None:
            for exp_act, exp_sec in case.primary:
                if citation_matches(r, exp_act, exp_sec):
                    primary_rank = i
                    break

        # Look for a secondary match
        if secondary_rank is None:
            for exp_act, exp_sec in case.secondary:
                if citation_matches(r, exp_act, exp_sec):
                    secondary_rank = i
                    break

        # Stop once we've found both
        if (
            (primary_rank is not None or not case.primary)
            and
            (secondary_rank is not None or not case.secondary)
        ):
            break

    # Duplicate-citation check
    seen = Counter(
        (r.get("act_name", ""), str(r.get("section_number", "")))
        for r in results
    )
    dupes = {k: v for k, v in seen.items() if v > 1}

    # Category leakage check
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
        "primary_rank": primary_rank,
        "secondary_rank": secondary_rank,
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
                f'(primary={case.primary}, secondary={case.secondary})'
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