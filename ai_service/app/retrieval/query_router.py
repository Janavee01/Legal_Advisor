LEGAL_CONCEPTS = {
    "domestic violence": ["domestic violence"],
    "workplace harassment": [
        "workplace harassment",
        "sexual harassment",
        "harassment at workplace",
    ],
    "minimum wages": [
        "minimum wage",
        "minimum wages",
    ],
    "working hours": [
        "working hours",
        "daily hours",
        "weekly hours",
        "overtime",
    ],
    "consumer defect": [
        "defective product",
        "defective",
        "refund",
        "replacement",
    ],
    "drunk driving": [
        "drunk driving",
        "drunken driving",
        "driving under influence",
    ],
}

import re

CATEGORY_KEYWORDS = {
    "criminal": [
        "murder",
        "theft",
        "assault",
        "kidnap",
        "punishment",
        "bail",
        "fir",
        "police",
        "crime",
        "homicide",
        "attempt",
    ],

    "consumer": [
        "refund",
        "defective",
        "consumer",
        "service",
        "amazon",
        "flipkart",
        "warranty",
        "replacement",
        "product",
        "seller",
    ],

    "family": [
        "divorce",
        "custody",
        "marriage",
        "maintenance",
        "alimony",
        "child support",
    ],
}


def detect_intents(query: str) -> dict:

    query_lower = query.lower()

    result = {
        "category": None,
        "offence": None,
        "intent": None,
        "section_number": None,
        "active_intents": [],
    }

    # -------------------------------------------------
    # category detection
    # -------------------------------------------------

    for category, keywords in CATEGORY_KEYWORDS.items():

        for word in keywords:

            if word in query_lower:
                result["category"] = category
                break

        if result["category"]:
            break

    # -------------------------------------------------
    # section extraction
    # -------------------------------------------------

    section_match = re.search(
        r"(section|sec)\s+(\d+)",
        query_lower
    )

    if section_match:

        result["section_number"] = section_match.group(2)

    else:

        # handles:
        # "302 murder punishment"

        standalone_number = re.search(
            r"\b(\d{2,4})\b",
            query_lower
        )

        if standalone_number:
            result["section_number"] = standalone_number.group(1)

    # -------------------------------------------------
    # offence detection
    # -------------------------------------------------

    offence_keywords = [
        "murder",
        "kill",
        "homicide",
        "culpable homicide",
        "theft",
        "assault",
        "kidnap",
    ]

    for word in offence_keywords:

        if word in query_lower:

            result["offence"] = word
            result["active_intents"].append(word)

            break

    # -------------------------------------------------
    # intent detection
    # -------------------------------------------------

    punishment_keywords = [
        "punishment",
        "sentence",
        "imprisonment",
        "fine",
        "penalty",
        "death penalty",
    ]

    attempt_keywords = [
        "attempt",
        "trying",
        "preparation",
    ]

    bail_keywords = [
        "bail",
        "anticipatory bail",
        "regular bail",
    ]

    # punishment intent

    for word in punishment_keywords:

        if word in query_lower:

            result["intent"] = "punishment"
            result["active_intents"].append("punishment")

            break

    # attempt intent

    if result["intent"] is None:

        for word in attempt_keywords:

            if word in query_lower:

                result["intent"] = "attempt"
                result["active_intents"].append("attempt")

                break

    # bail intent

    if result["intent"] is None:

        for word in bail_keywords:

            if word in query_lower:

                result["intent"] = "bail"
                result["active_intents"].append("bail")

                break

    for concept, phrases in LEGAL_CONCEPTS.items():

        for phrase in phrases:
        
            if phrase in query_lower:
                result["active_intents"].append(concept)
                break

    result["active_intents"] = list(
        set(result["active_intents"])
    )

    return result