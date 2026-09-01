"""
04_finetune_reranker.py

Fine-tunes BAAI/bge-reranker-v2-m3 on training_pairs.json (output of
03_build_training_pairs.py) so it learns to discriminate between sibling
sections of the same Indian statute — the exact confusion pattern your
eval showed (e.g. Code On Security s.16 vs s.17, RTI Act s.18 vs s.19).

Saves the fine-tuned model to ./finetuned_reranker/. Point reranker.py's
get_reranker() at this local path instead of the HF hub id once you've
confirmed it improves eval.py's numbers (never swap it in blind).

Requires: pip install sentence-transformers torch

Usage:
    python 04_finetune_reranker.py training_pairs.json ./finetuned_reranker
"""

import json
import sys

from sentence_transformers import CrossEncoder, InputExample
from torch.utils.data import DataLoader


BASE_MODEL = "BAAI/bge-reranker-v2-m3"
EPOCHS = 1
BATCH_SIZE = 2
WARMUP_RATIO = 0.1
# Held out fraction for a quick sanity-check split; the real eval that
# matters is still eval.py / eval_misses_only.py against your full
# retrieval pipeline, not this loss number.
VAL_FRACTION = 0.05


def main(pairs_path: str, out_dir: str):
    with open(pairs_path, "r", encoding="utf-8") as f:
        pairs = json.load(f)

    examples = [
        InputExample(texts=[p["query"], p["doc"]], label=float(p["label"]))
        for p in pairs
    ]

    n_val = max(1, int(len(examples) * VAL_FRACTION))
    train_examples = examples[n_val:]
    val_examples = examples[:n_val]

    print(f"Training on {len(train_examples)} pairs, holding out {len(val_examples)} for sanity check")

    model = CrossEncoder(
    BASE_MODEL,
    num_labels=1,
    max_length=256,
)

    train_dataloader = DataLoader(train_examples, shuffle=True, batch_size=BATCH_SIZE)
    warmup_steps = int(len(train_dataloader) * EPOCHS * WARMUP_RATIO)

    model.fit(
        train_dataloader=train_dataloader,
        epochs=EPOCHS,
        warmup_steps=warmup_steps,
        output_path=out_dir,
        show_progress_bar=True,
    )

    model.save(out_dir)
    print(f"Fine-tuned model saved to {out_dir}")
    print(
        "\nNext steps:\n"
        f"  1. In reranker.py, temporarily point get_reranker() at '{out_dir}' "
        "instead of the hub id.\n"
        "  2. Run: python -m ai_service.app.rag.eval_misses_only\n"
        "  3. Only if strict Hit@1/3/5 improves without regressing the other "
        "148 previously-passing cases, run the full eval.py suite and keep it.\n"
    )


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python 04_finetune_reranker.py <training_pairs.json> <output_dir>")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])