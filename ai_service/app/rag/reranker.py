"""
reranker.py — Cross-encoder reranker for retrieved legal sections.

Takes the top-N results from retrieve.py and re-scores them using a
cross-encoder model that sees the full (query, document) pair — giving
much stronger relevance signal than embedding cosine similarity alone.

The final score blends:
    - rerank_score  : cross-encoder raw logit (can be negative, large range)
    - retrieval score : normalized semantic + BM25 score from retrieve.py (0-1ish)
    - title_match   : weak signal if query terms appear in section title

Weights: retrieval 55%, rerank 35%, title 10%.
The retrieval score dominates slightly because the cross-encoder
ms-marco-MiniLM-L-6-v2 was trained on web passages, not Indian statute
text — it gives strong signal but isn't perfectly calibrated for this domain.
"""

from sentence_transformers import CrossEncoder
import numpy as np

_reranker = None

# Maximum characters of section text sent to the cross-encoder.
# ms-marco-MiniLM-L-6-v2 has a 512-token limit; ~600 chars is safe.
MAX_TEXT_CHARS = 600


def get_reranker() -> CrossEncoder:
    global _reranker
    if _reranker is None:
        _reranker = CrossEncoder(
            "cross-encoder/ms-marco-MiniLM-L-6-v2",
            device="cpu"
        )
    return _reranker


def rerank(query: str, results: list[dict]) -> list[dict]:
    if not results:
        return results

    model = get_reranker()
    pairs = []
    valid_indices = []

    for i, r in enumerate(results):
        if not isinstance(r, dict):
            continue

        title = r.get("section_title", "")
        text = r.get("text", "")
        act = r.get("act_name", "")
        section = r.get("section_number", "")

        if not text:
            continue

        # Truncate to model token limit
        text_truncated = text[:MAX_TEXT_CHARS] + (" [truncated]" if len(text) > MAX_TEXT_CHARS else "")

        # Format that gives the cross-encoder the most useful signal:
        # title repeated twice gives it extra weight since the cross-encoder
        # pays attention to early tokens more heavily.
        doc = (
            f"[TITLE] {title}. {title}. "
            f"[ACT] {act}. "
            f"[SECTION] {section}. "
            f"[TEXT] {text_truncated}"
        )

        pairs.append((query, doc))
        valid_indices.append(i)

    if not pairs:
        return results

    BATCH_SIZE = 8
    raw_scores = []

    for i in range(0, len(pairs), BATCH_SIZE):
        batch = pairs[i:i + BATCH_SIZE]
        raw_scores.extend(model.predict(batch))

    raw_scores = np.array(raw_scores, dtype=float)

    # Normalize rerank scores to [0, 1] so they're on the same scale
    # as retrieval_score. Without this, a single high-scoring result
    # dominates regardless of retrieval quality.
    # We use min-max normalization across this result set.
    if len(raw_scores) > 1:
        score_min = raw_scores.min()
        score_max = raw_scores.max()
        score_range = score_max - score_min + 1e-8
        normalized_scores = (raw_scores - score_min) / score_range
    else:
        normalized_scores = np.array([1.0])

    for idx, (rerank_score, norm_score) in zip(valid_indices, zip(raw_scores, normalized_scores)):
        r = results[idx]

        r["rerank_score"] = float(rerank_score)
        r["rerank_score_norm"] = float(norm_score)

        retrieval_score = float(r.get("score", 0.0))

        # Title match: weak keyword overlap signal
        title = r.get("section_title", "").lower()
        query_tokens = set(query.lower().split())
        title_tokens = set(title.split())
        title_match = float(bool(query_tokens & title_tokens))

        # Final blend: retrieval score dominates, rerank provides strong signal,
        # title match is a small tiebreaker.
        r["final_score"] = (
            0.55 * retrieval_score +
            0.35 * float(norm_score) +
            0.10 * title_match
        )

    return sorted(
        [r for r in results if isinstance(r, dict)],
        key=lambda x: x.get("final_score", 0),
        reverse=True
    )