from dataclasses import dataclass, field

@dataclass
class RetrievalContext:
    original_query: str
    expanded_query: str
    intents: list[str]
    category: str | None
    confidence: float
    anchors: list[str] = field(default_factory=list)