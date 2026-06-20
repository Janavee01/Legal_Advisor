from ai_service.app.retrieval.semantic_router import semantic_route
import re

def detect_intents(query: str) -> dict:

    query_lower = query.lower()

    result = {
        "category": None,
        "offence": None,
        "intent": None,
        "section_number": None,
        "active_intents": [],
    }

    route = semantic_route(query)

    if route["confidence"] >= 0.45:
        result["category"] = route["category"]

    section_match = re.search(
        r"(section|sec)\s+(\d+)",
        query_lower
    )

    if section_match:
        result["section_number"] = section_match.group(2)
    else:
        standalone_number = re.search(
            r"\b(\d{2,4})\b",
            query_lower
        )

        if standalone_number:
            result["section_number"] = standalone_number.group(1)

    return result