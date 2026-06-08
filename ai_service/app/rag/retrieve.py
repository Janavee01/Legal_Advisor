import logging
from pathlib import Path
import re
import pickle
import numpy as np
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer
from ai_service.app.rag.query_context_builder import QueryContextBuilder
from ai_service.app.rag.reranker import rerank
from ai_service.app.rag.vectordb import get_collection
from ai_service.app.retrieval.query_router import detect_intents
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)

_model = None
_bm25 = None
_bm25_docs = None
QUERY_PREFIX = "Represent this sentence for retrieval: "
BASE_DIR = Path(__file__).resolve().parents[3]
BM25_PATH = BASE_DIR / "ai_service" / "app" / "data" / "bm25.pkl"


def _get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer("BAAI/bge-base-en-v1.5")
    return _model


def _embed(text, model):
    return model.encode(text).tolist()


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
    
    context = QueryContextBuilder().build(query)

    query_to_embed = context.expanded_query
    predicted_category = getattr(context, "category", None)
    confidence = getattr(context, "confidence", 0.0)

    if category_filter:
        final_category = category_filter
    elif confidence >= 0.65:
        final_category = predicted_category
    else:
        final_category = None

    model = _get_model()
    collection = get_collection()

    bm25, bm25_docs = _load_bm25()

    
    query_embedding = (
    0.8 * np.array(_embed(query_to_embed, model))
    + 0.2 * np.array(_embed("legal provisions: " + query_to_embed, model))
).tolist()

    bm25_scores = bm25.get_scores(_tokenize(query))

    bm25_lookup = {
        doc["doc_id"]: bm25_scores[i]
        for i, doc in enumerate(bm25_docs)
    }

    where = None
    

    chroma_results = collection.query(
        query_embeddings=[query_embedding],
        n_results=200,
        where=where,
        include=["documents", "metadatas", "distances"],
    )   
    

    results = []
    
    
    bm25_scores = np.array(bm25_scores)

    max_bm25 = float(np.max(bm25_scores)) if bm25_scores.size > 0 else 1.0
    for doc_text, meta, distance in zip(
        chroma_results["documents"][0],
        chroma_results["metadatas"][0],
        chroma_results["distances"][0],
    ):
        
        if not doc_text:
            continue

        semantic_score = max(0.0, 1.0 - distance / 2.0)
        query_tokens = set(_tokenize(query))

        section_tokens = set(_tokenize(meta.get("section_title", "")))
        citation_tokens = set(_tokenize(meta.get("citation", "")))
        text_tokens = set(_tokenize(doc_text[:500]))  # limit noise
        
        category_bonus = 0.05 if meta.get("category") == context.category else 0.0
       
        doc_id = int(meta.get("doc_id", -1))
        if doc_id == -1:
            continue

        bm25_score = bm25_lookup.get(doc_id, 0.0)
        bm25_mean = np.mean(bm25_scores)
        bm25_std = np.std(bm25_scores) + 1e-6

        bm25_norm = (bm25_score - bm25_mean) / bm25_std
        bm25_norm = 1 / (1 + np.exp(-bm25_norm))

        title_overlap = len(
            query_tokens & section_tokens
        )
        
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
            "score": (
                0.70 * semantic_score +
                0.30 * bm25_norm +
                category_bonus
            ),
        })

    results.sort(key=lambda x: x["score"], reverse=True)
    results = results[:15]
    print("BEFORE RERANK:", len(results))
    
    results = rerank(context.expanded_query, results)
    
    print("AFTER RERANK:", len(results))
    print([type(r) for r in results])
  
    #return results[:top_k]
    return {
    "context": context,
    "results": results[:top_k]
    }

if __name__ == "__main__":
    import sys

    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "test query"

    output = retrieve(query, top_k=5)

    results = output["results"]

    if not results:
        print("No results found")
    else:
        for r in results:
            print("\nSCORE:", r.get("final_score", r["score"]))
            print("BM25:", r["bm25_score"], "SEM:", r["semantic_score"])
            print("CITATION:", r["citation"])
            print(r["text"][:300])