#retrieve.py
import logging
from pathlib import Path
import re
import pickle
import numpy as np
from rank_bm25 import BM25Okapi
from ai_service.app.rag.query_context_builder import (
    get_query_context_builder
)
from ai_service.app.rag.reranker import rerank

from ai_service.app.rag.vectordb import get_collection
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)
import os
import logging

_ACT_NAME_PATTERNS = [
    re.compile(r"bharatiya\s+nagarik\s+suraksha\s+sanhita(?:\s+\d{4})?", re.IGNORECASE),
    re.compile(r"bharatiya\s+nyaya\s+sanhita(?:\s+\d{4})?", re.IGNORECASE),
    re.compile(r"bharatiya\s+sakshya\s+adhiniyam(?:\s+\d{4})?", re.IGNORECASE),
    re.compile(r"industrial\s+disputes\s+act(?:\s+\d{4})?", re.IGNORECASE),
    re.compile(r"industrial\s+relations\s+code(?:\s+\d{4})?", re.IGNORECASE),
    re.compile(r"occupational\s+safety\s+health\s+.*?(?:code|act)(?:\s+\d{4})?", re.IGNORECASE),
    re.compile(r"code\s+on\s+wages(?:\s+\d{4})?", re.IGNORECASE),
    re.compile(r"payment\s+of\s+wages\s+act(?:\s+\d{4})?", re.IGNORECASE),
    re.compile(r"factories\s+act(?:\s+\d{4})?", re.IGNORECASE),
    re.compile(r"labour\s+factories\s+act(?:\s+\d{4})?", re.IGNORECASE),
    re.compile(r"maternity\s+benefit\s+act(?:\s+\d{4})?", re.IGNORECASE),
    re.compile(r"employees\s+compensation\s+act(?:\s+\d{4})?", re.IGNORECASE),
    re.compile(r"employees\s+provident\s+funds?\s+.*?(?:act|code)?(?:\s+\d{4})?", re.IGNORECASE),
    re.compile(r"code\s+on\s+security(?:\s+\d{4})?", re.IGNORECASE),
    re.compile(r"consumer\s+protection\s+act(?:\s+\d{4})?", re.IGNORECASE),
    re.compile(r"legal\s+metrology\s+act(?:\s+\d{4})?", re.IGNORECASE),
    re.compile(r"motor\s+vehicles?\s+act(?:\s+\d{4})?", re.IGNORECASE),
    re.compile(r"transfer\s+of\s+property\s+act(?:\s+\d{4})?", re.IGNORECASE),
    re.compile(r"hindu\s+marriage\s+act(?:\s+\d{4})?", re.IGNORECASE),
    re.compile(r"special\s+marriage\s+act(?:\s+\d{4})?", re.IGNORECASE),
    re.compile(r"hindu\s+succession\s+act(?:\s+\d{4})?", re.IGNORECASE),
    re.compile(r"indian\s+succession\s+act(?:\s+\d{4})?", re.IGNORECASE),
    re.compile(r"guardians?\s+and\s+wards?\s+act(?:\s+\d{4})?", re.IGNORECASE),
    re.compile(r"protection\s+of\s+women\s+from\s+domestic\s+violence\s+act(?:\s+\d{4})?", re.IGNORECASE),
    re.compile(r"protection\s+of\s+children\s+from\s+sexual\s+offences\s+act(?:\s+\d{4})?", re.IGNORECASE),
    re.compile(r"juvenile\s+justice\s+act(?:\s+\d{4})?", re.IGNORECASE),
    re.compile(r"narcotic\s+drugs?\s+and\s+psychotropic\s+substances?\s+act(?:\s+\d{4})?", re.IGNORECASE),
    re.compile(r"arms\s+act(?:\s+\d{4})?", re.IGNORECASE),
    re.compile(r"information\s+technology\s+act(?:\s+\d{4})?", re.IGNORECASE),
    re.compile(r"right\s+to\s+information\s+act(?:\s+\d{4})?", re.IGNORECASE),
    re.compile(r"legal\s+services?\s+authorities?\s+act(?:\s+\d{4})?", re.IGNORECASE),
    re.compile(r"registration\s+act(?:\s+\d{4})?", re.IGNORECASE),
    re.compile(r"scheduled\s+castes?\s+and\s+scheduled\s+tribes?\s+act(?:\s+\d{4})?", re.IGNORECASE),
    re.compile(r"rights?\s+of\s+persons?\s+with\s+disabilities?\s+act(?:\s+\d{4})?", re.IGNORECASE),
    re.compile(r"maintenance\s+and\s+welfare\s+of\s+parents?\s+.*?(?:act)(?:\s+\d{4})?", re.IGNORECASE),
    re.compile(r"passports?\s+act(?:\s+\d{4})?", re.IGNORECASE),
    re.compile(r"evidence\s+act(?:\s+\d{4})?", re.IGNORECASE),
    re.compile(r"indian\s+penal\s+code(?:\s+\d{4})?", re.IGNORECASE),
    re.compile(r"code\s+of\s+criminal\s+procedure(?:\s+\d{4})?", re.IGNORECASE),
    re.compile(r"code\s+of\s+civil\s+procedure(?:\s+\d{4})?", re.IGNORECASE),
]

def _detect_act_names_from_query(query: str) -> list[str]:
    """Extract Act names directly from the raw user query."""
    query_lower = query.lower()
    detected = []
    for pattern in _ACT_NAME_PATTERNS:
        for match in pattern.finditer(query_lower):
            act_text = match.group().strip()
            # Normalise: strip trailing year, title-case it
            act_text = re.sub(r"\s+\d{4}$", "", act_text)
            # Title-case each word
            act_text = " ".join(w.capitalize() for w in act_text.split())
            detected.append(act_text)
    return list(dict.fromkeys(detected))

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
_vector_docs_by_id = None
_title_bm25 = None
_title_bm25_keys = None
BASE_DIR = Path(__file__).resolve().parents[3]
BM25_PATH = BASE_DIR / "ai_service" / "app" / "data" / "bm25.pkl"
VECTOR_STORE_PATH = BASE_DIR / "ai_service" / "app" / "data" / "vector_store.pkl"


def _get_model():
    return get_model()

from ai_service.app.rag.embedder import get_model, QUERY_PREFIX

def _embed(text, model):
    return model.encode(QUERY_PREFIX + text, normalize_embeddings=True).tolist()

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


def _load_vector_docs_by_id():
    """Map BM25's stable document ids to their Chroma record ids."""
    global _vector_docs_by_id

    if _vector_docs_by_id is None:
        if not VECTOR_STORE_PATH.exists():
            raise ValueError("vector_store.pkl missing")
        with open(VECTOR_STORE_PATH, "rb") as f:
            _vector_docs_by_id = {
                int(doc["id"]): doc for doc in pickle.load(f)
            }

    return _vector_docs_by_id


def _load_title_bm25():
    """Build a BM25 index from section titles for precise section discrimination."""
    global _title_bm25, _title_bm25_keys

    if _title_bm25 is not None:
        return _title_bm25, _title_bm25_keys

    with open(VECTOR_STORE_PATH, "rb") as f:
        all_docs = pickle.load(f)

    # Dedupe: keep one title per unique (act_name, section_number)
    seen = {}
    for doc in all_docs:
        key = (doc.get("act_name", ""), doc.get("section_number", ""))
        if key not in seen:
            seen[key] = doc

    titles = []
    keys = []
    for (act, sec), doc in seen.items():
        title = doc.get("section_title", "")
        if title:
            titles.append(title)
            keys.append((act, sec))

    tokenized_titles = [_tokenize(t) for t in titles]
    _title_bm25 = BM25Okapi(tokenized_titles)
    _title_bm25_keys = keys

    return _title_bm25, _title_bm25_keys

def dedupe_by_section(results, key_fn=lambda r: (r["act_name"], r["section_number"])):
    best = {}
    for r in results:
        k = key_fn(r)
        if k not in best or r["score"] > best[k]["score"]:
            best[k] = r
    return list(best.values())

def _tokenize(text: str):
    return re.findall(r"[a-zA-Z0-9]+", text.lower())


def _bm25_candidates(collection, query_embedding, scores, category, limit=50):
    """Fetch lexical candidates that are absent from dense top-k results."""
    docs_by_id = _load_vector_docs_by_id()
    candidates = []
    top_idx = np.argpartition(scores, -limit)[-limit:]
    top_idx = top_idx[np.argsort(scores[top_idx])[::-1]]

    for corpus_index in top_idx:
        if scores[corpus_index] <= 0:
            continue
        doc_id = int(_bm25_docs[corpus_index]["doc_id"])
        doc = docs_by_id.get(doc_id)
        if doc and (category is None or doc.get("category") == category):
            candidates.append(doc)
        if len(candidates) == limit:
            break

    if not candidates:
        return {"documents": [], "metadatas": [], "distances": []}

    fetched = collection.get(
        ids=[f"{doc['category']}::{doc['chunk_id']}" for doc in candidates],
        include=["documents", "metadatas", "embeddings"],
    )
    query_vec = np.asarray(query_embedding)
    distances = [
        float(np.sum((query_vec - np.asarray(embedding)) ** 2))
        for embedding in fetched["embeddings"]
    ]

    return {
        "documents": fetched["documents"],
        "metadatas": fetched["metadatas"],
        "distances": distances,
    }

def _stem(tok: str) -> str:
            # cheap suffix-stripping stemmer — enough to match report/reporting,
            # offence/offences, etc. without pulling in a dependency
            for suf in ("ing", "tion", "ed", "es", "s"):
                if tok.endswith(suf) and len(tok) - len(suf) >= 3:
                    return tok[: -len(suf)]
            return tok



def retrieve(query: str, top_k: int = 5, category_filter: str | None = None, min_score: float = 0.0):

    context = get_query_context_builder().build(query)
    print("QUERY:", query)
    print("INTENTS:", getattr(context, "intents", None))
    print("MATCHED INTENTS:", getattr(context, "matched_intents", None))
    print("CATEGORY:", context.category)
    print("EXPANDED QUERY:", context.expanded_query)
    print()

    # Intent examples can clarify the query
    query_to_embed = context.expanded_query
    
    model = _get_model()
    collection = get_collection()

    bm25, bm25_docs = _load_bm25()
    title_bm25, title_bm25_keys = _load_title_bm25()

    # ---- Multi-representation recall ----
    # Retrieve using several query views — the raw query, the intent-expanded
    # query, and a prototype-anchored view — and union their candidates.
    # A relevant section surfaced by any one view then gets a fair chance at
    # re-ranking, instead of being lost to the ceiling of a single embedding.
    query_views = [query]
    if context.expanded_query and context.expanded_query != query:
        query_views.append(context.expanded_query)
    prototype = (getattr(context, "prototype", "") or "").strip()
    if prototype:
        prototype_view = f"{query} {prototype}"
        if prototype_view not in query_views:
            query_views.append(prototype_view)

    view_embeddings = [_embed(v, model) for v in query_views]

    # A candidate's lexical score is its best match across all query views.
    bm25_view_scores = [
        bm25.get_scores(_tokenize(v))
        for v in query_views
    ]
    bm25_scores = np.maximum.reduce(bm25_view_scores)

    # Title BM25: precise lexical match against section titles
    title_bm25_scores = title_bm25.get_scores(_tokenize(query))
    title_bm25_lookup = {
        key: float(title_bm25_scores[i])
        for i, key in enumerate(title_bm25_keys)
    }
    title_bm25_mean = np.mean(title_bm25_scores)
    title_bm25_std = np.std(title_bm25_scores) + 1e-6

    bm25_lookup = {
        doc["doc_id"]: bm25_scores[i]
        for i, doc in enumerate(bm25_docs)
    }

    # Hard-filter only on an explicit caller-supplied category. The intent
    # classifier's auto-detected category is a soft boost (category_bonus)
    # instead — it is frequently wrong and hard-filtering it excluded the
    # correct Act entirely.
    where = {"category": category_filter} if category_filter else None
    print("WHERE =", where)
    # Detect Act names directly from the raw user query for query-act bonus
    query_act_names = _detect_act_names_from_query(query)
    print("QUERY ACT NAMES:", query_act_names)
    print("QUERY VIEWS:", query_views)

    # Dense recall: union top-k from every query view, with the usual
    # widen/fallback behaviour when the category filter is starved.
    all_docs, all_metas, all_dists = [], [], []
    for view_emb in view_embeddings:
        res = collection.query(
            query_embeddings=[view_emb],
            n_results=50,
            where=where,
            include=["documents", "metadatas", "distances"],
        )

        if where and len(res["documents"][0]) < 10:
            print("Category filter starved results — widening within-category search")
            res = collection.query(
                query_embeddings=[view_emb],
                n_results=150,
                where=where,
                include=["documents", "metadatas", "distances"],
            )

            if len(res["documents"][0]) < 10:
                print("Still starved after widening — category may be too small; "
                      "falling back unfiltered as last resort")
                res = collection.query(
                    query_embeddings=[view_emb],
                    n_results=50,
                    where=None,
                    include=["documents", "metadatas", "distances"],
                )

        all_docs.extend(res["documents"][0])
        all_metas.extend(res["metadatas"][0])
        all_dists.extend(res["distances"][0])

    # Lexical recall: union BM25 candidates from every query view.
    for view_emb, view_scores in zip(view_embeddings, bm25_view_scores):
        lexical_results = _bm25_candidates(
            collection,
            view_emb,
            view_scores,
            category_filter,
        )
        all_docs.extend(lexical_results["documents"])
        all_metas.extend(lexical_results["metadatas"])
        all_dists.extend(lexical_results["distances"])

    # Dedupe candidates, keeping the best (smallest) distance per unique chunk.
    best_by_key = {}
    for doc, meta, dist in zip(all_docs, all_metas, all_dists):
        if not doc or not meta:
            continue
        key = (
            meta["act_name"],
            meta["section_number"],
            meta["chunk_id"]
        )
        if key not in best_by_key or dist < best_by_key[key][2]:
            best_by_key[key] = (doc, meta, dist)

    docs = [v[0] for v in best_by_key.values()]
    metas = [v[1] for v in best_by_key.values()]
    dists = [v[2] for v in best_by_key.values()]

    chroma_results = {
        "documents": [docs],
        "metadatas": [metas],
        "distances": [dists],
    }

    print(chroma_results["documents"][0][:3])
    print(chroma_results["metadatas"][0][:3])
    print(chroma_results["distances"][0][:3])

    print("\nActs returned by Chroma:")
    acts = sorted(set(
        meta.get("act_name", "")
        for meta in chroma_results["metadatas"][0]
    ))
    for act in acts:
        print("-", act)


    results = []
    
    bm25_mean = np.mean(bm25_scores)
    bm25_std = np.std(bm25_scores) + 1e-6

    query_act_lower = [a.lower() for a in query_act_names]

    query_tokens = {_stem(t) for t in _tokenize(query)}
    expanded_tokens = {_stem(t) for t in _tokenize(query_to_embed)}
    
    for doc_text, meta, distance in zip(
        chroma_results["documents"][0],
        chroma_results["metadatas"][0],
        chroma_results["distances"][0],
    ):
        
        if not doc_text:
            continue

        semantic_score = np.exp(-distance)

        section_title = meta.get("section_title", "").lower()
        section_tokens = {_stem(t) for t in _tokenize(section_title)}

        # Use expanded query tokens for title matching — the expanded query
        # includes intent examples that share vocabulary with section titles
        overlap = len(expanded_tokens & section_tokens)

        if overlap >= 3:
            section_bonus = 0.30
        elif overlap == 2:
            section_bonus = 0.20
        elif overlap == 1:
            section_bonus = 0.08
        else:
            section_bonus = 0.0

      
        category_bonus = (
            0.10
            if context.category
            and meta.get("category") == context.category
            else 0.0
        )

        act_name_lower = meta.get("act_name", "").lower()

        # Query-Act-name boost: when the user explicitly mentions an Act
        # name in their query, sections from that Act get a significant
        # relevance boost — even if intent matching missed entirely.
        query_act_bonus = (
            0.15
            if any(act_name_lower in qa for qa in query_act_lower)
            else 0.0
        )
        doc_id = int(meta.get("doc_id", -1))
        if doc_id == -1:
            continue

        bm25_score = bm25_lookup.get(doc_id, 0.0)

        if overlap > 0:
            bm25_score *= 1.2

        bm25_norm = (bm25_score - bm25_mean) / bm25_std

        bm25_norm_sigmoid = 1 / (1 + np.exp(-bm25_norm))

        base_score = (
            0.50 * semantic_score +
            0.50 * bm25_norm_sigmoid +
            category_bonus +
            section_bonus +
            query_act_bonus
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
    results = results[:30]
    print("\nTop retrieval scores before rerank:")
    for r in results[:20]:
            print(
                f"{r['score']:.4f}",
                r["act_name"],
                r["section_number"],
                r["section_title"]
            )
    ranked = rerank(
    query,
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