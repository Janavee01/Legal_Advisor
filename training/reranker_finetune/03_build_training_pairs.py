"""
03_build_training_pairs.py

Turns hard_negatives.json + section_queries.json into (query, doc, label)
training pairs for fine-tuning the CrossEncoder, in exactly the doc format
reranker.py uses at inference time — so the fine-tuned model sees the same
input shape it will see in production.

For every section with generated queries:
  - each query paired with its OWN section's doc  -> label 1.0
  - each query paired with each mined hard-negative section's doc -> label 0.0

This directly targets your eval's dominant failure mode: sibling sections
of the same Act (adjacent section numbers or near-identical titles) being
ranked above the correct one.

Input:
    hard_negatives.json   (output of 01_mine_hard_negatives.py)
    section_queries.json  (output of 02_generate_queries.py)
Output:
    training_pairs.json   — list of {"query", "doc", "label"}

Usage:
    python 03_build_training_pairs.py hard_negatives.json section_queries.json training_pairs.json
"""

import json
import sys

MAX_TEXT_CHARS = 600  # keep identical to reranker.py's MAX_TEXT_CHARS


def format_doc(chunk: dict) -> str:
    title = chunk.get("section_title", "")
    text = chunk.get("text", "")
    act = chunk.get("act_name", "")
    section = chunk.get("section_number", "")
    text_truncated = text[:MAX_TEXT_CHARS] + (" [truncated]" if len(text) > MAX_TEXT_CHARS else "")
    return f"[TITLE] {title}. [ACT] {act}. [SECTION] {section}. [TEXT] {text_truncated}"


def main(hard_neg_path: str, queries_path: str, out_path: str):
    with open(hard_neg_path, "r", encoding="utf-8") as f:
        hard_negs = json.load(f)
    with open(queries_path, "r", encoding="utf-8") as f:
        section_queries = json.load(f)

    pairs = []
    skipped_no_queries = 0

    for key, entry in hard_negs.items():
        queries = section_queries.get(key, [])
        if not queries:
            skipped_no_queries += 1
            continue

        chunk = entry["chunk"]
        pos_doc = format_doc(chunk)
        neg_docs = [format_doc(neg) for neg in entry["hard_negatives"]]

        for q in queries:
            pairs.append({"query": q, "doc": pos_doc, "label": 1.0})
            for neg_doc in neg_docs:
                pairs.append({"query": q, "doc": neg_doc, "label": 0.0})

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(pairs, f, indent=2, ensure_ascii=False)

    n_pos = sum(1 for p in pairs if p["label"] == 1.0)
    n_neg = sum(1 for p in pairs if p["label"] == 0.0)
    print(f"Sections skipped (no generated queries): {skipped_no_queries}")
    print(f"Total training pairs: {len(pairs)}  (positive={n_pos}, negative={n_neg})")
    print(f"Written to {out_path}")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python 03_build_training_pairs.py <hard_negatives.json> <section_queries.json> <training_pairs_out.json>")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2], sys.argv[3])