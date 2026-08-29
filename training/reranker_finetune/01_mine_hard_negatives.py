"""
01_mine_hard_negatives.py

Groups your parsed corpus by Act, then for every section finds its most
"confusable" neighbours within the same Act — the pattern your eval showed
as the dominant failure mode (BNS 101 vs 103, BNS 137 vs 138, GWA 7 vs 8 vs
17, etc.).

Two signals, combined:
  1. Section-number adjacency (natural sort, handles "66E", "7Q", "14B").
  2. Section-title text similarity (difflib ratio) — catches confusable
     pairs that aren't numerically adjacent (e.g. "35" and "196" of the
     same Act, if titles are near-identical).

Input:  a JSON file that is a flat list of chunk dicts, each with at least
        act_name, section_number, section_title, text, category, citation.
        (Same schema as the sample chunk you showed me — this is whatever
        file ingest.py reads from before pushing into Chroma/BM25.)

Output: hard_negatives.json
        {
          "<act_name>||<section_number>": {
            "chunk": {...},                # the section itself
            "hard_negatives": [ {...}, ... ]  # 2-4 confusable sections, same act
          },
          ...
        }
"""

import json
import re
import sys
from difflib import SequenceMatcher
from pathlib import Path

N_HARD_NEGATIVES = 3          # how many confusable sections to keep per section
ADJACENCY_WINDOW = 2          # look +/- this many positions in sorted order
TITLE_SIM_THRESHOLD = 0.55    # difflib ratio above which titles count as "similar"


def section_sort_key(section_number: str):
    """Natural sort for '66E', '7Q', '14B', '180', '101' etc."""
    m = re.match(r"^\s*(\d+)\s*([A-Za-z]*)\s*$", str(section_number))
    if m:
        return (int(m.group(1)), m.group(2))
    return (float("inf"), str(section_number))


def title_similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, (a or "").lower(), (b or "").lower()).ratio()


def mine_for_act(chunks: list[dict]) -> dict[str, dict]:
    ordered = sorted(chunks, key=lambda c: section_sort_key(c["section_number"]))
    n = len(ordered)
    out = {}

    for i, chunk in enumerate(ordered):
        candidates = {}

        # Signal 1: numeric adjacency
        lo, hi = max(0, i - ADJACENCY_WINDOW), min(n, i + ADJACENCY_WINDOW + 1)
        for j in range(lo, hi):
            if j == i:
                continue
            other = ordered[j]
            key = (other["act_name"], other["section_number"])
            candidates[key] = candidates.get(key, 0.0) + 0.6  # adjacency weight

        # Signal 2: title similarity (catches non-adjacent confusables)
        for j, other in enumerate(ordered):
            if j == i:
                continue
            sim = title_similarity(chunk.get("section_title", ""), other.get("section_title", ""))
            if sim >= TITLE_SIM_THRESHOLD:
                key = (other["act_name"], other["section_number"])
                candidates[key] = candidates.get(key, 0.0) + sim

        ranked = sorted(candidates.items(), key=lambda kv: kv[1], reverse=True)
        top_keys = [k for k, _ in ranked[:N_HARD_NEGATIVES]]

        lookup = {(c["act_name"], c["section_number"]): c for c in ordered}
        hard_negs = [lookup[k] for k in top_keys if k in lookup]

        out_key = f"{chunk['act_name']}||{chunk['section_number']}"
        out[out_key] = {"chunk": chunk, "hard_negatives": hard_negs}

    return out


def main(corpus_path: str, out_path: str):
    with open(corpus_path, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    by_act: dict[str, list[dict]] = {}
    for c in chunks:
        by_act.setdefault(c["act_name"], []).append(c)

    result = {}
    for act, act_chunks in by_act.items():
        result.update(mine_for_act(act_chunks))

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    total_pairs = sum(len(v["hard_negatives"]) for v in result.values())
    print(f"Mined hard negatives for {len(result)} sections across {len(by_act)} acts.")
    print(f"Total (section, hard_negative) pairs: {total_pairs}")
    print(f"Written to {out_path}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python 01_mine_hard_negatives.py <corpus.json> <hard_negatives_out.json>")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])
