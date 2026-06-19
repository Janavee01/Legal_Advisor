#reranker.py
from sentence_transformers import CrossEncoder
import numpy as np
import torch

_model = None


from sentence_transformers import CrossEncoder

_reranker = None

def get_reranker():
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
    indices = []

    for i, r in enumerate(results):
        text = r.get("text")

        if not isinstance(r, dict):
            continue

        if not text:
            continue

        doc = (
    f"ACT: {r.get('act_name','')}\n"
    f"SECTION: {r.get('section_title','')}\n"
    f"CITATION: {r.get('citation','')}\n"
    f"CONTENT: {text}"
)

        pairs.append((query, doc))
        indices.append(i)

    if not pairs:
        return results

    BATCH_SIZE = 8
    scores = []

    for i in range(0, len(pairs), BATCH_SIZE):
        batch = pairs[i:i+BATCH_SIZE]
        scores.extend(model.predict(batch))
    scores = np.array(scores, dtype=float)

    if len(scores) > 1:
        scores = (scores - scores.min()) / (scores.max() - scores.min() + 1e-8)
    else:
        scores = np.array([1.0])

    for idx, score in zip(indices, scores):
        r = results[idx]

        if not isinstance(r, dict):
            continue

        r["rerank_score"] = float(score)

        retrieval_score = float(r.get("score", 0.0))

        r["final_score"] = (
            0.8 * r["rerank_score"] +
            0.2 * retrieval_score
        )

    return sorted(
        [r for r in results if isinstance(r, dict)],
        key=lambda x: x.get("final_score", 0),
        reverse=True
    )