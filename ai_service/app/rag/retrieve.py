import logging
from pathlib import Path
import re
import pickle
from ai_service.app.retrieval.query_router import detect_intents
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer
from ai_service.app.retrieval.semantic_router import semantic_route
from ai_service.app.rag.reranker import rerank
from ai_service.app.rag.vectordb import get_collection

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)

_model = None
_bm25 = None
_bm25_docs = None

BASE_DIR = Path(__file__).resolve().parents[3]
BM25_PATH = BASE_DIR / "ai_service" / "app" / "data" / "bm25.pkl"


# ───────────────────────────────
# Model
# ───────────────────────────────

def _get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer("BAAI/bge-base-en-v1.5")
    return _model


def _embed(text: str, model):
    return model.encode("query: " + text, normalize_embeddings=True).tolist()


# ───────────────────────────────
# BM25
# ───────────────────────────────

def _load_bm25():
    global _bm25, _bm25_docs

    if _bm25 is not None:
        return _bm25, _bm25_docs

    if not BM25_PATH.exists():
        raise ValueError("bm25.pkl missing")

    data = pickle.load(open(BM25_PATH, "rb"))

    _bm25_docs = data["documents"]
    _bm25 = BM25Okapi(data["tokenized_corpus"])

    return _bm25, _bm25_docs


def _tokenize(text: str):
    return re.findall(r"[a-zA-Z0-9]+", text.lower())


# ───────────────────────────────
# Retrieve
# ───────────────────────────────

def retrieve(
    query: str,
    top_k: int = 5,
    category_filter: str | None = None,
    min_score: float = 0.30,
):

    model = _get_model()
    collection = get_collection()
    bm25, bm25_docs = _load_bm25()

    routing = detect_intents(query)
    semantic_category = semantic_route(query)

    print("SEMANTIC ROUTING:", semantic_category)

    query_embedding = _embed(query, model)

    # BM25 scores
    bm25_scores = bm25.get_scores(_tokenize(query))

    bm25_lookup = {
        doc["doc_id"]: bm25_scores[i]
        for i, doc in enumerate(bm25_docs)
    }

    # category routing
    predicted_category = semantic_category["category"]
    confidence = semantic_category["confidence"]

    if category_filter:
        final_category = category_filter
    elif confidence >= 0.65:
        final_category = predicted_category
    else:
        final_category = None

    where = {"category": final_category} if final_category not in (None, "") else None

    # ───────────────────────────────
    # Chroma retrieval
    # ───────────────────────────────

    chroma_results = collection.query(
        query_embeddings=[query_embedding],
        n_results=100,
        where=where,
        include=["documents", "metadatas", "distances"],
    )

    docs = chroma_results["documents"][0]

    print("DOC COUNT:", len(docs))

    if docs:
        print("FIRST DOC:", docs[0][:200])
        print("FIRST DIST:", chroma_results["distances"][0][0])
    else:
        print("NO DOCS RETURNED FROM CHROMA")
        return []

    # ───────────────────────────────
    # Build candidate list
    # ───────────────────────────────

    results = []

    for doc_text, meta, distance in zip(
        chroma_results["documents"][0],
        chroma_results["metadatas"][0],
        chroma_results["distances"][0],
    ):

        if not doc_text:
            continue

        semantic_score = max(0.0, 1.0 - distance / 2.0)

        # filter weak semantic matches
        if semantic_score < min_score:
            continue

        # BM25
        doc_id = meta.get("doc_id")
        bm25_score = 0.0

        if doc_id is not None:
            try:
                bm25_score = bm25_lookup.get(int(doc_id), 0.0)
            except:
                bm25_score = 0.0

        bm25_norm = bm25_score / (bm25_score + 5.0)

        final_score = 0.65 * semantic_score + 0.35 * bm25_norm

        # intent boosts
        section_title = meta.get("section_title", "").lower()
        citation = meta.get("citation", "").lower()
        text_lower = doc_text.lower()

        if routing.get("offence"):
            offence = routing["offence"].lower()

            if offence in section_title:
                final_score += 0.15
            if offence in citation:
                final_score += 0.10
            if offence in text_lower:
                final_score += 0.05

        if routing.get("intent"):
            intent = routing["intent"].lower()

            if intent in section_title:
                final_score += 0.12
            if intent in text_lower:
                final_score += 0.05

        if routing.get("section_number"):
            if str(meta.get("section_number")) == str(routing["section_number"]):
                final_score += 0.30

        results.append({
            "text": doc_text,
            "citation": meta.get("citation", "Unknown"),
            "section_number": meta.get("section_number", ""),
            "section_title": meta.get("section_title", ""),
            "chapter": meta.get("chapter", ""),
            "act_name": meta.get("act_name", ""),
            "short_name": meta.get("short_name", ""),
            "year": meta.get("year", 0),
            "category": meta.get("category", ""),
            "source": meta.get("source", ""),
            "topics": meta.get("topics", ""),
            "semantic_score": round(semantic_score, 4),
            "bm25_score": round(bm25_score, 4),
            "score": round(final_score, 4),
        })

    # ───────────────────────────────
    # Pre-rerank sorting
    # ───────────────────────────────

    results.sort(key=lambda x: x["score"], reverse=True)
    candidates = results[:100]

    print("BEFORE RERANK:", len(candidates))

    # ───────────────────────────────
    # CrossEncoder rerank (final authority)
    # ───────────────────────────────

    candidates = rerank(query, candidates)

    # enforce ordering from reranker
    candidates.sort(key=lambda x: x["rerank_score"], reverse=True)

    # attach final score
    for r in candidates:
        r["score"] = r.get("rerank_score", r["score"])

    print("AFTER RERANK:", len(candidates))

    return candidates[:top_k]


# ───────────────────────────────
# CLI test
# ───────────────────────────────

if __name__ == "__main__":
    import sys

    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "test query"

    results = retrieve(query, top_k=5)

    if not results:
        print("No results found")
    else:
        for r in results:
            print("\nSCORE:", r["score"])
            print("BM25:", r["bm25_score"], "SEM:", r["semantic_score"])
            print("CITATION:", r["citation"])
            print(r["text"][:300])