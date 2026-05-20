"""
parser.py — Extracts structured sections from Indian legal Act PDFs.

Indian Acts have a consistent structure:
    "CHAPTER II
     RIGHTS OF CONSUMERS

     Section 2. — Definitions.—
     In this Act, unless the context otherwise requires,—
     ..."

This parser identifies section boundaries using that pattern and
outputs structured JSON: one record per section, with full metadata.

Run:
    python parser.py

Reads  : datasets/raw_pdfs/<category>/<act>.pdf
Writes : datasets/parsed/<category>/<act>.json
"""

import re
import json
import logging
from pathlib import Path
from typing import Optional
import pdfplumber

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parents[3]
RAW_PDF_DIR = BASE_DIR / "datasets" / "raw_pdfs"
PARSED_DIR = BASE_DIR / "datasets" / "parsed"

# ── Act-level metadata (keyed on filename stem) ───────────────────────────────
ACT_METADATA = {
    "consumer_protection_act_2019": {
        "act_name": "Consumer Protection Act, 2019",
        "short_name": "CPA 2019",
        "year": 2019,
        "ministry": "Ministry of Consumer Affairs",
        "relevance": ["consumer", "refund", "defective goods", "unfair trade", "complaint"],
    },
    "code_on_wages_2019": {
        "act_name": "Code on Wages, 2019",
        "short_name": "CoW 2019",
        "year": 2019,
        "ministry": "Ministry of Labour and Employment",
        "relevance": ["wages", "overtime", "salary", "payment", "minimum wage"],
    },
    "payment_of_wages_act_1936": {
        "act_name": "Payment of Wages Act, 1936",
        "short_name": "PWA 1936",
        "year": 1936,
        "ministry": "Ministry of Labour and Employment",
        "relevance": ["wages", "salary", "deductions", "payment timeline"],
    },
    "transfer_of_property_act_1882": {
        "act_name": "Transfer of Property Act, 1882",
        "short_name": "TPA 1882",
        "year": 1882,
        "ministry": "Ministry of Law and Justice",
        "relevance": ["lease", "tenant", "landlord", "rent", "security deposit", "eviction"],
    },
    "bharatiya_nyaya_sanhita_2023": {
        "act_name": "Bharatiya Nyaya Sanhita, 2023",
        "short_name": "BNS 2023",
        "year": 2023,
        "ministry": "Ministry of Home Affairs",
        "relevance": ["criminal", "assault", "theft", "harassment", "police", "FIR"],
    },
    "legal_metrology_act_2009": {
        "act_name": "Legal Metrology Act, 2009",
        "short_name": "LMA 2009",
        "year": 2009,
        "ministry": "Ministry of Consumer Affairs",
        "relevance": ["MRP", "weights", "measures", "price", "packaging"],
    },
}

# ── Regex patterns for section detection ─────────────────────────────────────
# Handles these real-world formats found in Indian Act PDFs:
#   "2. Definitions.—"
#   "Section 2.—Definitions.—"
#   "2A. Special provisions.—"
#   "35. Jurisdiction of District Commission.—"

SECTION_PATTERN = re.compile(
    r"^(?:Section\s+)?(\d+[A-Z]?)\.\s+([^\n—–-]{3,80}?)(?:\.—|—|\.—|–)",
    re.MULTILINE,
)

CHAPTER_PATTERN = re.compile(
    r"^CHAPTER\s+([IVXLCDM]+|[0-9]+)\s*\n(.+)$",
    re.MULTILINE,
)

# Lines to skip — common PDF header/footer noise in Indian government docs
NOISE_PATTERNS = [
    re.compile(r"^\s*\d+\s*$"),               # standalone page numbers
    re.compile(r"THE GAZETTE OF INDIA", re.I),
    re.compile(r"MINISTRY OF LAW", re.I),
    re.compile(r"^\s*—\s*$"),
    re.compile(r"jftLVªh laö", re.I),         # Hindi registry header
    re.compile(r"REGISTERED NO\.", re.I),
    re.compile(r"EXTRAORDINARY", re.I),
]


def clean_text(text: str) -> str:
    """Remove PDF extraction noise while preserving section structure."""
    lines = text.split("\n")
    cleaned = []
    for line in lines:
        if any(p.search(line) for p in NOISE_PATTERNS):
            continue
        cleaned.append(line)

    text = "\n".join(cleaned)
    # Collapse excessive whitespace but preserve paragraph breaks
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def extract_text_from_pdf(pdf_path: Path) -> str:
    """Extract full text from PDF using pdfplumber."""
    log.info("Extracting text from: %s", pdf_path.name)
    pages_text = []

    with pdfplumber.open(pdf_path) as pdf:
        log.info("  Pages: %d", len(pdf.pages))
        for i, page in enumerate(pdf.pages):
            text = page.extract_text(x_tolerance=2, y_tolerance=3)
            if text:
                pages_text.append(text)
            if (i + 1) % 20 == 0:
                log.info("  Processed %d/%d pages...", i + 1, len(pdf.pages))

    return "\n".join(pages_text)


def parse_sections(full_text: str, act_metadata: dict) -> list[dict]:
    """
    Split full Act text into individual sections with metadata.
    Returns a list of section dicts ready for ingestion.
    """
    cleaned = clean_text(full_text)

    # Find all section start positions
    section_matches = list(SECTION_PATTERN.finditer(cleaned))

    if not section_matches:
        log.warning("No sections detected — falling back to paragraph chunking")
        return _paragraph_fallback(cleaned, act_metadata)

    log.info("  Detected %d sections", len(section_matches))

    # Track current chapter
    chapter_matches = {m.start(): m.group(2).strip() for m in CHAPTER_PATTERN.finditer(cleaned)}
    chapter_positions = sorted(chapter_matches.keys())

    def get_chapter_at(pos: int) -> str:
        """Return the chapter title that was most recently declared before pos."""
        relevant = [p for p in chapter_positions if p <= pos]
        if not relevant:
            return "General"
        return chapter_matches[max(relevant)]

    sections = []
    for i, match in enumerate(section_matches):
        section_number = match.group(1).strip()
        section_title = match.group(2).strip()

        # Section text runs from this match to the next section (or end)
        start = match.start()
        end = section_matches[i + 1].start() if i + 1 < len(section_matches) else len(cleaned)
        section_text = cleaned[start:end].strip()

        # Skip stub sections (too short to be useful)
        if len(section_text) < 50:
            continue

        chapter = get_chapter_at(start)

        # Build the citation string — this is what gets shown to users
        citation = f"{act_metadata['act_name']} › Section {section_number} › {section_title}"

        sections.append({
            "section_number": section_number,
            "section_title": section_title,
            "chapter": chapter,
            "text": section_text,
            "citation": citation,
            "act_name": act_metadata["act_name"],
            "short_name": act_metadata["short_name"],
            "year": act_metadata["year"],
            "ministry": act_metadata["ministry"],
            "relevance_tags": act_metadata["relevance"],
            "char_count": len(section_text),
        })

    return sections


def _paragraph_fallback(text: str, act_metadata: dict) -> list[dict]:
    """
    Used when section detection fails (e.g. scanned/image PDFs).
    Chunks by paragraph instead — less precise but still structured.
    """
    paragraphs = [p.strip() for p in text.split("\n\n") if len(p.strip()) > 100]
    log.warning("  Using paragraph fallback: %d chunks", len(paragraphs))

    return [
        {
            "section_number": f"P{i+1}",
            "section_title": "Paragraph",
            "chapter": "Unknown",
            "text": para,
            "citation": f"{act_metadata['act_name']} › Paragraph {i+1}",
            "act_name": act_metadata["act_name"],
            "short_name": act_metadata["short_name"],
            "year": act_metadata["year"],
            "ministry": act_metadata["ministry"],
            "relevance_tags": act_metadata["relevance"],
            "char_count": len(para),
        }
        for i, para in enumerate(paragraphs)
    ]


def parse_act(pdf_path: Path, category: str) -> Optional[Path]:
    """Parse a single Act PDF. Returns path to output JSON or None on failure."""
    stem = pdf_path.stem

    act_metadata = ACT_METADATA.get(stem)
    if not act_metadata:
        log.warning("No metadata defined for '%s' — using defaults", stem)
        act_metadata = {
            "act_name": stem.replace("_", " ").title(),
            "short_name": stem[:10],
            "year": 0,
            "ministry": "Unknown",
            "relevance": [],
        }

    try:
        full_text = extract_text_from_pdf(pdf_path)
    except Exception as e:
        log.error("PDF extraction failed for %s: %s", pdf_path.name, e)
        return None

    sections = parse_sections(full_text, act_metadata)

    if not sections:
        log.error("No sections extracted from %s", pdf_path.name)
        return None

    # Write output JSON
    out_dir = PARSED_DIR / category
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{stem}.json"

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(sections, f, ensure_ascii=False, indent=2)

    log.info("✓ Parsed %d sections → %s", len(sections), out_path)
    return out_path


def run():
    if not RAW_PDF_DIR.exists():
        log.error("Raw PDF directory not found: %s", RAW_PDF_DIR)
        log.error("Run scraper.py first.")
        return

    pdf_files = list(RAW_PDF_DIR.rglob("*.pdf"))
    if not pdf_files:
        log.error("No PDFs found in %s", RAW_PDF_DIR)
        return

    log.info("Found %d PDFs to parse", len(pdf_files))
    success, failed = [], []

    for pdf_path in pdf_files:
        category = pdf_path.parent.name
        log.info("\nParsing: %s [%s]", pdf_path.name, category)
        out = parse_act(pdf_path, category)
        (success if out else failed).append(pdf_path.name)

    print("\n── Parse Summary ─────────────────────────────")
    print(f"  Succeeded : {len(success)}")
    for s in success:
        print(f"    ✓ {s}")
    if failed:
        print(f"  Failed    : {len(failed)}")
        for f in failed:
            print(f"    ✗ {f}")
    print("──────────────────────────────────────────────")


if __name__ == "__main__":
    run()