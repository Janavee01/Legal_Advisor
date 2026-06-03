from sentence_transformers import SentenceTransformer
import numpy as np

_model = None
_category_embeddings = None


CATEGORY_DESCRIPTIONS = {
    "criminal": """
    Criminal law involving murder, homicide,
    assault, theft, kidnapping, punishment,
    FIR, police investigation, bail,
    criminal procedure, offences against body.
    """,

    "consumer": """
    Consumer protection disputes involving refunds,
    defective products, ecommerce fraud,
    warranty claims, unfair trade practices,
    online shopping complaints, seller disputes.
    """,

    "family": """
    Family law involving divorce, marriage,
    child custody, maintenance, alimony,
    domestic violence, inheritance,
    matrimonial disputes.
    """,
}


def _get_model():
    global _model

    if _model is None:
        _model = SentenceTransformer(
            "BAAI/bge-base-en-v1.5"
        )

    return _model


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

    for category, description in CATEGORY_DESCRIPTIONS.items():

        embedding = model.encode(
            "query: " + description,
            normalize_embeddings=True
        )

        _category_embeddings[category] = embedding

    return _category_embeddings


def semantic_route(query: str):

    model = _get_model()

    category_embeddings = _build_category_embeddings()

    query_embedding = model.encode(
        "query: " + query,
        normalize_embeddings=True
    )

    best_category = None
    best_score = -1

    for category, embedding in category_embeddings.items():

        score = _cosine_similarity(
            query_embedding,
            embedding
        )

        if score > best_score:
            best_score = score
            best_category = category

    return {
        "category": best_category,
        "confidence": round(float(best_score), 4),
    }