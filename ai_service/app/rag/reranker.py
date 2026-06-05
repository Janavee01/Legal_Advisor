from sentence_transformers import CrossEncoder
import numpy as np
import torch

_model = None


def get_reranker():
    global _model

    if _model is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"

        _model = CrossEncoder(
            "cross-encoder/ms-marco-MiniLM-L-6-v2",
            device=device
        )

    return _model


def rerank(query: str, results: list[dict]) -> list[dict]:
    if not results:
        return results

    model = get_reranker()

    pairs = []
    valid_results = []

    for r in results:
        text = r.get("text", "")

        if not text:
            continue

        doc = f"""
Act: {r.get('act_name', '')}
Citation: {r.get('citation', '')}
Section Title: {r.get('section_title', '')}

{text}
"""

        pairs.append((query, doc))
        valid_results.append(r)

    if not pairs:
        return results

    scores = model.predict(pairs)

    scores = np.array(scores, dtype=float)

    if len(scores) > 1:
        scores = (
            (scores - scores.min())
            / (scores.max() - scores.min() + 1e-8)
        )
    else:
        scores = np.array([1.0])

    for r, score in zip(valid_results, scores):
        r["rerank_score"] = float(score)

        retrieval_score = float(r.get("score", 0.0))

        r["final_score"] = (
            0.70 * float(score)
            + 0.30 * retrieval_score
        )

    return sorted(
        valid_results,
        key=lambda x: x["final_score"],
        reverse=True
    )