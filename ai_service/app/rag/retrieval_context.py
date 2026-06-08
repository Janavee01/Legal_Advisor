from dataclasses import dataclass
from typing import Optional, List, Dict, Any


@dataclass
class RetrievalContext:
    original_query: str
    expanded_query: str
    intents: List[str]
    category: Optional[str]
    confidence: float