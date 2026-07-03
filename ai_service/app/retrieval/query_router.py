"""
query_router.py — Thin wrapper around semantic_route that produces a
structured routing result for QueryContextBuilder.

Extracts:
    category        : top semantic category (None if below confidence threshold)
    confidence      : semantic router confidence score
    section_number  : if the user explicitly referenced a section number
"""

from ai_service.app.retrieval.semantic_router import semantic_route
import re


def detect_intents(query: str) -> dict:
    query_lower = query.lower()

    route = semantic_route(query)

    # Match the threshold in semantic_router.py (0.50).
    # The old value of 0.45 was inconsistent — semantic_router returned
    # None for category below 0.50, but detect_intents re-applied 0.45,
    # meaning it could override the router's own None with a category value.
    CONFIDENCE_THRESHOLD = 0.50

    result = {
        "category": route["category"] if route["confidence"] >= CONFIDENCE_THRESHOLD else None,
        "confidence": route["confidence"],
        "section_number": None,
        "all_scores": route.get("all_scores", {}),
    }

    # Explicit section reference in query ("section 12", "sec 12")
    section_match = re.search(r"(section|sec)\.?\s+(\d+[A-Za-z]?)", query_lower)
    if section_match:
        result["section_number"] = section_match.group(2)
    else:
        # Bare number that looks like a section (2-4 digits, not a year)
        standalone = re.search(r"\b(\d{2,3})\b", query_lower)
        if standalone:
            result["section_number"] = standalone.group(1)

    return result