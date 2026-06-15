from ai_service.app.retrieval.query_router import detect_intents
from ai_service.app.rag.intent_expander import LegalIntentExpander
from .retrieval_context import RetrievalContext

class QueryContextBuilder:

    def __init__(self):
        self.expander = LegalIntentExpander()

    def build(self, query: str) -> RetrievalContext:

        routing = detect_intents(query)
        expanded = self.expander.expand(query)

        expanded_query = " ".join([
    query,
    expanded.get("intent", "").replace("_", " ")
])

        confidence = 1.0 if routing.get("active_intents") else 0.4

        return RetrievalContext(
            original_query=query,
            expanded_query=expanded_query,
            intents=list(set(routing.get("active_intents", []))),
            category=routing.get("category"),
            confidence=confidence,
        )