import logging
from pathlib import Path
import re
import pickle
import time
import numpy as np
from rank_bm25 import BM25Okapi
from ai_service.app.rag.query_context_builder import (
    get_query_context_builder
)
from ai_service.app.rag.reranker import rerank, parse_anchor_keys, _anchor_tier

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
            act_text = re.sub(r"\s+\d{4}$", "", act_text)
            act_text = " ".join(w.capitalize() for w in act_text.split())
            detected.append(act_text)
    return list(dict.fromkeys(detected))


os.environ["TQDM_DISABLE"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

# Optional per-stage timing diagnostics (enabled with RETRIEVE_TIMING=1).
_TIMING = os.environ.get("RETRIEVE_TIMING") == "1"

_TITLE_OVERLAP_STOPWORDS = {
    "provid", "under", "law", "shall", "may", "act", "code", "section",
    "person", "matter", "relat", "purpos", "time", "make", "made", "requir",
    "everi", "ani", "such", "thi", "that", "who", "what", "how", "when",
    "where", "doe", "is", "do", "in", "of", "for", "to", "a", "the", "and",
    "or", "be", "with", "on", "if", "not", "by",
}

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("huggingface_hub").setLevel(logging.ERROR)
logging.getLogger("sentence_transformers").setLevel(logging.ERROR)
logging.getLogger("transformers").setLevel(logging.ERROR)

_bm25 = None
_bm25_docs = None
_bm25_doc_pos = None
_vector_docs_by_id = None
_title_bm25 = None
_title_bm25_keys = None
_title_bm25_pos = None

# Cache BM25 candidate Chroma records so multiple query views do not
# repeatedly fetch the same document + embedding.
_bm25_candidate_cache = {}

BASE_DIR = Path(__file__).resolve().parents[3]
BM25_PATH = BASE_DIR / "ai_service" / "app" / "data" / "bm25.pkl"
VECTOR_STORE_PATH = BASE_DIR / "ai_service" / "app" / "data" / "vector_store.pkl"


def _get_model():
    return get_model()


from ai_service.app.rag.embedder import (
    get_model,
    QUERY_PREFIX,
    free_gpu_for_rerank,
    restore_embedder,
)


def _embed(text, model):
    return model.encode(
        QUERY_PREFIX + text,
        normalize_embeddings=True
    ).tolist()


def _load_bm25():
    global _bm25, _bm25_docs, _bm25_doc_pos

    if _bm25 is not None:
        return _bm25, _bm25_docs

    if not BM25_PATH.exists():
        raise ValueError("bm25.pkl missing")

    with open(BM25_PATH, "rb") as f:
        data = pickle.load(f)

    _bm25_docs = data["documents"]
    # Precompute a once-per-process doc_id → score-array index. Previously
    # every query rebuilt a full-corpus {doc_id: score} dict.
    _bm25_doc_pos = {
        int(doc["doc_id"]): i
        for i, doc in enumerate(_bm25_docs)
    }
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
    global _title_bm25, _title_bm25_keys, _title_bm25_pos

    if _title_bm25 is not None:
        return _title_bm25, _title_bm25_keys

    with open(VECTOR_STORE_PATH, "rb") as f:
        all_docs = pickle.load(f)

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
    # Precompute a once-per-process (act, section) → index map instead of
    # rebuilding a full dict on every query.
    _title_bm25_pos = {
        key: i
        for i, key in enumerate(keys)
    }

    return _title_bm25, _title_bm25_keys


def dedupe_by_section(
    results,
    key_fn=lambda r: (r["act_name"], r["section_number"])
):
    best = {}

    for r in results:
        k = key_fn(r)

        if k not in best or r["score"] > best[k]["score"]:
            best[k] = r

    return list(best.values())


def _tokenize(text: str):
    return re.findall(r"[a-zA-Z0-9]+", text.lower())


def _bm25_candidates(
    collection,
    query_embedding,
    scores,
    category,
    limit=80
):
    """Fetch lexical candidates that are absent from dense top-k results."""

    docs_by_id = _load_vector_docs_by_id()

    # Same candidate selection logic as before.
    top_idx = np.argpartition(scores, -limit)[-limit:]
    top_idx = top_idx[np.argsort(scores[top_idx])[::-1]]

    candidates = []

    for corpus_index in top_idx:
        if scores[corpus_index] <= 0:
            continue

        doc_id = int(_bm25_docs[corpus_index]["doc_id"])
        doc = docs_by_id.get(doc_id)

        if doc and (
            category is None
            or doc.get("category") == category
        ):
            candidates.append(doc)

        if len(candidates) == limit:
            break

    if not candidates:
        return {
            "documents": [],
            "metadatas": [],
            "distances": [],
        }

    # Only fetch documents that are not already cached.
    uncached = []

    for doc in candidates:
        cache_key = f"{doc['category']}::{doc['chunk_id']}"

        if cache_key not in _bm25_candidate_cache:
            uncached.append(doc)

    if uncached:
        fetched = collection.get(
            ids=[
                f"{doc['category']}::{doc['chunk_id']}"
                for doc in uncached
            ],
            include=["documents", "metadatas", "embeddings"],
        )

        for doc, document, metadata, embedding in zip(
            uncached,
            fetched["documents"],
            fetched["metadatas"],
            fetched["embeddings"],
        ):
            cache_key = f"{doc['category']}::{doc['chunk_id']}"

            _bm25_candidate_cache[cache_key] = (
                document,
                metadata,
                np.asarray(embedding, dtype=np.float32),
            )

    query_vec = np.asarray(
        query_embedding,
        dtype=np.float32
    )

    documents = []
    metadatas = []
    distances = []

    for doc in candidates:
        cache_key = f"{doc['category']}::{doc['chunk_id']}"

        cached = _bm25_candidate_cache.get(cache_key)

        if cached is None:
            continue

        document, metadata, embedding = cached

        documents.append(document)
        metadatas.append(metadata)

        distances.append(
            float(
                np.sum(
                    (query_vec - embedding) ** 2
                )
            )
        )

    return {
        "documents": documents,
        "metadatas": metadatas,
        "distances": distances,
    }


def _stem(tok: str) -> str:
    # cheap suffix-stripping stemmer — enough to match report/reporting,
    # offence/offences, etc. without pulling in a dependency
    for suf in ("ing", "tion", "ed", "es", "s"):
        if tok.endswith(suf) and len(tok) - len(suf) >= 3:
            return tok[:-len(suf)]

    return tok


def retrieve(
    query: str,
    top_k: int = 5,
    category_filter: str | None = None,
    min_score: float = 0.0
):

    t0 = time.perf_counter()

    def mark(label: str = ""):
        nonlocal t0
        if _TIMING:
            now = time.perf_counter()
            print(f"[timing] {label:28s} {now - t0:7.2f}s")
            t0 = now

    context = get_query_context_builder().build(query)

    mark("context build")

    print("QUERY:", query)
    print("INTENTS:", getattr(context, "intents", None))
    print("MATCHED INTENTS:", getattr(context, "matched_intents", None))
    print("CATEGORY:", context.category)
    print("EXPANDED QUERY:", context.expanded_query)
    print()

    query_to_embed = context.expanded_query

    model = _get_model()
    collection = get_collection()

    bm25, bm25_docs = _load_bm25()
    title_bm25, title_bm25_keys = _load_title_bm25()

    # ---------------------------------------------------------
    # Multi-representation recall
    # ---------------------------------------------------------

    query_views = [query]

    if (
        context.expanded_query
        and context.expanded_query != query
    ):
        query_views.append(context.expanded_query)

    prototype = (
        getattr(context, "prototype", "") or ""
    ).strip()

    if prototype:
        prototype_view = f"{query} {prototype}"

        if prototype_view not in query_views:
            query_views.append(prototype_view)

    # PERFORMANCE:
    # Encode every query view in one model call instead of one call
    # per view. This preserves exactly the same embeddings.
    encoded = model.encode(
        [QUERY_PREFIX + v for v in query_views],
        normalize_embeddings=True,
        convert_to_numpy=True,
    )

    view_embeddings = encoded.tolist()

    mark("embed query views")

    # ---------------------------------------------------------
    # BM25
    # ---------------------------------------------------------

    bm25_view_scores = [
        bm25.get_scores(_tokenize(v))
        for v in query_views
    ]

    bm25_scores = np.maximum.reduce(
        bm25_view_scores
    )

    mark("bm25 scoring")

    # ---------------------------------------------------------
    # Title BM25
    # ---------------------------------------------------------

    title_bm25_scores = title_bm25.get_scores(
        _tokenize(query)
    )

    title_bm25_mean = np.mean(title_bm25_scores)
    title_bm25_std = np.std(title_bm25_scores) + 1e-6

    # bm25_scores / title_bm25_scores are the full-corpus score arrays;
    # per-query {id: score} dicts are replaced by once-per-process position
    # maps (_bm25_doc_pos / _title_bm25_pos) indexed in the scoring loop.

    # ---------------------------------------------------------
    # Category / Act detection
    # ---------------------------------------------------------

    where = (
        {"category": category_filter}
        if category_filter
        else None
    )

    print("WHERE =", where)

    query_act_names = _detect_act_names_from_query(query)

    print("QUERY ACT NAMES:", query_act_names)
    print("QUERY VIEWS:", query_views)

    primary_anchor_keys = parse_anchor_keys(
        getattr(context, "primary_anchors", []) or []
    )

    secondary_anchor_keys = parse_anchor_keys(
        getattr(context, "secondary_anchors", []) or []
    )

    anchor_keys = primary_anchor_keys | secondary_anchor_keys

    print("PRIMARY KEYS:", primary_anchor_keys)
    print("SECONDARY KEYS:", secondary_anchor_keys)

    # ---------------------------------------------------------
    # Dense recall
    # ---------------------------------------------------------

    all_docs = []
    all_metas = []
    all_dists = []

    # PERFORMANCE:
    # When no fallback is required, issue all dense queries in one
    # Chroma call instead of making 3 separate calls.
    #
    # Chroma accepts multiple query embeddings and returns one result
    # list per embedding.
    res = collection.query(
        query_embeddings=view_embeddings,
        n_results=80,
        where=where,
        include=["documents", "metadatas", "distances"],
    )

    # Detect whether category starvation requires the existing
    # widening/fallback behavior.
    needs_fallback = (
        where
        and any(
            len(documents) < 10
            for documents in res["documents"]
        )
    )

    if not needs_fallback:
        for documents, metadatas, distances in zip(
            res["documents"],
            res["metadatas"],
            res["distances"],
        ):
            all_docs.extend(documents)
            all_metas.extend(metadatas)
            all_dists.extend(distances)

    else:
        # Preserve the original per-view fallback behavior exactly.
        for view_emb in view_embeddings:
            res = collection.query(
                query_embeddings=[view_emb],
                n_results=80,
                where=where,
                include=[
                    "documents",
                    "metadatas",
                    "distances",
                ],
            )

            if len(res["documents"][0]) < 10:
                print(
                    "Category filter starved results — "
                    "widening within-category search"
                )

                res = collection.query(
                    query_embeddings=[view_emb],
                    n_results=150,
                    where=where,
                    include=[
                        "documents",
                        "metadatas",
                        "distances",
                    ],
                )

                if len(res["documents"][0]) < 10:
                    print(
                        "Still starved after widening — category may "
                        "be too small; falling back unfiltered as "
                        "last resort"
                    )

                    res = collection.query(
                        query_embeddings=[view_emb],
                        n_results=50,
                        where=None,
                        include=[
                            "documents",
                            "metadatas",
                            "distances",
                        ],
                    )

            all_docs.extend(res["documents"][0])
            all_metas.extend(res["metadatas"][0])
            all_dists.extend(res["distances"][0])

    mark("chroma dense query")

    # ---------------------------------------------------------
    # Lexical recall
    # ---------------------------------------------------------

    for view_emb, view_scores in zip(
        view_embeddings,
        bm25_view_scores,
    ):
        lexical_results = _bm25_candidates(
            collection,
            view_emb,
            view_scores,
            category_filter,
        )

        all_docs.extend(
            lexical_results["documents"]
        )
        all_metas.extend(
            lexical_results["metadatas"]
        )
        all_dists.extend(
            lexical_results["distances"]
        )

    mark("lexical recall")

    # ---------------------------------------------------------
    # Dedupe candidate chunks
    # ---------------------------------------------------------

    best_by_key = {}

    for doc, meta, dist in zip(
        all_docs,
        all_metas,
        all_dists,
    ):
        if not doc or not meta:
            continue

        key = (
            meta["act_name"],
            meta["section_number"],
            meta["chunk_id"],
        )

        if (
            key not in best_by_key
            or dist < best_by_key[key][2]
        ):
            best_by_key[key] = (
                doc,
                meta,
                dist,
            )

    docs = [
        v[0]
        for v in best_by_key.values()
    ]

    metas = [
        v[1]
        for v in best_by_key.values()
    ]

    dists = [
        v[2]
        for v in best_by_key.values()
    ]

    chroma_results = {
        "documents": [docs],
        "metadatas": [metas],
        "distances": [dists],
    }

    # Keep only lightweight diagnostics.
    print(
        f"\nCandidate chunks after dedupe: {len(docs)}"
    )

    print("\nActs returned by Chroma:")
    acts = sorted(
        set(
            meta.get("act_name", "")
            for meta in metas
        )
    )

    for act in acts:
        print("-", act)

    # ---------------------------------------------------------
    # Scoring
    # ---------------------------------------------------------

    results = []

    bm25_mean = np.mean(bm25_scores)
    bm25_std = np.std(bm25_scores) + 1e-6

    query_act_lower = [
        a.lower()
        for a in query_act_names
    ]

    query_tokens = {
        _stem(t)
        for t in _tokenize(query)
    }

    expanded_tokens = {
        _stem(t)
        for t in _tokenize(query_to_embed)
    }

    for doc_text, meta, distance in zip(
        docs,
        metas,
        dists,
    ):

        if not doc_text:
            continue

        semantic_score = np.exp(-distance)

        section_title = meta.get(
            "section_title",
            ""
        ).lower()

        section_tokens = {
            _stem(t)
            for t in _tokenize(section_title)
        }

        raw_overlap_tokens = (
            query_tokens & section_tokens
        ) - _TITLE_OVERLAP_STOPWORDS

        raw_overlap = len(
            raw_overlap_tokens
        )

        expanded_overlap_tokens = (
            expanded_tokens & section_tokens
        ) - _TITLE_OVERLAP_STOPWORDS

        expanded_overlap = len(
            expanded_overlap_tokens
        )

        if raw_overlap >= 3:
            section_bonus = 0.18
        elif raw_overlap == 2:
            section_bonus = 0.12
        elif raw_overlap == 1:
            section_bonus = 0.06
        elif expanded_overlap >= 3:
            section_bonus = 0.10
        elif expanded_overlap == 2:
            section_bonus = 0.06
        elif expanded_overlap == 1:
            section_bonus = 0.02
        else:
            section_bonus = 0.0

        category_hint = (
            category_filter
            or context.category
        )

        category_bonus = (
            0.10
            if category_hint
            and meta.get("category")
            == category_hint
            else 0.0
        )

        act_name_lower = meta.get(
            "act_name",
            ""
        ).lower()

        query_act_bonus = (
            0.15
            if any(
                qa in act_name_lower
                or act_name_lower in qa
                for qa in query_act_lower
            )
            else 0.0
        )

        anchor_tier = _anchor_tier(
            primary_anchor_keys,
            secondary_anchor_keys,
            meta.get("act_name", ""),
            meta.get("section_number", ""),
        )

        anchor_bonus = (
            0.25
            if anchor_tier == "primary"
            else 0.12
            if anchor_tier == "secondary"
            else 0.0
        )

        doc_id = int(
            meta.get("doc_id", -1)
        )

        if doc_id == -1:
            continue

        bm25_score = 0.0
        pos = (
            _bm25_doc_pos.get(doc_id)
            if _bm25_doc_pos is not None
            else None
        )

        if pos is not None:
            bm25_score = float(
                bm25_scores[pos]
            )

        if raw_overlap > 0:
            bm25_score *= 1.2

        bm25_norm = (
            bm25_score - bm25_mean
        ) / bm25_std

        bm25_norm_sigmoid = (
            1 / (1 + np.exp(-bm25_norm))
        )

        title_key = (
            meta.get("act_name", ""),
            meta.get("section_number", ""),
        )

        title_bm25_score = 0.0
        title_pos = (
            _title_bm25_pos.get(title_key)
            if _title_bm25_pos is not None
            else None
        )

        if title_pos is not None:
            title_bm25_score = float(
                title_bm25_scores[title_pos]
            )

        title_bm25_norm = (
            title_bm25_score
            - title_bm25_mean
        ) / title_bm25_std

        title_bm25_sigmoid = (
            1 / (1 + np.exp(-title_bm25_norm))
        )

        title_bm25_bonus = (
            0.40
            * (title_bm25_sigmoid - 0.5)
        )

        base_score = (
            0.50 * semantic_score
            + 0.50 * bm25_norm_sigmoid
            + category_bonus
            + section_bonus
            + query_act_bonus
            + title_bm25_bonus
            + anchor_bonus
        )

        results.append({
            "text": doc_text,
            "chunk_id": meta["chunk_id"],
            "citation": meta.get(
                "citation",
                "Unknown",
            ),
            "section_number": meta.get(
                "section_number",
                "",
            ),
            "section_title": meta.get(
                "section_title",
                "",
            ),
            "chapter": meta.get(
                "chapter",
                "",
            ),
            "act_name": meta.get(
                "act_name",
                "",
            ),
            "short_name": meta.get(
                "short_name",
                "",
            ),
            "year": meta.get(
                "year",
                0,
            ),
            "category": meta.get(
                "category",
                "",
            ),
            "source": meta.get(
                "source",
                "",
            ),
            "semantic_score": round(
                semantic_score,
                4,
            ),
            "bm25_score": round(
                bm25_score,
                4,
            ),
            "score": base_score,
        })

    results.sort(
        key=lambda x: x["score"],
        reverse=True,
    )

    mark("scoring + sort")

    results = dedupe_by_section(
        results
    )

    # Keep an 80-candidate reranker pool (50 missed several just-below
    # the cutoff correct sections — recall failures).
    results_full = results
    results = results[:80]

    # Pool guarantee: curated anchor sections must always enter the
    # reranker pool even when the base retrieval score ranks them lower
    # than the 80th cutoff (e.g. definitional sections with long,
    # multi-topic text that the dense model under-ranks).
    if anchor_keys:
        in_pool = {
            (r["act_name"], str(r["section_number"]))
            for r in results
        }

        for r in results_full:
            key = (
                r["act_name"],
                str(r["section_number"]),
            )

            if key in in_pool:
                continue

            if _anchor_tier(
                primary_anchor_keys,
                secondary_anchor_keys,
                r["act_name"],
                r["section_number"],
            ):
                results.append(r)
                in_pool.add(key)

    print(
        "\nTop retrieval scores before rerank:"
    )

    for r in results[:20]:
        print(
            f"{r['score']:.4f}",
            r["act_name"],
            r["section_number"],
            r["section_title"],
        )

    # Free the embedder so the cross-encoder gets the whole GPU (larger
    # batches, no OOM->CPU fallback), then restore it for the next query.
    free_gpu_for_rerank()

    try:
        ranked = rerank(
            query,
            results,
            primary_anchor_keys=primary_anchor_keys,
            secondary_anchor_keys=secondary_anchor_keys,
        )
    finally:
        restore_embedder()

    mark("rerank")

    print("\nReranker scores:")

    for r in ranked:
        print(
            f"{r['final_score']:.4f}",
            f"rr={r['rerank_score']:.4f}",
            f"ret={r['score']:.4f}",
            r["citation"],
            r["section_title"],
        )

    ranked = dedupe_by_section(
        ranked,
        key_fn=lambda r: (
            r["act_name"],
            r["section_number"],
        ),
    )

    ranked.sort(
        key=lambda x: x["final_score"],
        reverse=True,
    )

    ranked = ranked[:top_k]

    print("\nFinal Retrieval Results")

    for r in ranked:
        print(
            f"{r['final_score']:.4f}",
            r["citation"],
            r["section_title"],
        )

    return {
        "context": context,
        "chroma": chroma_results,
        "results": ranked,
    }