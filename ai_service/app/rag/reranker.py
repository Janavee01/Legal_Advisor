from sentence_transformers import CrossEncoder

_model = None


def get_reranker():
    global _model

    if _model is None:
        _model = CrossEncoder(
            "cross-encoder/ms-marco-MiniLM-L-6-v2"
        )

    return _model


def rerank(query: str, results: list[dict]) -> list[dict]:

    if not results:
        return results

    model = get_reranker()

    pairs = [
        (query, r["text"])
        for r in results
    ]

    scores = model.predict(pairs)

    for r, score in zip(results, scores):
        r["rerank_score"] = float(score)

    results.sort(
        key=lambda x: x["rerank_score"],
        reverse=True
    )

    return results