"""
retrieve.py — Retrieves relevant legal sections for a user query.

Uses Chroma as the primary store (not the pickle fallback).
Returns full citation metadata with every result.

Exports:
    retrieve(query, top_k, category_filter) -> list[dict]

Each result dict:
    text           : the legal text chunk
    citation       : "Consumer Protection Act, 2019 › Section 35 › Jurisdiction..."
    section_number : "35"
    section_title  : "Jurisdiction of District Commission"
    act_name       : "Consumer Protection Act, 2019"
    short_name     : "CPA 2019"
    year           : 2019
    category       : "consumer"
    score          : 0.82  (cosine similarity, higher = more relevant)
"""

import logging
from sentence_transformers import SentenceTransformer
from vectordb import get_collection

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)

_model = None  # lazy-loaded


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def retrieve(
    query: str,
    top_k: int = 5,
    category_filter: str | None = None,
    min_score: float = 0.3,
) -> list[dict]:
    """
    Query the vector store and return ranked legal sections.

    Args:
        query           : user's natural language query
        top_k           : number of results to return
        category_filter : restrict to one category ("consumer", "labour", "tenant", "criminal")
        min_score       : discard results below this cosine similarity threshold

    Returns:
        List of result dicts, sorted by score descending.
    """
    model = _get_model()
    collection = get_collection()

    query_embedding = model.encode(query).tolist()

    # Build Chroma where-filter if category is specified
    where = {"category": category_filter} if category_filter else None

    # Fetch more than top_k from Chroma to allow score filtering
    fetch_k = max(top_k * 3, 15)

    chroma_results = collection.query(
        query_embeddings=[query_embedding],
        n_results=fetch_k,
        where=where,
        include=["documents", "metadatas", "distances"],
    )

    results = []

    documents = chroma_results.get("documents", [[]])[0]
    metadatas = chroma_results.get("metadatas", [[]])[0]
    distances = chroma_results.get("distances", [[]])[0]

    for doc, meta, distance in zip(documents, metadatas, distances):
        # Chroma returns L2 distance; convert to cosine similarity
        # For normalised embeddings: cosine_sim = 1 - (distance / 2)
        score = 1.0 - (distance / 2.0)

        if score < min_score:
            continue

        results.append({
            "text":           doc,
            "citation":       meta.get("citation", "Unknown"),
            "section_number": meta.get("section_number", ""),
            "section_title":  meta.get("section_title", ""),
            "chapter":        meta.get("chapter", ""),
            "act_name":       meta.get("act_name", ""),
            "short_name":     meta.get("short_name", ""),
            "year":           meta.get("year", 0),
            "category":       meta.get("category", ""),
            "source":         meta.get("source", ""),
            "score":          round(score, 4),
        })

    # Sort by score and return top_k
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k]


def format_for_llm(results: list[dict]) -> str:
    """
    Format retrieved results into a context block for the LLM prompt.
    Each section clearly labeled with its citation.
    """
    if not results:
        return "No relevant legal sections found in the knowledge base."

    parts = []
    for i, r in enumerate(results, 1):
        parts.append(
            f"[Source {i}] {r['citation']}\n"
            f"{r['text']}"
        )

    return "\n\n---\n\n".join(parts)


# ── CLI test ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    test_queries = [
        ("landlord not returning security deposit", None),
        ("employer not paying overtime wages", "labour"),
        ("shop refused to give refund on defective product", "consumer"),
    ]

    for query, category in test_queries:
        print(f"\n{'='*60}")
        print(f"Query    : {query}")
        print(f"Category : {category or 'all'}")
        print("=" * 60)

        results = retrieve(query, top_k=3, category_filter=category)

        if not results:
            print("No results above threshold.")
            continue

        for r in results:
            print(f"\nScore    : {r['score']:.4f}")
            print(f"Citation : {r['citation']}")
            print(f"Text     : {r['text'][:200]}{'...' if len(r['text']) > 200 else ''}")