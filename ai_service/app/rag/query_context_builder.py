from ai_service.app.retrieval.query_router import detect_intents
from ai_service.app.rag.intent_expander import LegalIntentExpander
from .retrieval_context import RetrievalContext

class QueryContextBuilder:

    def __init__(self):
        self.expander = LegalIntentExpander()

    def build(self, query: str) -> RetrievalContext:

        routing = detect_intents(query)
        expanded = self.expander.expand(query)

        matched_intents = expanded.get(
            "matched_intents",
            []
        )

        intent_names = list(dict.fromkeys(
            i["intent"]
            for i in matched_intents
        ))

        anchors = []

        for intent in matched_intents:
            anchors.extend(
                intent.get("anchors", [])
            )

        anchors = list(dict.fromkeys(anchors))
        parts = [query]

        for intent in matched_intents:
            parts.append(
                intent["intent"].replace("_", " ")
            )

        expanded_query = " ".join(parts)

        confidence = (
            max(
                [i["score"] for i in matched_intents],
                default=0.0
            )
        )

        return RetrievalContext(
            original_query=query,
            expanded_query=expanded_query,
            intents=intent_names,
            category=routing.get("category"),
            confidence=confidence,
            anchors=anchors
        )