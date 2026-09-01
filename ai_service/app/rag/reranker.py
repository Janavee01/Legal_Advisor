"""
reranker.py — Fine-tuned cross-encoder reranker.

Retrieval:
    BAAI/bge-m3

Reranking:
    legal_advisor/training/reranker_finetune/finetuned_reranker

The fine-tuned reranker receives (query, legal-section) pairs and
produces the final relevance score used by retrieve.py.
"""

from pathlib import Path

import numpy as np
from sentence_transformers import CrossEncoder


_reranker = None

# ---------------------------------------------------------------------------
# Model path
# ---------------------------------------------------------------------------

# reranker.py:
#   legal_advisor/ai_service/app/rag/reranker.py
#
# parents[0] = rag
# parents[1] = app
# parents[2] = ai_service
# parents[3] = legal_advisor
#
# Therefore this resolves to:
#   legal_advisor/training/reranker_finetune/finetuned_reranker

PROJECT_ROOT = Path(__file__).resolve().parents[3]

FINETUNED_RERANKER_PATH = (
    PROJECT_ROOT
    / "training"
    / "reranker_finetune"
    / "finetuned_reranker"
)


# Maximum characters of section text sent to the cross-encoder.
#
# Keep this at 600 for the first comparison so that the ONLY major
# experimental change is the reranker model itself.
MAX_TEXT_CHARS = 600


# ---------------------------------------------------------------------------
# Load reranker
# ---------------------------------------------------------------------------

def get_reranker() -> CrossEncoder:
    global _reranker

    if _reranker is None:
        import torch

        device = (
            "cuda"
            if torch.cuda.is_available()
            else "cpu"
        )

        if not FINETUNED_RERANKER_PATH.exists():
            raise FileNotFoundError(
                "Fine-tuned reranker model not found at: "
                f"{FINETUNED_RERANKER_PATH}"
            )

        print(
            "Loading fine-tuned reranker:",
            FINETUNED_RERANKER_PATH,
        )

        _reranker = CrossEncoder(
            str(FINETUNED_RERANKER_PATH),
            device=device,
        )

        print(
            "Fine-tuned reranker loaded on:",
            device,
        )

    return _reranker


# ---------------------------------------------------------------------------
# Rerank
# ---------------------------------------------------------------------------

def rerank(
    query: str,
    results: list[dict],
) -> list[dict]:

    if not results:
        return results

    model = get_reranker()

    pairs = []
    valid_indices = []

    for i, result in enumerate(results):

        if not isinstance(result, dict):
            continue

        title = result.get(
            "section_title",
            "",
        )

        text = result.get(
            "text",
            "",
        )

        act = result.get(
            "act_name",
            "",
        )

        section = result.get(
            "section_number",
            "",
        )

        if not text:
            continue

        # ---------------------------------------------------------------
        # Keep the document representation identical to the previous
        # evaluation. This makes the model swap a clean A/B test.
        # ---------------------------------------------------------------

        text_truncated = (
            text[:MAX_TEXT_CHARS]
            + (
                " [truncated]"
                if len(text) > MAX_TEXT_CHARS
                else ""
            )
        )

        doc = (
            f"[TITLE] {title}. "
            f"[ACT] {act}. "
            f"[SECTION] {section}. "
            f"[TEXT] {text_truncated}"
        )

        pairs.append(
            (
                query,
                doc,
            )
        )

        valid_indices.append(i)

    if not pairs:
        return results

    # ---------------------------------------------------------------
    # Cross-encoder inference
    # ---------------------------------------------------------------

    raw_scores = model.predict(
    pairs,
    batch_size=16,
    show_progress_bar=False,
)

    # ---------------------------------------------------------------
    # Normalize reranker scores to [0, 1]
    # ---------------------------------------------------------------

    if len(raw_scores) > 1:

        score_min = raw_scores.min()
        score_max = raw_scores.max()

        score_range = (
            score_max
            - score_min
            + 1e-8
        )

        normalized_scores = (
            raw_scores - score_min
        ) / score_range

    else:
        normalized_scores = np.array(
            [1.0]
        )

    # ---------------------------------------------------------------
    # Attach scores
    # ---------------------------------------------------------------

    for idx, rerank_score, norm_score in zip(
        valid_indices,
        raw_scores,
        normalized_scores,
    ):

        result = results[idx]

        result["rerank_score"] = float(
            rerank_score
        )

        result["rerank_score_norm"] = float(
            norm_score
        )

        retrieval_score = float(
            result.get(
                "score",
                0.0,
            )
        )

        # -----------------------------------------------------------
        # Weak title signal
        # -----------------------------------------------------------

        title = result.get(
            "section_title",
            "",
        ).lower()

        query_tokens = set(
            query.lower().split()
        )

        title_tokens = set(
            title.split()
        )

        title_match = float(
            bool(
                query_tokens
                & title_tokens
            )
        )

        # -----------------------------------------------------------
        # Final score
        #
        # Keep the exact same blend as the previous evaluation.
        # This isolates the effect of changing the reranker model.
        # -----------------------------------------------------------

        result["final_score"] = (
            0.55 * retrieval_score
            + 0.40 * float(norm_score)
            + 0.05 * title_match
        )

    # ---------------------------------------------------------------
    # Final ordering
    # ---------------------------------------------------------------

    return sorted(
        [
            result
            for result in results
            if isinstance(result, dict)
        ],
        key=lambda result: result.get(
            "final_score",
            0,
        ),
        reverse=True,
    )