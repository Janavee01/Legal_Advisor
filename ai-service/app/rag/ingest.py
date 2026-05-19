"""
ingest.py — Ingests parsed legal Act sections into the vector store.

Pipeline:
    datasets/parsed/<category>/<act>.json
        → chunker.chunk_sections()
        → embedder.get_embedding()
        → Chroma (primary store, used for retrieval)
        → vector_store.pkl (backup, used by retrieve.py fallback)

Run:
    python ingest.py            # ingest all parsed JSONs
    python ingest.py --reset    # wipe Chroma and re-ingest from scratch
"""

import json
import pickle
import logging
import argparse
from pathlib import Path

from embedder import get_embedding
from vectordb import get_collection
from chunker import chunk_sections

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parents[3]
PARSED_DIR = BASE_DIR / "datasets" / "parsed"
DATA_DIR = BASE_DIR / "ai-service" / "app" / "data"
VECTOR_STORE_PATH = DATA_DIR / "vector_store.pkl"
INGESTED_LOG_PATH = DATA_DIR / "ingested_files.json"  # tracks what's already been ingested

DATA_DIR.mkdir(parents=True, exist_ok=True)


def load_ingested_log() -> set:
    """Return set of already-ingested filenames (for incremental ingestion)."""
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
    log.info("Saved pickle store: %d total documents", len(documents))


def ingest_file(json_path: Path, category: str, collection, existing_docs: list, doc_id_start: int) -> tuple[list, int]:
    """
    Ingest a single parsed JSON file.
    Returns (new_documents, next_doc_id).
    """
    with open(json_path, encoding="utf-8") as f:
        sections = json.load(f)

    # Attach category and source to each section before chunking
    for s in sections:
        s["category"] = category
        s["source"] = json_path.name

    chunks = chunk_sections(sections)
    log.info("  %s → %d sections → %d chunks", json_path.name, len(sections), len(chunks))

    new_docs = []
    doc_id = doc_id_start

    for chunk in chunks:
        embedding = get_embedding(chunk["text"])

        # ── Store in Chroma ───────────────────────────────────────────────
        # Chroma metadata values must be str/int/float — no lists
        collection.add(
            ids=[str(doc_id)],
            documents=[chunk["text"]],
            embeddings=[embedding],
            metadatas=[{
                "citation":       chunk["citation"],
                "section_number": chunk["section_number"],
                "section_title":  chunk["section_title"],
                "chapter":        chunk["chapter"],
                "act_name":       chunk["act_name"],
                "short_name":     chunk["short_name"],
                "year":           chunk["year"],
                "category":       chunk["category"],
                "source":         chunk["source"],
                "chunk_index":    chunk["chunk_index"],
                "total_chunks":   chunk["total_chunks"],
            }]
        )

        # ── Store in pickle (mirrors Chroma for retrieve.py) ──────────────
        new_docs.append({
            "id":             doc_id,
            "text":           chunk["text"],
            "embedding":      embedding,
            "citation":       chunk["citation"],
            "section_number": chunk["section_number"],
            "section_title":  chunk["section_title"],
            "chapter":        chunk["chapter"],
            "act_name":       chunk["act_name"],
            "short_name":     chunk["short_name"],
            "year":           chunk["year"],
            "category":       chunk["category"],
            "source":         chunk["source"],
        })

        doc_id += 1

    return new_docs, doc_id


def run(reset: bool = False):
    if not PARSED_DIR.exists():
        log.error("Parsed directory not found: %s", PARSED_DIR)
        log.error("Run parser.py first.")
        return

    json_files = list(PARSED_DIR.rglob("*.json"))
    if not json_files:
        log.error("No parsed JSON files found in %s", PARSED_DIR)
        return

    collection = get_collection(reset=reset)

    ingested_log = set() if reset else load_ingested_log()
    existing_docs = [] if reset else load_existing_pickle()
    doc_id = max((d["id"] for d in existing_docs), default=-1) + 1

    total_new_docs = []
    skipped = []

    for json_path in sorted(json_files):
        category = json_path.parent.name
        key = f"{category}/{json_path.name}"

        if key in ingested_log:
            log.info("Skipping (already ingested): %s", key)
            skipped.append(key)
            continue

        log.info("\nIngesting: %s [%s]", json_path.name, category)
        try:
            new_docs, doc_id = ingest_file(json_path, category, collection, existing_docs, doc_id)
            total_new_docs.extend(new_docs)
            ingested_log.add(key)
        except Exception as e:
            log.error("Failed to ingest %s: %s", json_path.name, e)
            raise

    # Persist
    all_docs = existing_docs + total_new_docs
    save_pickle(all_docs)
    save_ingested_log(ingested_log)

    print("\n── Ingestion Summary ─────────────────────────")
    print(f"  New chunks ingested : {len(total_new_docs)}")
    print(f"  Skipped (cached)    : {len(skipped)}")
    print(f"  Total in store      : {len(all_docs)}")
    print("──────────────────────────────────────────────")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true", help="Wipe Chroma and re-ingest everything")
    args = parser.parse_args()
    run(reset=args.reset)