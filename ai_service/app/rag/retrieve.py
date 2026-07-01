#retrieve.py
import logging
from pathlib import Path
import re
import pickle
import numpy as np
from rank_bm25 import BM25Okapi
from ai_service.app.rag.query_context_builder import QueryContextBuilder
from ai_service.app.rag.reranker import rerank
from ai_service.app.rag.embedder import get_model
from ai_service.app.rag.vectordb import get_collection
from ai_service.app.retrieval.query_router import detect_intents
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)
import os
import logging

os.environ["TQDM_DISABLE"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("huggingface_hub").setLevel(logging.ERROR)
logging.getLogger("sentence_transformers").setLevel(logging.ERROR)
logging.getLogger("transformers").setLevel(logging.ERROR)

_bm25 = None
_bm25_docs = None
QUERY_PREFIX = "Represent this sentence for retrieval: "
BASE_DIR = Path(__file__).resolve().parents[3]
BM25_PATH = BASE_DIR / "ai_service" / "app" / "data" / "bm25.pkl"


def _get_model():
    return get_model()

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
    print("QUERY:", query)
    print("INTENTS:", getattr(context, "intents", None))
    print("MATCHED INTENTS:", getattr(context, "matched_intents", None))
    print("CATEGORY:", context.category)
    print("ANCHORS:", context.anchors)
    print("EXPANDED QUERY:", context.expanded_query)
    print()

    anchor_text = " ".join(context.anchors)

    query_to_embed = " ".join([
        context.expanded_query,
        anchor_text,
        context.category or "",
        " ".join(context.intents)
    ]).strip()

    model = _get_model()
    collection = get_collection()

    bm25, bm25_docs = _load_bm25()

    anchor_text = " ".join(context.anchors)

    main_embedding = np.array(
        _embed(query_to_embed, model)
    )

    anchor_embedding = np.array(
        _embed(anchor_text, model)
    ) if anchor_text else np.zeros_like(main_embedding)

    query_embedding = (
        0.7 * main_embedding +
        0.3 * anchor_embedding
    ).tolist()
    
    bm25_query = (
    query_to_embed +
    " " +
    " ".join(context.anchors)
)

    bm25_scores = bm25.get_scores(
        _tokenize(bm25_query)
    )

    bm25_lookup = {
        doc["doc_id"]: bm25_scores[i]
        for i, doc in enumerate(bm25_docs)
    }


    where = {"category": context.category} if context.category else None

    chroma_results = collection.query(
        query_embeddings=[query_embedding],
        n_results=50,
        where=where,
        include=["documents", "metadatas", "distances"],
    )
    print("\nActs returned by Chroma:")
    acts = sorted(set(
        meta.get("act_name", "")
        for meta in chroma_results["metadatas"][0]
    ))
    for act in acts:
        print("-", act)


    results = []
    
    
    bm25_scores = np.array(bm25_scores)
    bm25_mean = np.mean(bm25_scores)
    bm25_std = np.std(bm25_scores) + 1e-6
    for doc_text, meta, distance in zip(
        chroma_results["documents"][0],
        chroma_results["metadatas"][0],
        chroma_results["distances"][0],
    ):
        
        if not doc_text:
            continue


        semantic_score = np.exp(-distance)
        query_tokens = set(_tokenize(query))
        section_hint = meta.get("section_title", "").lower()
        section_tokens = set(_tokenize(section_hint))

        section_overlap = len(query_tokens & section_tokens)

        section_penalty = -0.05 if section_overlap == 0 else 0.02

        section_tokens = set(_tokenize(meta.get("section_title", "")))
      
        category_bonus = 0.0

        if context.category and meta.get("category"):
            if meta["category"] == context.category:
                category_bonus = 0.10
            elif context.category in meta.get("topics", ""):
                category_bonus = 0.03

        anchor_bonus = 0.0
        act_name_lower = meta.get("act_name", "").lower()
        if any(act_name_lower in anchor.lower() for anchor in context.anchors):
            anchor_bonus = 0.15   # tune this
        
        if anchor_bonus > 0:
            print("ANCHOR BONUS:", meta["act_name"], meta["section_number"], anchor_bonus)
       
        doc_id = int(meta.get("doc_id", -1))
        if doc_id == -1:
            continue

        bm25_score = bm25_lookup.get(doc_id, 0.0)
  

        bm25_norm = (bm25_score - bm25_mean) / bm25_std

        intent_match = len(set(context.intents) & set(meta.get("topics", "").split(",")))
        intent_boost = 0.08 * intent_match
            
        bm25_norm_sigmoid = 1 / (1 + np.exp(-bm25_norm))

        base_score = (
            0.7 * semantic_score +
            0.3 * bm25_norm_sigmoid +
            category_bonus + anchor_bonus +
            intent_boost +
            section_penalty)

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
            "score": base_score,
        })

    print("\nRelevant act scores before rerank:")
    for r in sorted(results, key=lambda x: x["score"], reverse=True):
        if r["act_name"] in (
            "Protection Of Women From Domestic Violence Act 2005",
            "Legal Metrology Act 2009",
        ):
            print(
                r["score"],
                r["act_name"],
                r["section_number"],
                r["section_title"],
            )

    results.sort(key=lambda x: x["score"], reverse=True)
    results = results[:20]
    print("\nTop retrieval scores before rerank:")
    for r in sorted(results, key=lambda x: x["score"], reverse=True)[:20]:
            print(
                f"{r['score']:.4f}",
                r["act_name"],
                r["section_number"],
                r["section_title"]
            )
    rerank(
    f"{query}. Related legal concepts: {' '.join(context.intents)}",
    results,
)
    print("\nReranker scores:")
    for r in sorted(results, key=lambda x: x["final_score"], reverse=True):
        print(
            f"{r['final_score']:.4f}",
            f"rr={r['rerank_score']:.4f}",
            f"ret={r['score']:.4f}",
            r["act_name"],
            r["section_number"],
            r["section_title"],
        )
    results.sort(key=lambda x: x["final_score"], reverse=True)
    results = results[:top_k] 
    print("\nTOP RETRIEVAL RESULTS")

    for r in results[:top_k]:
        print(
            round(r["score"], 4),
            r["act_name"],
            r["section_number"],
            r["section_title"]
        )

    seen = set()
    deduped = []

    for r in results:
        key = (
            r["act_name"],
            r["section_number"]
        )

        if key in seen:
            continue

        seen.add(key)
        deduped.append(r)

    results = deduped[:top_k]

    for r in results[:10]:
        print(
            f"{r['final_score']:.4f}",
            f"rr={r['rerank_score']:.4f}",
            f"ret={r['score']:.4f}",
            r["act_name"],
            r["section_number"]
        )
    
    for r in results[:20]:
        print(
            round(r["final_score"], 4),
            r["act_name"],
            r["section_number"],
            r["section_title"]
        )
     
    return {
    "context": context,
    "chroma": chroma_results,
    "results": results[:top_k]
}

#if __name__ == "__main__":
#    import sys
#
#    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "test query"
#
#    output = retrieve(query, top_k=5)
#
#    results = output["results"]
#
#    if not results:
#        print("No results found")
#    else:
#        for r in results:
#            print("\nSCORE:", r.get("final_score", r["score"]))
#            print("BM25:", r["bm25_score"], "SEM:", r["semantic_score"])
#            print("CITATION:", r["citation"])
#            print(r["text"][:300])

