import json
import numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer


BASE_DIR = Path(__file__).resolve().parents[3]
INTENT_PATH = BASE_DIR / "ai_service" / "app" / "rag" / "intent_index.json"


class LegalIntentExpander:
    def __init__(self):
        self.model = SentenceTransformer(
            "BAAI/bge-base-en-v1.5",
            device="cpu"
        )

        with open(INTENT_PATH, "r") as f:
            self.intents = json.load(f)

        self._build_index()

    def _build_index(self):
        texts = [
            " ".join(i.get("examples", []))
            for i in self.intents
        ]

        self.intent_embeddings = np.array(
            self.model.encode(
                texts,
                batch_size=16,
                normalize_embeddings=True
            ),
            dtype=np.float32
        )

    def expand(self, query: str):
        query_vec = np.array(
            self.model.encode(query, normalize_embeddings=True),
            dtype=np.float32
        )

        scores = self.intent_embeddings @ query_vec

        best_idx = int(np.argmax(scores))
        best_intent = self.intents[best_idx]

        return {
            "intent": best_intent["intent"],
            "anchors": best_intent["anchors"],
            "confidence": float(scores[best_idx]),
            "expanded_queries": [
                query,
                *best_intent.get("examples", []),
                best_intent["intent"].replace("_", " ")
            ]
        }