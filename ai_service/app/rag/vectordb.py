import chromadb
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[3]

CHROMA_DIR = (
    BASE_DIR
    / "ai_service"
    / "app"
    / "data"
    / "chroma"
)

CHROMA_DIR.mkdir(
    parents=True,
    exist_ok=True
)

client = chromadb.PersistentClient(path=str(CHROMA_DIR))

_collection = None
COLLECTION_NAME = "nyaya_legal_knowledge"


def get_collection(reset=False):
    global _collection

    if reset:
        try:
            client.delete_collection(COLLECTION_NAME)
        except Exception:
            pass
        _collection = None

    if _collection is None:
        _collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"description": "Nyaya legal knowledge base"},
        )

    return _collection