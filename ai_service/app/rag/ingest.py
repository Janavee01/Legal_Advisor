#ingest.py
import json
import pickle
import logging
import argparse
import os
from pathlib import Path
from rank_bm25 import BM25Okapi
from .tagger import extract_topics
from .chunker import chunk_sections
from .vectordb import get_collection
from .parser import ACT_METADATA
from .embedder import get_model
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parents[3]
PARSED_DIR = BASE_DIR / "datasets" / "parsed"
DATA_DIR = BASE_DIR / "ai_service" / "app" / "data"

VECTOR_STORE_PATH = DATA_DIR / "vector_store.pkl"
INGESTED_LOG_PATH = DATA_DIR / "ingested_files.json"

DATA_DIR.mkdir(parents=True, exist_ok=True)
DOC_PREFIX = "[LEGAL_DOC]"
EMBED_CACHE_PATH = DATA_DIR / "embedding_cache.pkl"

# ───────────────────────────────
# Helpers
# ───────────────────────────────
def load_embedding_cache():
    if EMBED_CACHE_PATH.exists():
        with open(EMBED_CACHE_PATH, "rb") as f:
            return pickle.load(f)
    return {}


def save_embedding_cache(cache):
    with open(EMBED_CACHE_PATH, "wb") as f:
        pickle.dump(cache, f)
        
def load_ingested_log() -> set:
    if INGESTED_LOG_PATH.exists():
        with open(INGESTED_LOG_PATH) as f:
            return set(json.load(f))
    return set()


def save_ingested_log(ingested: set):
    with open(INGESTED_LOG_PATH, "w") as f:
        json.dump(sorted(ingested), f, indent=2)


def load_existing_pickle() -> list:
    if VECTOR_STORE_PATH.exists():
        with open(VECTOR_STORE_PATH, "rb") as f:
            return pickle.load(f)
    return []


def save_pickle(documents: list):
    with open(VECTOR_STORE_PATH, "wb") as f:
        pickle.dump(documents, f)
    log.info("Saved pickle store: %d docs", len(documents))


def tokenize(text: str):
    import re
    return re.findall(r"[a-zA-Z0-9]+", text.lower())


# ───────────────────────────────
# Model (GLOBAL - IMPORTANT FIX)
# ───────────────────────────────

model = get_model()

def ingest_file(json_path, category, act_metadata, collection, doc_id_start,cache):

    with open(json_path, encoding="utf-8") as f:
        sections = json.load(f)

    for s in sections:
        s["category"] = category
        s["source"] = json_path.name
        s["short_name"] = act_metadata.get("short_name", "")
        s["act_name"] = act_metadata.get("act_name", "")
        s["year"] = act_metadata.get("year", 0)
        s.setdefault("topics", act_metadata.get("relevance", []))

    chunks = chunk_sections(sections)

    if not chunks:
        return [], doc_id_start

    LOW_VALUE_SECTIONS = [
        "power to make rules",
        "repeal",
        "repeals",
        "power to remove difficulties",
        "delegation of powers",
    ]

    filtered_chunks = []

    for chunk in chunks:
        title = chunk["section_title"].lower()

        if any(x in title for x in LOW_VALUE_SECTIONS):
            continue

        filtered_chunks.append(chunk)

    if not filtered_chunks:
        return [], doc_id_start

    texts = [
        f"Act: {c['act_name']}\n"
        f"Chapter: {c.get('chapter', '')}\n"
        f"Section: {c['section_title']}\n\n"
        f"{c['text']}"
        for c in filtered_chunks
    ]
    
   

    new_texts = []
    new_chunks = []
    

    for i, chunk in enumerate(filtered_chunks):
        cid = chunk["chunk_id"]

        if cid not in cache:
            new_texts.append(texts[i])
            new_chunks.append(chunk)

    if new_texts:
        new_embeddings = model.encode(
            new_texts,
            batch_size=8,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=True
        ).tolist()
    else:
        new_embeddings = []

    # store new embeddings into cache
    for chunk, emb in zip(new_chunks, new_embeddings):
        cache[chunk["chunk_id"]] = emb

    save_embedding_cache(cache)

    ids = []
    documents = []
    metadatas = []
    new_docs = []
    embeddings = []
    doc_id = doc_id_start

    for chunk in filtered_chunks:

        cid = chunk["chunk_id"]

        # skip if not newly embedded
        if cid not in cache:
            continue

        embedding = cache[cid]
        embeddings.append(embedding)
        topics = extract_topics(chunk["text"]) or ["general"]

        ids.append(cid)
        documents.append(chunk["text"])

        metadatas.append({
            "doc_id": doc_id,
            "citation": chunk["citation"],
            "section_number": chunk["section_number"],
            "section_title": chunk["section_title"],
            "chapter": chunk.get("chapter", ""),
            "act_name": chunk["act_name"],
            "topics": ", ".join(topics),
            "short_name": chunk["short_name"],
            "year": chunk["year"],
            "category": chunk["category"],
            "source": chunk["source"],
            "chunk_index": chunk["chunk_index"],
            "total_chunks": chunk["total_chunks"],
            "chunk_id": cid,
        })

        new_docs.append({
            "id": doc_id,
            "text": chunk["text"],
            "citation": chunk["citation"],
            "chunk_id": cid,
            "topics": topics,
            "section_number": chunk["section_number"],
            "section_title": chunk["section_title"],
            "chapter": chunk.get("chapter", ""),
            "act_name": chunk["act_name"],
            "short_name": chunk["short_name"],
            "year": chunk["year"],
            "category": chunk["category"],
            "source": chunk["source"],
        })

        doc_id += 1

        
    collection.add(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas
    )

    return new_docs, doc_id

# ───────────────────────────────
# Main run
# ───────────────────────────────

def run(reset: bool = False):

    if not PARSED_DIR.exists():
        log.error("Parsed directory missing")
        return

    json_files = list(PARSED_DIR.rglob("*.json"))
    collection = get_collection(reset=reset)

    ingested_log = set() if reset else load_ingested_log()
    existing_docs = [] if reset else load_existing_pickle()

    doc_id = max((d["id"] for d in existing_docs), default=-1) + 1

    cache = load_embedding_cache()
    total_new_docs = []
    skipped = []

    for json_path in sorted(json_files):

        category = json_path.parent.name
        stem = json_path.stem

        act_metadata = ACT_METADATA.get(stem)
        if act_metadata is None:
            act_metadata = {
                "act_name": stem.replace("_", " ").title(),
                "short_name": stem[:10],
                "year": 0,
                "relevance": []
            }

        key = f"{category}/{json_path.name}:v1"

        if key in ingested_log:
            log.info("Skipping: %s", key)
            skipped.append(key)
            continue

        log.info("Ingesting: %s [%s]", json_path.name, category)

        try:
            new_docs, doc_id = ingest_file(
                json_path,
                category,
                act_metadata,
                collection,
                doc_id,
                cache
            )

            total_new_docs.extend(new_docs)
            ingested_log.add(key)

        except Exception as e:
            log.error("Failed: %s", e)
            raise

    all_docs = existing_docs + total_new_docs

    # BM25 rebuild
    tokens = [tokenize(d["text"]) for d in all_docs]

    bm25_store = {
        "tokenized_corpus": tokens,
        "documents": [{"doc_id": d["id"]} for d in all_docs]
    }

    with open(DATA_DIR / "bm25.pkl", "wb") as f:
        pickle.dump(bm25_store, f)

    save_pickle(all_docs)
    save_ingested_log(ingested_log)

    print("\n── Ingestion Summary ─────────────────────────")
    print("New chunks :", len(total_new_docs))
    print("Skipped    :", len(skipped))
    print("Total      :", len(all_docs))
    print("CHROMA     :", collection.count())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true")
    args = parser.parse_args()
    run(reset=args.reset)