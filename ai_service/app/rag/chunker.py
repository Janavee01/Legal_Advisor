"""
chunker.py — Section-aware chunker for parsed Indian legal Act JSON.

Old approach: split on character count → breaks mid-sentence, loses citations.
New approach: each section from parser.py is already a natural chunk.
              Long sections are split on sentence boundaries, never mid-word.

Exports:
    chunk_sections(sections: list[dict]) -> list[dict]
    chunk_text(text: str) -> list[str]   # kept for backward compatibility
"""

import re
from typing import Optional

# Maximum characters per chunk sent to the embedder.
# all-MiniLM-L6-v2 has a 256 token limit ≈ ~1000 chars safe upper bound.
MAX_CHUNK_CHARS = 500
MIN_CHUNK_CHARS = 80  # discard stubs shorter than this


def _split_into_sentences(text: str) -> list[str]:
    """
    Split text into sentences using punctuation boundaries.
    Handles Indian legal text patterns like "proviso.—" and numbered clauses.
    """
    # Split on sentence-ending punctuation followed by whitespace + capital
    sentence_endings = re.compile(r"(?<=[.!?;—])\s+(?=[A-Z\(\"])")
    sentences = sentence_endings.split(text)
    return [s.strip() for s in sentences if s.strip()]


def _merge_into_chunks(sentences: list[str], max_chars: int) -> list[str]:
    """
    Greedily merge sentences into chunks that don't exceed max_chars.
    Never breaks mid-sentence.
    """
    chunks = []
    current = ""

    for sentence in sentences:
        # If a single sentence exceeds limit, it becomes its own chunk
        if len(sentence) > max_chars:
            if current:
                chunks.append(current.strip())
                current = ""
            chunks.append(sentence.strip())
            continue

        if len(current) + len(sentence) + 1 <= max_chars:
            current = (current + " " + sentence).strip()
        else:
            if current:
                chunks.append(current.strip())
            current = sentence

    if current:
        chunks.append(current.strip())

    return [c for c in chunks if len(c) >= MIN_CHUNK_CHARS]


def chunk_sections(sections: list[dict]) -> list[dict]:
    """
    Main function used by ingest.py.

    Takes parsed sections (output of parser.py) and returns a flat list
    of chunks ready for embedding. Each chunk carries full citation metadata.

    Each output dict:
        text          : the text to embed
        citation      : "Consumer Protection Act, 2019 › Section 35 › Jurisdiction..."
        section_number: "35"
        section_title : "Jurisdiction of District Commission"
        act_name      : "Consumer Protection Act, 2019"
        short_name    : "CPA 2019"
        year          : 2019
        category      : "consumer"
        source        : "consumer_protection_act_2019.json"
        chunk_index   : 0  (if section was split into multiple chunks)
        total_chunks  : 1
    """
    all_chunks = []

    for section in sections:
        text = section["text"]

        if len(text) <= MAX_CHUNK_CHARS:
            # Section fits in one chunk — ideal case, no splitting needed
            sub_chunks = [text]
        else:
            sentences = _split_into_sentences(text)
            sub_chunks = _merge_into_chunks(sentences, MAX_CHUNK_CHARS)

        total = len(sub_chunks)

        for i, chunk_text in enumerate(sub_chunks):
            # For multi-chunk sections, append part indicator to citation
            citation = section["citation"]
            if total > 1:
                citation = f"{citation} (part {i+1}/{total})"

            all_chunks.append({
                "text": chunk_text,
                "citation": citation,
                "section_number": section["section_number"],
                "section_title": section["section_title"],
                "chapter": section.get("chapter", ""),
                "act_name": section["act_name"],
                "short_name": section["short_name"],
                "year": section["year"],
                "category": section.get("category", "general"),
                "source": section.get("source", ""),
                "chunk_index": i,
                "total_chunks": total,
            })

    return all_chunks


# ── Backward compatibility ────────────────────────────────────────────────────
def chunk_text(text: str, chunk_size: int = 900) -> list[str]:
    """
    Legacy interface — kept so existing code calling chunk_text() doesn't break.
    Uses sentence-boundary splitting instead of the old character-slice approach.
    """
    sentences = _split_into_sentences(text)
    return _merge_into_chunks(sentences, chunk_size)