import logging
from pathlib import Path
import re
import pickle

from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer

from reranker import rerank
from vectordb import get_collection

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)

_model = None
_bm25 = None
_bm25_docs = None

BASE_DIR = Path(__file__).resolve().parents[3]
BM25_PATH = BASE_DIR / "ai_service" / "app" / "data" / "bm25.pkl"


def _get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer("BAAI/bge-base-en-v1.5")
    return _model


def _embed(text: str, model):
    return model.encode("query: " + text, normalize_embeddings=True).tolist()


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


def retrieve(query: str, top_k: int = 5, category_filter: str | None = None, min_score: float = 0.0):

    model = _get_model()
    collection = get_collection()

    bm25, bm25_docs = _load_bm25()

    query_embedding = _embed(query, model)

    bm25_scores = bm25.get_scores(_tokenize(query))

    bm25_lookup = {
        doc["doc_id"]: bm25_scores[i]
        for i, doc in enumerate(bm25_docs)
    }

    where = {"category": category_filter} if category_filter else None

    chroma_results = collection.query(
        query_embeddings=[query_embedding],
        n_results=max(top_k * 3, 15),
        where=where,
        include=["documents", "metadatas", "distances"],
    )

    results = []

    for doc_text, meta, distance in zip(
        chroma_results["documents"][0],
        chroma_results["metadatas"][0],
        chroma_results["distances"][0],
    ):

        print("META KEYS:", meta.keys())
        print("META:", meta)
        
        if not doc_text:
            continue

        semantic_score = max(0.0, 1.0 - distance / 2.0)
        print("DIST:", distance, "SEM:", semantic_score)
        if semantic_score < min_score:
            continue

        doc_id = int(meta.get("doc_id", -1))
        if doc_id == -1:
            continue

        bm25_score = bm25_lookup.get(doc_id, 0.0)
        bm25_norm = bm25_score / (bm25_score + 5.0)

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
            "score": round(0.7 * semantic_score + 0.3 * bm25_norm, 4),
        })

    print("BEFORE RERANK:", len(results))

    results = rerank(query, results)
    
    print("AFTER RERANK:", len(results))

    return results[:top_k]

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