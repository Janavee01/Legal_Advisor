"""
00_merge_corpus.py

Your parsed data lives as multiple JSON files under datasets/parsed/<category>/*.json
(one file per act, most likely). This walks that whole tree and flattens
everything into a single JSON list of chunk dicts, which is what
01_mine_hard_negatives.py and 03_build_training_pairs.py expect.

Handles a few possible shapes per file, since I can't see your files directly:
  - a JSON list of chunk dicts                -> extend directly
  - a dict with a "chunks" / "sections" key    -> extend that list
  - a single chunk dict (has "act_name")       -> append as one chunk

Usage:
    python 00_merge_corpus.py ../../datasets/parsed all_chunks.json
"""

import json
import sys
from pathlib import Path


def load_chunks_from_file(path: Path) -> list[dict]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, list):
        return data

    if isinstance(data, dict):
        for key in ("chunks", "sections", "data"):
            if key in data and isinstance(data[key], list):
                return data[key]
        if "act_name" in data:
            return [data]

    print(f"  [warn] unrecognized shape in {path}, skipping")
    return []


def main(root_dir: str, out_path: str):
    root = Path(root_dir)
    json_files = sorted(root.rglob("*.json"))
    print(f"Found {len(json_files)} JSON files under {root}")

    all_chunks = []
    for jf in json_files:
        chunks = load_chunks_from_file(jf)
        all_chunks.extend(chunks)
        print(f"  {jf.relative_to(root)}: {len(chunks)} chunks")

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, indent=2, ensure_ascii=False)

    acts = sorted(set(c.get("act_name", "?") for c in all_chunks))
    print(f"\nTotal chunks: {len(all_chunks)}")
    print(f"Total acts:   {len(acts)}")
    print(f"Written to {out_path}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python 00_merge_corpus.py <datasets/parsed dir> <all_chunks_out.json>")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])