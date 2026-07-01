"""
intent_expander.py — Maps a user query to known legal intents.

Loads intent_index.json at startup, builds embeddings once, then scores
each query against all intents using cosine similarity.

Returns the top-2 intents that score within 85% of the best score,
with their anchors (Act + Section references) and example queries.
"""

import json
import numpy as np
from pathlib import Path
from ai_service.app.rag.embedder import get_model
from ai_service.app.retrieval.semantic_router import semantic_route
BASE_DIR = Path(__file__).resolve().parents[3]
INTENT_PATH = BASE_DIR / "ai_service" / "app" / "rag" / "intent_index.json"

QUERY_PREFIX = "Represent this query for retrieving relevant legal passages: "
ROUTER_CONFIDENCE = 0.50

class LegalIntentExpander:

    def __init__(self):
        self.model = get_model()

        with open(INTENT_PATH, "r") as f:
            self.intents = json.load(f)

        self._build_index()

    def _build_index(self):
        """
        Pre-compute one embedding per intent by combining:
            - example queries (the primary signal)
            - anchors (Act + Section references)
            - the intent name itself

        Using the query prefix keeps the embedding space consistent
        with how we encode user queries at retrieval time.
        """
        texts = [
            QUERY_PREFIX + " ".join(
            i.get("examples", [])
            + i.get("anchors", [])
            + [i.get("prototype", "")]
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

    def expand(self, query: str) -> dict:
        """
        Score the query against all intents and return top matches.

        Returns:
            {
                "matched_intents": [
                    {
                        "intent": "maternity_leave",
                        "score": 0.87,
                        "anchors": [...],
                        "examples": [...]
                    },
                    ...
                ]
            }

        Logic:
            1. Encode the query with the same prefix used during indexing.
            2. Score all intents via dot product (embeddings are normalised,
               so this is cosine similarity).
            3. Collect all intents within 85% of the top score.
            4. Return the top-2 by score.

        The 85% threshold keeps closely-related intents (e.g. bail + FIR)
        while excluding unrelated ones. Top-2 cap prevents anchor bloat
        that pushes the query embedding in conflicting directions.
        """

        route = semantic_route(query)

        predicted_category = route["category"]
        confidence = route["confidence"]
        print(predicted_category, confidence)

        # Use only intents from the predicted category if the router is confident.
        if predicted_category and confidence >= ROUTER_CONFIDENCE:
            candidate_indices = [
                i for i, intent in enumerate(self.intents)
                if intent.get("category") == predicted_category
            ]
        else:
            candidate_indices = list(range(len(self.intents)))

        print("Candidate intents:")
        for i in candidate_indices:
            print("-", self.intents[i]["intent"])

        query_vec = self.model.encode(
            QUERY_PREFIX + query,
            normalize_embeddings=True
        )

        candidate_embeddings = self.intent_embeddings[candidate_indices]

        scores = candidate_embeddings @ query_vec

        top_local_indices = np.argsort(scores)[::-1]

        best_score = float(scores[top_local_indices[0]])
        
        # Collect ALL intents above threshold first, THEN truncate to top-2.
        # The old code interleaved truncation with collection, causing
        # non-deterministic results depending on loop iteration order.
        candidates = []
        MIN_SCORE = 0.50 
        SECONDARY_GAP = 0.05

        for local_idx in top_local_indices:
            
            score = float(scores[local_idx])
            if score < MIN_SCORE:
                continue

            if best_score - score > SECONDARY_GAP:
                break
            
            original_idx = candidate_indices[local_idx]

            candidates.append({
                "intent": self.intents[original_idx]["intent"],
                "score": score,
                "anchors": self.intents[original_idx].get("anchors", []),
                "examples": self.intents[original_idx].get("examples", [])
            })
        
        matched_intents = candidates[:2]

        for local_idx in top_local_indices[:10]:
            original_idx = candidate_indices[local_idx]
            print(
                self.intents[original_idx]["intent"],
                round(float(scores[local_idx]), 4)
            )

        # Sort by score (already sorted, but explicit for clarity) and cap at 2
        
        print("\nMatched intents:")
        for m in matched_intents:
            print(f"{m['intent']} ({m['score']:.4f})")
        return {"matched_intents": matched_intents,
                "category": predicted_category,
                "confidence": confidence}
    

#def main():
#    expander = LegalIntentExpander()
#
#    queries = [
#      #  "wife harassed by husband",
#      #  "shopkeeper selling above mrp",
#      #  "how to file rti",
#      #  "employee not paid salary",
#       # "husband asking for dowry",
#       # "boss touching me at office",
#        "fake shopping website took my money",
#        #"tenant not getting security deposit",
#        #"cyber fraud through UPI",
#        #"divorce due to cruelty",
#        #"child sexually abused"
#        "amazon delivered the wrong product",
#        "i paid through a fake website and lost 5000"
#    ]
#
#    for query in queries:
#        print(f"\nQuery: {query}")
#        expander.expand(query)
#
#
#if __name__ == "__main__":
#    main()