import json
import numpy as np
from pathlib import Path
from ai_service.app.rag.embedder import get_model



BASE_DIR = Path(__file__).resolve().parents[3]
INTENT_PATH = BASE_DIR / "ai_service" / "app" / "rag" / "intent_index.json"


class LegalIntentExpander:
    def __init__(self):
        self.model = get_model()
       

        with open(INTENT_PATH, "r") as f:
            self.intents = json.load(f)

        self._build_index()

    def _build_index(self):
        texts = [
    " ".join(
        i.get("examples", [])
        + i.get("anchors", [])
        + [i.get("intent", "").replace("_", " ")]
    )
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

        top_k = 3

        top_indices = np.argsort(scores)[::-1][:top_k]

        best_score = float(scores[top_indices[0]])
        matched_intents = []

        for idx in top_indices:
            score = float(scores[idx])
        
            if len(matched_intents) > 1:
                matched_intents = sorted(matched_intents, key=lambda x: x["score"], reverse=True)
                matched_intents = matched_intents[:2]
            
            if score < best_score * 0.85:
                continue
            
            matched_intents.append({
                "intent": self.intents[idx]["intent"],
                "score": score,
                "anchors": self.intents[idx].get("anchors", []),
                "examples": self.intents[idx].get("examples", [])
            })
        
        
        return {
            "matched_intents": matched_intents
        }