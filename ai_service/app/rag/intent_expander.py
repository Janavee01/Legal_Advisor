import json
from pathlib import Path
from sentence_transformers import SentenceTransformer
import numpy as np


BASE_DIR = Path(__file__).resolve().parents[3]
INTENT_PATH = BASE_DIR / "ai_service" / "app" / "rag" / "intent_index.json"


class LegalIntentExpander:
    def __init__(self):
        self.model = SentenceTransformer("BAAI/bge-base-en-v1.5")

        with open(INTENT_PATH, "r") as f:
            self.intents = json.load(f)

        self.intent_embeddings = []
        self._build_index()

    def _build_index(self):
        texts = []

        for intent in self.intents:
            # combine examples into one embedding anchor
            combined = " ".join(intent.get("examples", []))
            texts.append(combined)

        self.intent_embeddings = self.model.encode(
            texts,
            normalize_embeddings=True
        )

    def expand(self, query: str):
        query_vec = self.model.encode(
            query,
            normalize_embeddings=True
        )

        scores = np.dot(self.intent_embeddings, query_vec)

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