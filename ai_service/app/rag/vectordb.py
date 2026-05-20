"""
vectordb.py — ChromaDB collection manager for Nyaya.

Responsibilities:
- initialize persistent Chroma client
- create/access collection
- support reset mode
"""

import chromadb
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[3]
CHROMA_DIR = BASE_DIR / "ai-service" / "app" / "data" / "chroma"

client = chromadb.PersistentClient(path=str(CHROMA_DIR))

COLLECTION_NAME = "nyaya_legal_knowledge"


def get_collection(reset: bool = False):
    if reset:
        try:
            client.delete_collection(COLLECTION_NAME)
        except Exception:
            pass

    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"description": "Nyaya legal knowledge base"}
    )