from sentence_transformers import CrossEncoder

_model = None


def get_reranker():
    global _model

    if _model is None:
        _model = CrossEncoder(
            "cross-encoder/ms-marco-MiniLM-L-6-v2",
            device="cpu"
        )

    return _model


def rerank(query: str, results: list[dict]) -> list[dict]:
    if not results:
        return results

    model = get_reranker()

    pairs = [
        (query, r.get("text", ""))
        for r in results
        if r.get("text")
    ]

    if not pairs:
        return results

    scores = model.predict(pairs)

    for r, score in zip(results, scores):
        r["rerank_score"] = float(score)

    return sorted(
        results,
        key=lambda x: x.get("rerank_score", 0),
        reverse=True
    )