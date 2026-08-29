"""
query_context_builder.py — Builds a RetrievalContext from a raw user query.

All mappings are derived at runtime from existing config files:
    - intent_index.json       : intent → examples and category
    - category_prototypes.py  : category → description text
    - semantic_router         : query → best category (confidence-gated)
    - intent_expander         : query → matched intents

No hardcoded intent→category or keyword→intent mappings.
"""

import json
import numpy as np
from pathlib import Path

from ai_service.app.retrieval.query_router import detect_intents
from ai_service.app.rag.intent_expander import LegalIntentExpander
from ai_service.app.rag.embedder import get_model
from ai_service.app.rag.category_prototypes import CATEGORY_PROTOTYPES
from .retrieval_context import RetrievalContext

from functools import lru_cache

@lru_cache(maxsize=1)
def get_query_context_builder():
    return QueryContextBuilder()

from .intent_expander import get_intent_expander

BASE_DIR = Path(__file__).resolve().parents[3]
INTENT_PATH = BASE_DIR / "ai_service" / "app" / "rag" / "intent_index.json"

# Minimum cosine similarity for an intent to be mapped to a category
INTENT_CATEGORY_THRESHOLD = 0.45

# Minimum margin over second-best category to avoid ambiguous mapping
INTENT_CATEGORY_MARGIN = 0.03

# If a co-firing intent's direct query similarity is below this fraction
# of the best-matching intent, it's a false co-match and gets dropped
CONFLICT_DROP_THRESHOLD = 0.85

@lru_cache(maxsize=1)
def get_intent_category_map():
    model = get_model()

    with open(INTENT_PATH) as f:
        intents = json.load(f)

    return _build_intent_to_category_map(
        model,
        intents
    )


@lru_cache(maxsize=1)
def get_conflict_resolver():
    model = get_model()

    with open(INTENT_PATH) as f:
        intents = json.load(f)

    return ConflictResolver(model, intents)

def _build_intent_to_category_map(model, intents: list[dict]) -> dict[str, str]:
    """
    Dynamically map each intent to its most likely category by embedding
    each intent's example text and comparing against category prototypes.

    Adding a new intent to intent_index.json → auto-mapped on next startup.
    Adding a new category to category_prototypes.py → auto-considered.
    No dict to manually maintain.
    """
    category_names = list(CATEGORY_PROTOTYPES.keys())
    category_texts = list(CATEGORY_PROTOTYPES.values())

    category_embeddings = np.array(
        model.encode(category_texts, normalize_embeddings=True),
        dtype=np.float32
    )

    intent_to_category = {}

    for intent in intents:
        name = intent.get("intent", "")
        representation = " ".join(
            intent.get("examples", [])
            + [name.replace("_", " ")]
        )

        if not representation.strip():
            continue

        intent_vec = model.encode(representation, normalize_embeddings=True)
        scores = category_embeddings @ intent_vec

        sorted_scores = np.sort(scores)[::-1]
        best_idx = int(np.argmax(scores))
        best_score = float(sorted_scores[0])
        second_score = float(sorted_scores[1]) if len(sorted_scores) > 1 else 0.0
        margin = best_score - second_score

        if best_score >= INTENT_CATEGORY_THRESHOLD and margin >= INTENT_CATEGORY_MARGIN:
            intent_to_category[name] = category_names[best_idx]

    return intent_to_category


class ConflictResolver:
    """
    Resolves false co-matches: two intents that both score above the
    LegalIntentExpander threshold but only one is actually relevant
    given the specific query.

    Uses direct query-vs-intent cosine similarity at request time,
    which is more precise than the index-time score used during expansion.
    """

    def __init__(self, model, intents: list[dict]):
        self.model = model

        intent_texts = {
            i["intent"]: " ".join(
                i.get("examples", [])
                + [i["intent"].replace("_", " ")]
            )
            for i in intents
        }

        names = list(intent_texts.keys())
        vecs = model.encode(list(intent_texts.values()), normalize_embeddings=True)
        self.intent_vecs = dict(zip(names, vecs))

    def resolve(self, query: str, matched_intents: list[dict]) -> list[dict]:
        if len(matched_intents) <= 1:
            return matched_intents

        query_vec = self.model.encode(query, normalize_embeddings=True)

        query_scores = {
            i["intent"]: float(
                np.dot(query_vec, self.intent_vecs[i["intent"]])
                if i["intent"] in self.intent_vecs
                else i.get("score", 0.0)
            )
            for i in matched_intents
        }

        best = max(query_scores.values())
        filtered = [
            i for i in matched_intents
            if query_scores.get(i["intent"], 0.0) >= best * CONFLICT_DROP_THRESHOLD
        ]

        return filtered if filtered else matched_intents[:1]


class QueryContextBuilder:

    def __init__(self):
        self.expander = get_intent_expander()
        self.model = get_model()

        with open(INTENT_PATH, "r") as f:
            self.intents = json.load(f)
        
        self._intent_to_category = get_intent_category_map()
        self._conflict_resolver = get_conflict_resolver()

    def build(self, query: str) -> RetrievalContext:

        routing = detect_intents(query)

        expanded = self.expander.match_intents(
            query,
            category=routing.get("category"),
            router_confidence=routing.get("confidence", 0.0)
        )

        matched_intents = expanded.get("matched_intents", [])

        matched_intents = self._conflict_resolver.resolve(query, matched_intents)

        matched_intents = sorted(
            matched_intents,
            key=lambda x: x["score"],
            reverse=True
        )
                            
        intent_names = list(dict.fromkeys(
            i["intent"] for i in matched_intents
        ))

        print("ROUTING:", routing)
        print("EXPANDED:", expanded)
        print("AFTER RESOLVER:", matched_intents)
        print("FINAL INTENTS:", intent_names)

        parts = [query]

        for idx, intent in enumerate(matched_intents):
            parts.append(intent["intent"].replace("_", " "))
            # Primary intent gets its prototype (curated legal vocabulary) and
            # full examples; secondary intents get at most 1 example to prevent
            # query pollution with unrelated terms.
            max_examples = 2 if idx == 0 else 1
            if idx == 0:
                parts.append(intent.get("prototype", ""))
            parts.extend(intent.get("examples", [])[:max_examples])
        
        expanded_query = " ".join(parts)

        intent_confidence = max(
            (i["score"] for i in matched_intents),
            default=0.0
        )

        # Category resolution — no hardcoded fallback dict:
        # Priority 1: semantic router (when confident)
        # Priority 2: intent→category (derived from embeddings at startup)
        # Priority 3: None (search full corpus)
        category = routing.get("category")

        if not category:
            for intent_name in intent_names:
                inferred = self._intent_to_category.get(intent_name)
                if inferred:
                    category = inferred
                    break

        return RetrievalContext(
            original_query=query,
            expanded_query=expanded_query,
            intents=intent_names,
            category=category,
            confidence=max(
                routing.get("confidence", 0.0),
                intent_confidence
            ),
            anchors=[],
            prototype=(
                matched_intents[0].get("prototype", "")
                if matched_intents else ""
            ),
        )