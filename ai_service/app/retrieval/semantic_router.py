from ai_service.app.rag.embedder import get_model
import numpy as np

_model = None
_category_embeddings = None
QUERY_PREFIX = "Represent this query for retrieving relevant legal passages: "
# ── Category prototype descriptions ────────────────────────────────────────────
# Each prototype is a rich text description of what belongs in the category.
# Keep descriptions distinct — overlapping language causes misrouting.
# Critical: "criminal" must be clearly separated from "women_child" because
# both have "punishment" sections. We achieve this by being explicit about
# which Acts live in each category.
from ai_service.app.rag.category_prototypes import CATEGORY_PROTOTYPES

def _get_model():
    return get_model()


def _cosine_similarity(a, b):
    return np.dot(a, b) / (
        np.linalg.norm(a) * np.linalg.norm(b)
    )


def _build_category_embeddings():
    global _category_embeddings

    if _category_embeddings is not None:
        return _category_embeddings

    model = _get_model()
    _category_embeddings = {}

    for category, description in CATEGORY_PROTOTYPES.items():
        embedding = model.encode(
            QUERY_PREFIX + description,
            normalize_embeddings=True
        )
        _category_embeddings[category] = embedding

    return _category_embeddings


def semantic_route(query: str):
    model = _get_model()
    category_embeddings = _build_category_embeddings()

    query_embedding = model.encode(
        QUERY_PREFIX + query,
        normalize_embeddings=True
    )

    scores = {
        category: float(_cosine_similarity(query_embedding, embedding))
        for category, embedding in category_embeddings.items()
    }

    best_category = max(scores, key=scores.get)
    best_score = scores[best_category]

    # Raised from 0.45 to 0.50 — reduces false-confidence misroutes.
    # A query that only weakly matches any category should fall back to
    # the full corpus rather than confidently routing to the wrong one.
    CONFIDENCE_THRESHOLD = 0.50

    return {
        "category": best_category if best_score >= CONFIDENCE_THRESHOLD else None,
        "confidence": round(best_score, 4),
        "all_scores": {k: round(v, 4) for k, v in sorted(scores.items(), key=lambda x: -x[1])},
    }