"""
faithfulness.py — Citation grounding check for generated answers.

Pipeline per test case:
  1. answer_retrieved(query)  -> grounded answer + the top-k sources used.
  2. Extract every citation in the answer ("Section X", "S. X" ...) and tie
     each to the act name mentioned nearest before it.
  3. Verify each (Act, Section) citation exists in the retrieved top-k
     context that was actually passed to the model.

Metrics:
    Citations total            : how many citations the model wrote
    Grounded (strict)          : (Act, Section) present in context
    Grounded (lenient)         : section number present in context, act unknown
    Citation precision         : grounded / total (strict & lenient)
    Source recall (coverage)   : distinct grounded sources / sources provided
    No-citation answers        : answered with zero usable citations

Semantic mis-attribution (citing a provided section with content that
belongs to another section) is NOT caught here — only presence in context.
A claim-level LLM judge pass can be added on top later.

Run:
    python -m ai_service.app.rag.faithfulness --limit 15
    python -m ai_service.app.rag.faithfulness --cases <file> --limit 0
    python -m ai_service.app.rag.eval --cases <file>
"""

import argparse
import contextlib
import io
import re
import sys
import time

from pathlib import Path

from .answer import answer_retrieved
from .eval import load_test_cases

PROJECT_ROOT = Path(__file__).resolve().parents[3]

SECTION_RE = re.compile(r"(?:[Ss]ection|[Ss]\.)\s+(\d+[A-Za-z]*)")


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


def _normalize_act(name: str) -> str:
    return (name or "").strip().lower()


def extract_citations(answer: str, known_acts: list[str]) -> list[dict]:
    """Return [{act, section, raw}] by pairing each Section N with the
    nearest preceding act-name mention."""
    acts_sorted = sorted(
        {a for a in known_acts if a}, key=len, reverse=True
    )

    citations = []

    for m in SECTION_RE.finditer(answer):
        section = m.group(1)
        before = answer[: m.start()]

        act = None
        for a in acts_sorted:
            if a.lower() in before.lower():
                act = a
                break

        citations.append(
            {
                "act": act,
                "section": section,
                "raw": answer[max(0, m.start() - 90): m.end()],
            }
        )

    return citations


def check_answer(answer: str, sources: list[dict]) -> dict:
    context_keys = {
        (_normalize_act(s.get("act_name")), str(s.get("section_number")))
        for s in sources
    }
    context_sections = {str(s.get("section_number")) for s in sources}

    citations = extract_citations(answer, [s.get("act_name") for s in sources])

    grounded_strict = []
    grounded_lenient = []
    ungrounded = []

    for c in citations:
        if not c["act"]:
            if c["section"] in context_sections:
                grounded_lenient.append(c)
            else:
                ungrounded.append(c)
            continue

        if (_normalize_act(c["act"]), c["section"]) in context_keys:
            grounded_strict.append(c)
        elif c["section"] in context_sections:
            grounded_lenient.append(c)
        else:
            ungrounded.append(c)

    grounded_set = {
        (_normalize_act(c["act"]), c["section"])
        for c in grounded_strict + grounded_lenient
    }

    distinct_grounded_sources = sum(
        1 for s in sources
        if (_normalize_act(s.get("act_name")), str(s.get("section_number")))
        in grounded_set
    )

    return {
        "citations": citations,
        "grounded_strict": grounded_strict,
        "grounded_lenient": grounded_lenient,
        "ungrounded": ungrounded,
        "sources": sources,
        "distinct_grounded_sources": distinct_grounded_sources,
    }


def run_case(case, top_k: int, model: str | None) -> dict:
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        out = answer_retrieved(
            case.query,
            top_k=top_k,
            model=model,
        )

    answer = out.get("answer", "")
    sources = out.get("sources", [])

    check = check_answer(answer, sources)

    return {
        "case": case,
        "answer": answer,
        "sources": sources,
        "model": out.get("model"),
        "usage": out.get("usage"),
        "check": check,
        "log": buf.getvalue(),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--limit", type=int, default=15,
                        help="max cases to run; 0 = all")
    parser.add_argument("--model", default=None,
                        help="Gemini model id override")
    parser.add_argument("--verbose", action="store_true",
                        help="print answers + captured retrieval log")
    parser.add_argument("--cases", type=str, default=None,
                        help="path to a python file defining TEST_CASES")
    args = parser.parse_args()

    test_cases = load_test_cases(args.cases)

    if args.limit and args.limit > 0:
        test_cases = test_cases[: args.limit]

    output_file = Path(__file__).with_name("faithfulness_output.txt")
    f = open(output_file, "w", encoding="utf-8")
    sys.stdout = Tee(sys.__stdout__, f)

    print(f"Running {len(test_cases)} cases (top_k={args.top_k})\n")

    total_citations = 0
    grounded_strict = 0
    grounded_lenient = 0
    ungrounded = 0
    no_citation_cases = 0
    coverage_sum = 0.0
    errors = 0
    first_usage = None

    flagged = []

    t0 = time.perf_counter()

    for case in test_cases:
        try:
            outcome = run_case(case, args.top_k, args.model)
        except Exception as e:
            errors += 1
            print(f"ERROR on '{case.query}': {e}")
            continue

        answer = outcome["answer"]
        check = outcome["check"]
        sources = outcome["sources"]

        n = len(check["citations"])
        gs = len(check["grounded_strict"])
        gl = len(check["grounded_lenient"])
        ug = len(check["ungrounded"])
        ungrounded_cites = [
            c["raw"].replace("\n", " ") for c in check["ungrounded"]
        ]

        total_citations += n
        grounded_strict += gs
        grounded_lenient += gl
        ungrounded += ug

        if n == 0:
            no_citation_cases += 1

        coverage = (
            check["distinct_grounded_sources"] / len(sources)
            if sources
            else 0.0
        )
        coverage_sum += coverage

        sources_cited = [
            f"{_normalize_act(s.get('act_name'))} s{str(s.get('section_number'))}"
            for s in sources
            if (_normalize_act(s.get("act_name")), str(s.get("section_number")))
            in {
                (_normalize_act(c["act"]), c["section"])
                for c in check["grounded_strict"] + check["grounded_lenient"]
            }
        ]

        if args.verbose:
            print(f'━━━ {case.query}')
            print(f'ANSWER:\n{answer}\n')
            print(f'SOURCES ({len(sources)}):')
            for s in sources:
                print(f"  - {s.get('citation')}")
            print()

        flagged_bits = []
        if ug:
            flagged_bits.append(f"{ug} UNGROUNDED")
        if not sources_cited and n:
            flagged_bits.append("cited-but-no-source-match")
        if n == 0:
            flagged_bits.append("NO CITATIONS")

        verdict = "OK" if not flagged_bits else "!"

        print(
            f"[{verdict}] citations={n:2d} grounded={gs + gl:2d}/{n:2d} "
            f"coverage={coverage:4.0%} {case.query}"
            f"{' | ' + ', '.join(flagged_bits) if flagged_bits else ''}"
        )

        if flagged_bits:
            flagged.append((case, flagged_bits, ungrounded_cites))

        if first_usage is None and outcome.get("usage"):
            first_usage = outcome.get("usage")

    elapsed = time.perf_counter() - t0

    print("=" * 78)
    n_cases = len(test_cases) - errors
    print(f"CASES    : {n_cases} ({elapsed:.1f}s total)")
    print(f"ERRORS   : {errors}")
    print(f"Citations: {total_citations} total "
          f"({total_citations / n_cases:.1f} per answered case)"
          if n_cases else "")
    if total_citations:
        print(f"Grounded strict : {grounded_strict}/{total_citations} "
              f"({100 * grounded_strict / total_citations:.1f}%)")
        print(f"Grounded lenient: {grounded_lenient}/{total_citations} "
              f"({100 * grounded_lenient / total_citations:.1f}%)")
        print(f"Ungrounded      : {ungrounded}/{total_citations} "
              f"({100 * ungrounded / total_citations:.1f}%)")
        print(f"Citation prec. (strict) : "
              f"{100 * grounded_strict / total_citations:.1f}%")
        print(f"Citation prec. (lenient): "
              f"{100 * (grounded_strict + grounded_lenient) / total_citations:.1f}%")
        print(f"Source recall (coverage) : {coverage_sum / n_cases:.1%}")
    print(f"No-citation answers: {no_citation_cases}/{n_cases}")

    if flagged:
        print("\n⚠ FLAGGED CASES:")
        for case, bits, ugs in flagged:
            print(f'  - "{case.query}" -> {", ".join(bits)}')
            for u in ugs:
                print(f"      ✗ ungrounded cite: ...{u}...")
        print()

    if first_usage:
        print("Sample usage metadata:", first_usage)

    sys.exit(1 if (flagged or errors) else 0)


if __name__ == "__main__":
    main()