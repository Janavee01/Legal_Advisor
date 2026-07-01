#ingest.py
import json
import pickle
import logging
import argparse
import os
import hashlib
from pathlib import Path
from rank_bm25 import BM25Okapi
from .tagger import extract_topics
from .chunker import chunk_sections
from .vectordb import get_collection
from .parser import ACT_METADATA
from .embedder import get_model
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)
from concurrent.futures import ThreadPoolExecutor
BASE_DIR = Path(__file__).resolve().parents[3]
PARSED_DIR = BASE_DIR / "datasets" / "parsed"
DATA_DIR = BASE_DIR / "ai_service" / "app" / "data"
from itertools import islice
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

def file_hash(path):
    with open(path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()

def prepare_chunk(chunk):
    cid = chunk["chunk_id"]
    text = build_search_text(chunk)
    return cid, text, chunk

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

def build_search_text(chunk):
    return f"""
{chunk['act_name']}
{chunk['section_number']} {chunk['section_title']}
{chunk['chapter']}

{chunk['text']}
""".strip()

LOW_VALUE_SECTIONS = [
    "power to make rules",
    "repeal",
    "repeals",
    "power to remove difficulties",
    "delegation of powers",
]

# ───────────────────────────────
# Model (GLOBAL - IMPORTANT FIX)
# ───────────────────────────────

model = get_model()
model.eval()

def ingest_file(json_path, category, act_metadata, collection, doc_id_start, cache):
    doc_id = doc_id_start 

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

    filtered_chunks = []

    for chunk in chunks:
        title = chunk["section_title"].lower()

        if any(x in title for x in LOW_VALUE_SECTIONS):
            continue

        filtered_chunks.append(chunk)

    if not filtered_chunks:
        return [], doc_id_start

    save_embedding_cache(cache)

    ids = []
    documents = []
    metadatas = []
    new_docs = []
    embeddings = []
    

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

        
    

    return new_docs, doc_id, filtered_chunks

# ───────────────────────────────
# Main run
# ───────────────────────────────

def run(reset: bool = False):
    all_new_texts = []
    all_new_chunks = []
    all_new_docs = []
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

        file_key = f"{category}/{json_path.name}"
        file_hash_value = file_hash(json_path)
        
        key = f"{file_key}:{file_hash_value}"

        if key in ingested_log:
            log.info("Skipping: %s", key)
            skipped.append(key)
            continue

        log.info("Ingesting: %s [%s]", json_path.name, category)

        try:
            new_docs, doc_id, chunks = ingest_file(
                json_path,
                category,
                act_metadata,
                collection,
                doc_id,
                cache
            )

            all_new_docs.extend(new_docs)
            all_new_chunks.extend(chunks)
    
            total_new_docs.extend(new_docs)
            ingested_log.add(key)

            

        except Exception as e:
            log.error("Failed: %s", e)
            raise

    texts_to_embed = []
    chunks_to_embed = []

    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(prepare_chunk, all_new_chunks))
    log.info("Encoding %d chunks...", len(texts_to_embed))
    for cid, text, chunk in [(r[0], r[1], r[2]) for r in results]:
        if cid in cache:
            continue

        texts_to_embed.append(text)
        chunks_to_embed.append(chunk)
    log.info("Encoding %d chunks...", len(texts_to_embed))
    # ---- SAFE BATCHING ----
    BATCH_SIZE = 64

    for i in range(0, len(texts_to_embed), BATCH_SIZE):
        batch_texts = texts_to_embed[i:i+BATCH_SIZE]
        batch_chunks = chunks_to_embed[i:i+BATCH_SIZE]
        log.info("Batch %d/%d", i//BATCH_SIZE + 1, (len(texts_to_embed)+BATCH_SIZE-1)//BATCH_SIZE)
        embeddings = model.encode(
            batch_texts,
            batch_size=32,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False
        ).tolist()

        for c, emb in zip(batch_chunks, embeddings):
            cache[c["chunk_id"]] = emb

    save_embedding_cache(cache)
    

    BATCH_SIZE = 256

    safe_ids = []
    documents = []
    embeddings = []
    metadatas = []


    for chunk in all_new_chunks:
        cid = chunk["chunk_id"]

        if cid not in cache:
            continue

        safe_id = f"{chunk['category']}::{cid}"

        safe_ids.append(safe_id)
        documents.append(chunk["text"])
        embeddings.append(cache[cid])

        topics = extract_topics(chunk["text"]) or ["general"]

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

        doc_id += 1
        
    log.info("Writing to vector DB: %d items", len(safe_ids))
    # ---- SAFE BATCH INSERT ----
    for i in range(0, len(safe_ids), BATCH_SIZE):
        collection.add(
            ids=safe_ids[i:i+BATCH_SIZE],
            documents=documents[i:i+BATCH_SIZE],
            embeddings=embeddings[i:i+BATCH_SIZE],
            metadatas=metadatas[i:i+BATCH_SIZE],
        )

        
    all_docs = existing_docs + total_new_docs

    # BM25 rebuild
    tokens = [tokenize(build_search_text(d)) for d in all_docs]

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