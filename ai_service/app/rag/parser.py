"""
parser.py — Extracts structured sections from Indian legal Act PDFs.
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


def load_act_metadata():
    metadata = {}
    for pdf_path in RAW_PDF_DIR.rglob("*.pdf"):
        stem = pdf_path.stem
        metadata[stem] = {
            "act_name": stem.replace("_", " ").title(),
            "short_name": stem[:12],
            "year": 0,
            "ministry": "Unknown",
            "relevance": []
        }
    return metadata


ACT_METADATA = load_act_metadata()

SECTION_PATTERN = re.compile(
    r"^(?:Section\s+)?(\d+[A-Z]?)\.\s+(.+?)\.[—–―-]",
    re.MULTILINE,
)

CHAPTER_PATTERN = re.compile(
    r"^CHAPTER\s+([IVXLCDM]+|[0-9]+)\s*\n(.+)$",
    re.MULTILINE,
)

NOISE_PATTERNS = [
    re.compile(r"^\s*\d+\s*$"),
    re.compile(r"THE GAZETTE OF INDIA", re.I),
    re.compile(r"MINISTRY OF LAW", re.I),
    re.compile(r"^\s*—\s*$"),
    re.compile(r"jftLVªh laö", re.I),
    re.compile(r"REGISTERED NO\.", re.I),
    re.compile(r"EXTRAORDINARY", re.I),
]


def clean_text(text: str) -> str:
    lines = text.split("\n")
    cleaned = []
    for line in lines:
        if any(p.search(line) for p in NOISE_PATTERNS):
            continue
        cleaned.append(line)
    text = "\n".join(cleaned)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def extract_text_from_pdf(pdf_path: Path) -> str:
    log.info("Extracting text from: %s", pdf_path.name)
    pages_text = []
    with pdfplumber.open(pdf_path) as pdf:
        log.info("  Pages: %d", len(pdf.pages))
        for i, page in enumerate(pdf.pages):
            text = page.extract_text(x_tolerance=2, y_tolerance=3)
            if text:
                pages_text.append(text)
    return "\n".join(pages_text)


def parse_sections(full_text: str, act_metadata: dict) -> list[dict]:
    cleaned = clean_text(full_text)
    section_matches = list(SECTION_PATTERN.finditer(cleaned))

    if not section_matches:
        log.warning("No sections detected — falling back to paragraph chunking")
        return _paragraph_fallback(cleaned, act_metadata)

    log.info("  Detected %d raw section matches", len(section_matches))

    chapter_matches = {m.start(): m.group(2).strip() for m in CHAPTER_PATTERN.finditer(cleaned)}
    chapter_positions = sorted(chapter_matches.keys())

    def get_chapter_at(pos: int) -> str:
        relevant = [p for p in chapter_positions if p <= pos]
        if not relevant:
            return "General"
        return chapter_matches[max(relevant)]

    sections = []
    skipped_footnotes = 0

    for i, match in enumerate(section_matches):
        section_number = match.group(1).strip()
        section_title = match.group(2).strip()

        start = match.start()
        end = section_matches[i + 1].start() if i + 1 < len(section_matches) else len(cleaned)
        section_text = cleaned[start:end].strip()

        if len(section_text) < 50:
            continue

        if _is_footnote_match(section_title, section_text):
            skipped_footnotes += 1
            # IMPORTANT: a footnote match still owns a text span (start:end)
            # that contains real downstream Act content (e.g. the rest of
            # Section 2's definitions, which continue after the footnote
            # interrupts mid-section). Dropping the match entirely would
            # silently delete that content. Instead, fold this span's text
            # — with the footnote's own boilerplate sentence stripped out —
            # onto the END of the most recently kept real section, so the
            # content survives under the correct citation.
            if sections:
                remainder = _strip_footnote_sentence(section_text)
                if remainder:
                    sections[-1]["text"] = sections[-1]["text"].rstrip() + "\n" + remainder
            continue

        chapter = get_chapter_at(start)
        citation = f"{act_metadata['act_name']} › Section {section_number} › {section_title}"

        sections.append({
            "category": act_metadata.get("category", "unknown"),
            "act_name": act_metadata["act_name"],
            "year": act_metadata["year"],
            "chapter": chapter,
            "section_number": section_number,
            "section_title": section_title,
            "topics": act_metadata.get("relevance", []),
            "text": section_text,
            "citation": citation,
            "char_count": len(section_text),
        })

    # char_count may now be stale for sections that absorbed footnote
    # remainders — refresh it before returning.
    for s in sections:
        s["char_count"] = len(s["text"])

    sections = _merge_duplicate_section_numbers(sections)

    if skipped_footnotes:
        log.info(
            "  Filtered %d footnote/notification false matches "
            "(non-footnote remainder text was preserved in the preceding section)",
            skipped_footnotes,
        )
    log.info("  Kept %d genuine sections", len(sections))

    return sections


def _strip_footnote_sentence(footnote_span_text: str) -> str:
    """
    A footnote match's text span runs from the footnote marker to the start
    of the next match. That span is mostly notification boilerplate, but it
    can also contain the *next real chunk* of Act text that follows the
    footnote on the page (e.g. clauses (4)/(5) of Section 2 continuing
    after the footnote block ends).

    Strategy: a footnote block always starts with "<small int>. <date>.--"
    and runs as one long notification sentence until a terminal period
    that ends a "Gazette of India ... sec. N(ii)." citation. We locate
    that whole block (marker → end-of-notification-sentence) and remove
    it wholesale, rather than splitting on every period — gazette
    boilerplate is full of internal abbreviation periods ("S.O.", "s.",
    "sec.") that make naive sentence-splitting shred real text around it.
    """
    footnote_block = re.compile(
        r"^\d{1,2}\.\s+\d{1,2}(st|nd|rd|th)?\s+\w+,?\s*\d{4}\.?\s*[-–—.]{1,2}"
        r".*?(?:Extraordinary,?\s*Part\s*[IVX]+,?\s*sec\.\s*\d+\([a-z]+\)\.|"
        r"see Gazette of India[^.]*\.|vide notification[^.]*\.)",
        re.I | re.S,
    )

    remainder = footnote_block.sub("", footnote_span_text)

    # Safety net: if the block regex didn't fully match (notification text
    # varies across Acts), fall back to dropping only lines that still
    # carry an unambiguous footnote marker, rather than returning the
    # untouched span.
    if _FOOTNOTE_BODY_MARKERS.search(remainder) or re.search(
        r"^\d{1,2}\.\s+\d{1,2}(st|nd|rd|th)?\s+\w+,?\s*\d{4}", remainder.strip()
    ):
        lines = remainder.split("\n")
        remainder = "\n".join(
            ln for ln in lines
            if not _FOOTNOTE_BODY_MARKERS.search(ln)
            and not re.match(r"^\d{1,2}\.\s+\d{1,2}(st|nd|rd|th)?\s+\w+,?\s*\d{4}", ln.strip())
        )

    return remainder.strip()


_DATE_TITLE_PATTERN = re.compile(
    r"^\d{1,2}(st|nd|rd|th)?\s+(January|February|March|April|May|June|July|"
    r"August|September|October|November|December)[,]?\s+\d{4}$",
    re.I,
)

_FOOTNOTE_BODY_MARKERS = re.compile(
    r"vide notification|gazette of india|S\.O\.\s*\d|w\.e\.f\.|"
    r"shall come into force|extraordinary,?\s*part",
    re.I,
)


def _is_footnote_match(section_title: str, section_text: str) -> bool:
    """
    Detects commencement-notification footnotes that masquerade as section
    headers, e.g.:
        "2. 24th July, 2020.-- S. 2 [clauses (4), (13)...], vide notification
        No. S.O. 2421(E), dated 23rd July 2020, see Gazette of India..."

    These match SECTION_PATTERN structurally (number + text + terminal dash)
    but are not real Act sections. Two independent signals catch them:
      1. The "title" captured is itself just a date (e.g. "24th July, 2020").
      2. The body text contains gazette/notification boilerplate language
         that never appears in actual substantive section text.
    """
    if _DATE_TITLE_PATTERN.match(section_title.strip()):
        return True

    # Check only the first ~300 chars — footnote markers appear early;
    # avoids false positives from a real section that merely *cites* a
    # notification deep in its body (e.g. an amendment proviso).
    head = section_text[:300]
    if _FOOTNOTE_BODY_MARKERS.search(head):
        return True

    return False


def _merge_duplicate_section_numbers(sections: list[dict]) -> list[dict]:
    """
    If filtering still leaves two entries with the same section_number
    (e.g. PDF text wrapped awkwardly around a footnote and split a real
    section into two matches), keep the longer/more complete one rather
    than silently duplicating citations.
    """
    by_number: dict[str, dict] = {}
    order: list[str] = []

    for s in sections:
        num = s["section_number"]
        if num not in by_number:
            by_number[num] = s
            order.append(num)
        else:
            existing = by_number[num]
            # Prefer the version with a non-trivial title and more text
            existing_is_bad_title = _DATE_TITLE_PATTERN.match(existing["section_title"])
            new_is_bad_title = _DATE_TITLE_PATTERN.match(s["section_title"])
            if existing_is_bad_title and not new_is_bad_title:
                by_number[num] = s
            elif len(s["text"]) > len(existing["text"]) and not new_is_bad_title:
                by_number[num] = s

    return [by_number[n] for n in order]


def _paragraph_fallback(text: str, act_metadata: dict) -> list[dict]:
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
            "topics": act_metadata.get("relevance", []),
            "char_count": len(para),
        }
        for i, para in enumerate(paragraphs)
    ]


def parse_act(pdf_path: Path, category: str) -> Optional[Path]:
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
    act_metadata["category"] = category

    try:
        full_text = extract_text_from_pdf(pdf_path)
    except Exception as e:
        log.error("PDF extraction failed for %s: %s", pdf_path.name, e)
        return None

    sections = parse_sections(full_text, act_metadata)

    if not sections:
        log.error("No sections extracted from %s", pdf_path.name)
        return None

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