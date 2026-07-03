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
BASE_DIR = Path(__file__).resolve().parents[3]
BM25_PATH = BASE_DIR / "ai_service" / "app" / "data" / "bm25.pkl"


def _get_model():
    return get_model()

def _embed(text, model):
    return model.encode(
        text,
        normalize_embeddings=True
    ).tolist()

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

def dedupe_by_section(results, key_fn=lambda r: (r["act_name"], r["section_number"])):
    best = {}
    for r in results:
        k = key_fn(r)
        if k not in best or r["score"] > best[k]["score"]:
            best[k] = r
    return list(best.values())

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

    section_bias = "section title: relevant legal heading"

    query_to_embed = " ".join([
    context.expanded_query,
    context.expanded_query,   # reinforcement
    "section title",
    "legal provision heading",
    anchor_text,
    context.category or "",
])
    
    model = _get_model()
    collection = get_collection()

    bm25, bm25_docs = _load_bm25()


    main_embedding = np.array(
        _embed(query_to_embed, model)
    )

    anchor_embedding = np.array(
        _embed(anchor_text, model)
    ) if anchor_text else np.zeros_like(main_embedding)

    query_embedding = (
    0.7 * main_embedding +
    0.3 * anchor_embedding
)

    query_embedding = (
        query_embedding / np.linalg.norm(query_embedding)
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
    anchor_act_names = list({
        a.split(" Section")[0].strip()
        for a in context.anchors
    })  
    print("WHERE =", where)
    chroma_results = collection.query(
        query_embeddings=[query_embedding],
        n_results=50,
        where=where,
        include=["documents", "metadatas", "distances"],
    )
    print(chroma_results["documents"][0][:3])
    print(chroma_results["metadatas"][0][:3])
    print(chroma_results["distances"][0][:3])
    if anchor_act_names:
        anchor_results = collection.query(
            query_embeddings=[query_embedding],
            n_results=10,
            where={"act_name": {"$in": anchor_act_names}},
            include=["documents", "metadatas", "distances"],
        )
        # merge + dedupe by (act_name, section_number) before scoring
        for key in ("documents", "metadatas", "distances"):
            chroma_results[key][0].extend(anchor_results[key][0])

    seen = set()

    docs = []
    metas = []
    dists = []

    for doc, meta, dist in zip(
    chroma_results["documents"][0],
    chroma_results["metadatas"][0],
    chroma_results["distances"][0],
):
        key = (
            meta["act_name"],
            meta["section_number"],
            meta["chunk_id"]
        )

        if key in seen:
            continue

        seen.add(key)
        docs.append(doc)
        metas.append(meta)
        dists.append(dist)

    chroma_results["documents"][0] = docs
    chroma_results["metadatas"][0] = metas
    chroma_results["distances"][0] = dists
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

    anchor_acts_lower = [a.lower() for a in context.anchors]
    
    for doc_text, meta, distance in zip(
        chroma_results["documents"][0],
        chroma_results["metadatas"][0],
        chroma_results["distances"][0],
    ):
        
        if not doc_text:
            continue


        semantic_score = np.exp(-distance)
        section_sim = 0.0

        section_title = meta.get("section_title", "").lower()
        query_tokens = set(_tokenize(query))

        section_tokens = set(_tokenize(section_title))

        overlap = len(query_tokens & section_tokens)

        if overlap >= 3:
            section_bonus = 0.25
        elif overlap == 2:
            section_bonus = 0.15
        elif overlap == 1:
            section_bonus = 0.05
        else:
            section_bonus = -0.10

        section_tokens = set(_tokenize(meta.get("section_title", "")))
      
        category_bonus = 0.0

        if context.category and meta.get("category"):
            if meta["category"] == context.category:
                category_bonus = 0.10

        anchor_bonus = 0.0
        act_name_lower = meta.get("act_name", "").lower()
        section_number = str(meta.get("section_number", ""))
        for anchor in anchor_acts_lower:
            if act_name_lower and act_name_lower in anchor:
                # Extra boost if the anchor also names this exact section
                if section_number and f"section {section_number.lower()}" in anchor:
                    anchor_bonus = 0.25
                else:
                    anchor_bonus = 0.12
                break

        doc_id = int(meta.get("doc_id", -1))
        if doc_id == -1:
            continue

        bm25_score = bm25_lookup.get(doc_id, 0.0)

        if overlap > 0:
            bm25_score *= 1.2

        bm25_norm = (bm25_score - bm25_mean) / bm25_std

        bm25_norm_sigmoid = 1 / (1 + np.exp(-bm25_norm))

        anchor_boost = 0.0
        if context.anchors:
            chunk_act = meta.get("act_name", "").lower()
            chunk_section = str(meta.get("section_number", ""))
            for anchor in context.anchors:
                anchor_lower = anchor.lower()
                # anchor format: "Act Name Section X"
                if chunk_section in anchor_lower and any(
                    word in anchor_lower for word in chunk_act.split()[:3]
                ):
                    anchor_boost = 0.15
                    break

        base_score = (
    0.7 * semantic_score +
    0.3 * bm25_norm_sigmoid +
    category_bonus +
    anchor_bonus +
    section_bonus + anchor_boost
)
        

        results.append({
            "text": doc_text,
            "chunk_id": meta["chunk_id"],
            "citation": meta.get("citation", "Unknown"),
            "section_number": meta.get("section_number", ""),
            "section_title": meta.get("section_title", ""),
            "chapter": meta.get("chapter", ""),
            "act_name": meta.get("act_name", ""),
            "short_name": meta.get("short_name", ""),
            "year": meta.get("year", 0),
            "category": meta.get("category", ""),
            "source": meta.get("source", ""),
            "semantic_score": round(semantic_score, 4),
            "bm25_score": round(bm25_score, 4),
            "score": base_score,
        })


    results.sort(key=lambda x: x["score"], reverse=True)
    results = dedupe_by_section(results)
    results = results[:20]
    print("\nTop retrieval scores before rerank:")
    for r in sorted(results, key=lambda x: x["score"], reverse=True)[:20]:
            print(
                f"{r['score']:.4f}",
                r["act_name"],
                r["section_number"],
                r["section_title"]
            )
    ranked = rerank(
    f"{context.expanded_query} {' '.join(context.anchors)}",
    results,
)

    print("\nReranker scores:")
    for r in sorted(ranked, key=lambda x: x["final_score"], reverse=True):
        print(
            f"{r['final_score']:.4f}",
            f"rr={r['rerank_score']:.4f}",
            f"ret={r['score']:.4f}",
            r["citation"],
            r["section_title"],
        )
    
    ranked.sort(key=lambda x: x["final_score"], reverse=True)   
    ranked = dedupe_by_section(ranked, key_fn=lambda r: (r["act_name"], r["section_number"]))
    ranked = ranked[:top_k]

    seen = set()
    deduped = []

    for r in ranked:
        key = (r["act_name"], r["section_number"], r["chunk_id"])

        if key in seen:
            continue

        seen.add(key)
        deduped.append(r)

    ranked = deduped[:top_k]

    print("\nFinal Retrieval Results")
    for r in ranked:
        print(
            f"{r['final_score']:.4f}",
            r["citation"],
            r["section_title"]
        )

    return {
    "context": context,
    "chroma": chroma_results,
    "results": ranked
}