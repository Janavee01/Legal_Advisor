from ai_service.app.retrieval.query_router import detect_intents
from ai_service.app.rag.intent_expander import LegalIntentExpander
from .retrieval_context import RetrievalContext


class QueryContextBuilder:

    def __init__(self):
        self.expander = LegalIntentExpander()

    def build(self, query: str) -> RetrievalContext:

        routing = detect_intents(query)

        expanded = self.expander.expand(query)

        expanded_query = " ".join(
            expanded.get("expanded_queries", [query])
        )

        return RetrievalContext(
            original_query=query,
            expanded_query=expanded_query,
            intents=routing.get("active_intents", []),
            category=routing.get("category"),
            confidence=routing.get("confidence", 0.0),
        )