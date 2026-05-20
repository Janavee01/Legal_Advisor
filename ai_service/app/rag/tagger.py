LEGAL_TOPICS = {
    "security deposit": [
        "security deposit",
        "advance amount",
        "deposit refund"
    ],
    "lease termination": [
        "termination",
        "eviction",
        "vacate"
    ],
    "rent": [
        "rent",
        "monthly payment",
        "arrears"
    ]
}


def extract_topics(text: str) -> list[str]:
    text_lower = text.lower()

    matched = []

    for topic, keywords in LEGAL_TOPICS.items():
        for kw in keywords:
            if kw in text_lower:
                matched.append(topic)
                break

    return matched