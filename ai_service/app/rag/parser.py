"""
parser.py — Extracts structured sections from Indian legal Act PDFs
(India Code style documents: Constitution, Acts, Sanhitas/Codes).

Redesigned from the original prototype to fix:
  - infinite recursion in the "hybrid" structure branch
  - a hardcoded section-number > 300 cap that silently dropped real
    sections in long acts (BNSS has 531 sections, BNS has 358)
  - a reference to an undefined name (_FOOTNOTE_BODY_MARKERS) that
    would crash the moment that code path was hit
  - inconsistent return arity from parse_act() that crashes run()
  - placeholder metadata (year=0, ministry="Unknown" for everything)
  - schedules leaking into the text of the preceding section
  - unbounded debug print() calls with no verbosity control

Usage:
    python parser.py                      # parse every PDF under RAW_PDF_DIR
    python parser.py --act the_arms_act_1959   # parse just one act (by stem)
    python parser.py --verbose            # include debug-level logging
    python parser.py --show-unregistered  # list PDFs with no ACT_REGISTRY entry
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import pdfplumber


BASE_DIR = Path(__file__).resolve().parents[3]

RAW_PDF_DIR = BASE_DIR / "datasets" / "raw_pdfs"
PARSED_DIR = BASE_DIR / "datasets" / "parsed"

log = logging.getLogger("act_parser")


def configure_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=[
            logging.FileHandler("parser.log", encoding="utf-8"),
            logging.StreamHandler(),
        ],
        force=True,
    )


# --------------------------------------------------------------------------
# Act registry — real metadata, keyed by PDF stem (filename without .pdf).
#
# This covers the 37 acts in the supplied manifest. For any PDF found on
# disk that ISN'T in this dict, load_act_metadata() falls back to a
# heuristic (title-case the filename, pull the year off the end) so the
# parser still runs on acts you haven't registered yet — it just tags
# them so you can find and backfill them later (--show-unregistered).
# --------------------------------------------------------------------------
ACT_REGISTRY: dict[str, dict] = {
    "the_passports_act_1967": dict(
        act_name="The Passports Act 1967", short_name="Passports Act",
        year=1967, ministry="Ministry of External Affairs", category="administrative"),
    "constitution_of_india": dict(
        act_name="Constitution of India", short_name="Constitution",
        year=1950, ministry="Ministry of Law and Justice", category="constitution",
        structure="constitution"),
    "consumer_protection_act_2019": dict(
        act_name="Consumer Protection Act 2019", short_name="Consumer Protection Act",
        year=2019, ministry="Ministry of Consumer Affairs, Food and Public Distribution", category="consumer"),
    "legal_metrology_act_2009": dict(
        act_name="Legal Metrology Act 2009", short_name="Legal Metrology Act",
        year=2009, ministry="Ministry of Consumer Affairs, Food and Public Distribution", category="consumer"),
    "bharatiya_nagarik_suraksha_sanhita_2023": dict(
        act_name="Bharatiya Nagarik Suraksha Sanhita 2023", short_name="BNSS",
        year=2023, ministry="Ministry of Home Affairs", category="criminal"),
    "bharatiya_nyaya_sanhita_2023": dict(
        act_name="Bharatiya Nyaya Sanhita 2023", short_name="BNS",
        year=2023, ministry="Ministry of Home Affairs", category="criminal"),
    "bharatiya_sakshya_adhiniyam_2023": dict(
        act_name="Bharatiya Sakshya Adhiniyam 2023", short_name="BSA",
        year=2023, ministry="Ministry of Home Affairs", category="criminal"),
    "narcotic_drugs_and_psychotropic_substances_act_1985": dict(
        act_name="Narcotic Drugs And Psychotropic Substances Act 1985", short_name="NDPS Act",
        year=1985, ministry="Department of Revenue, Ministry of Finance", category="criminal"),
    "the_arms_act_1959": dict(
        act_name="The Arms Act 1959", short_name="Arms Act",
        year=1959, ministry="Ministry of Home Affairs", category="criminal"),
    "information_technology_act_2000": dict(
        act_name="Information Technology Act 2000", short_name="IT Act",
        year=2000, ministry="Ministry of Electronics and Information Technology", category="cyber"),
    "guardians_and_wards_act_1890": dict(
        act_name="Guardians and Wards Act 1890", short_name="Guardians and Wards Act",
        year=1890, ministry="Ministry of Law and Justice", category="family"),
    "hindu_marriage_act_1955": dict(
        act_name="Hindu Marriage Act 1955", short_name="Hindu Marriage Act",
        year=1955, ministry="Ministry of Law and Justice", category="family"),
    "hindu_succession_act_1956": dict(
        act_name="Hindu Succession Act 1956", short_name="Hindu Succession Act",
        year=1956, ministry="Ministry of Law and Justice", category="family"),
    "indian_succession_act_1925": dict(
        act_name="Indian Succession Act 1925", short_name="Indian Succession Act",
        year=1925, ministry="Ministry of Law and Justice", category="family"),
    "special_marriage_act_1954": dict(
        act_name="Special Marriage Act 1954", short_name="Special Marriage Act",
        year=1954, ministry="Ministry of Law and Justice", category="family"),
    "code_on_wages_2019": dict(
        act_name="Code on Wages 2019", short_name="Code on Wages",
        year=2019, ministry="Ministry of Labour and Employment", category="labour"),
    "industrial_disputes_act_1947": dict(
        act_name="Industrial Disputes Act 1947", short_name="Industrial Disputes Act",
        year=1947, ministry="Ministry of Labour and Employment", category="labour"),
    "labour_factories_act_1948": dict(
        act_name="Labour Factories Act 1948", short_name="Factories Act",
        year=1948, ministry="Ministry of Labour and Employment", category="labour"),
    "occupational_safety_health_and_working_conditions_code_2020": dict(
        act_name="Occupational Safety Health And Working Conditions Code 2020", short_name="OSH Code",
        year=2020, ministry="Ministry of Labour and Employment", category="labour"),
    "payment_of_wages_act_1936": dict(
        act_name="Payment of Wages Act 1936", short_name="Payment of Wages Act",
        year=1936, ministry="Ministry of Labour and Employment", category="labour"),
    "the_code_on_security_2020": dict(
        act_name="The Code On Security 2020", short_name="Social Security Code",
        year=2020, ministry="Ministry of Labour and Employment", category="labour"),
    "the_employees_compensation_act_1923": dict(
        act_name="The Employees Compensation Act 1923", short_name="Employee's Compensation Act",
        year=1923, ministry="Ministry of Labour and Employment", category="labour"),
    "the_employees_provident_funds_and_miscellaneous_provisions_act_1952": dict(
        act_name="The Employees Provident Funds and Miscellaneous Provisions Act 1952", short_name="EPF Act",
        year=1952, ministry="Ministry of Labour and Employment", category="labour"),
    "the_maternity_benefit_act_1961": dict(
        act_name="The Maternity Benefit Act 1961", short_name="Maternity Benefit Act",
        year=1961, ministry="Ministry of Labour and Employment", category="labour"),
    "registration_act_1908": dict(
        act_name="The Registration Act 1908", short_name="Registration Act",
        year=1908, ministry="Ministry of Rural Development", category="property"),
    "transfer_of_property_act_1882": dict(
        act_name="Transfer Of Property Act 1882", short_name="Transfer of Property Act",
        year=1882, ministry="Ministry of Law and Justice", category="property"),
    "legal_services_authorities_act_1987": dict(
        act_name="Legal Services Authorities Act 1987", short_name="Legal Services Authorities Act",
        year=1987, ministry="Ministry of Law and Justice", category="rights"),
    "right_to_information_act_2005": dict(
        act_name="Right To Information Act 2005", short_name="RTI Act",
        year=2005, ministry="Ministry of Personnel, Public Grievances and Pensions", category="rights"),
    "maintenance_and_welfare_of_parents_and_senior_citizens_act_2007": dict(
        act_name="Maintenance And Welfare Of Parents And Senior Citizens Act 2007",
        short_name="Senior Citizens Act",
        year=2007, ministry="Ministry of Social Justice and Empowerment", category="social_justice"),
    "rights_of_persons_with_disabilities_act_2016": dict(
        act_name="Rights Of Persons With Disabilities Act 2016", short_name="RPWD Act",
        year=2016, ministry="Ministry of Social Justice and Empowerment", category="social_justice"),
    "scheduled_castes_and_scheduled_tribes_act_1989": dict(
        act_name="Scheduled Castes And Scheduled Tribes Act 1989",
        short_name="SC/ST (POA) Act",
        year=1989, ministry="Ministry of Social Justice and Empowerment", category="social_justice"),
    "motor_vehicles_act_1988": dict(
        act_name="Motor Vehicles Act 1988", short_name="Motor Vehicles Act",
        year=1988, ministry="Ministry of Road Transport and Highways", category="transport"),
    "dowry_prohibition_act_1961": dict(
        act_name="Dowry Prohibition Act 1961", short_name="Dowry Prohibition Act",
        year=1961, ministry="Ministry of Women and Child Development", category="women_child"),
    "juvenile_justice_act_2015": dict(
        act_name="Juvenile Justice Act 2015", short_name="JJ Act",
        year=2015, ministry="Ministry of Women and Child Development", category="women_child"),
    "protection_of_Children_from_sexual_offences_act_2012": dict(
        act_name="Protection Of Children From Sexual Offences Act 2012", short_name="POCSO Act",
        year=2012, ministry="Ministry of Women and Child Development", category="women_child"),
    "protection_of_women_from_domestic_violence_act_2005": dict(
        act_name="Protection Of Women From Domestic Violence Act 2005", short_name="PWDVA",
        year=2005, ministry="Ministry of Women and Child Development", category="women_child"),
    "sexual_harassment_of_women_at_workplace_act_2013": dict(
        act_name="Sexual Harassment Of Women At Workplace Act 2013",
        short_name="POSH Act",
        year=2013, ministry="Ministry of Women and Child Development", category="women_child"),
}

_YEAR_RE = re.compile(r"(18|19|20)\d{2}$")


def load_act_metadata(stem: str, category_from_path: str) -> dict:
    """Look the PDF stem up in ACT_REGISTRY; fall back to a heuristic guess
    for acts that haven't been registered yet, and flag them as such so
    they're easy to find with --show-unregistered."""
    if stem in ACT_REGISTRY:
        meta = dict(ACT_REGISTRY[stem])
        if meta.get("category") != category_from_path:
            log.warning(
                "Category mismatch for %s: registry says '%s', folder says '%s'",
                stem, meta.get("category"), category_from_path,
            )
        meta["registered"] = True
        return meta

    log.warning("No registry entry for '%s' — using heuristic metadata", stem)
    year_match = _YEAR_RE.search(stem)
    year = int(year_match.group()) if year_match else 0
    name_part = stem[: year_match.start()].rstrip("_") if year_match else stem
    act_name = name_part.replace("_", " ").title()
    if year:
        act_name = f"{act_name}, {year}"
    return dict(
        act_name=act_name,
        short_name=act_name[:40],
        year=year,
        ministry="Unknown",
        category=category_from_path,
        registered=False,
    )


# --------------------------------------------------------------------------
# Noise / footnote filtering
# --------------------------------------------------------------------------
NOISE_PATTERNS = [
    re.compile(r"^\s*\d+\s*$"),                      # bare page numbers
    re.compile(r"THE GAZETTE OF INDIA", re.I),
    re.compile(r"MINISTRY OF LAW", re.I),
    re.compile(r"^\s*—\s*$"),
    re.compile(r"jftLVªh laö", re.I),                 # Hindi header OCR artifact
    re.compile(r"REGISTERED NO\.", re.I),
    re.compile(r"EXTRAORDINARY", re.I),
]

# Markers that reliably identify amendment/commencement footnote text,
# whether it appears as a "section header" false-match or inline within
# a genuine section's body (pdfplumber often interleaves footnotes with
# body text because it just reads the page top-to-bottom).
#
# Unprefixed verbs must be followed by "by ..." (e.g. "Omitted by Act 44
# of 1964") so a genuine body line like "...are hereby repealed:" is not
# mistaken for a footnote. Bare verbs are only trusted when they follow a
# "N." numbered line-start, which is how India Code renders footnotes.
_FOOTNOTE_BODY_MARKERS = re.compile(
    r"(?:^\s*(?:\d{1,2}\.\s*)?|]\s*[—\-.\u2013\u2014\u2015]?\s*)"
    r"(?:Subs\.|Ins\.|Inserted|Omitted|Rep\.|Repealed|Renumbered|Added)\s+by\b"
    r"|^\s*\d{1,2}\.\s*(?:Subs\.|Ins\.|Inserted|Omitted|Rep\.|Repealed|"
    r"Renumbered|Added)\b"
    r"|^\s*(?:Vide notification|Vide Act\b|w\.e\.f\.|Notifn\.?)",
    re.I | re.M,
)

# Broadened line-level stripper for section bodies only. Picks up the
# extra India Code notes-section starters that are safe to delete inside a
# body but too ambiguous to trust when deciding whether a header is real
# (e.g. "3. The word \"and\" omitted by Act 54 of 1994, s. 9 ...").
_FOOTNOTE_STRIP_RE = re.compile(
    r"^\s*\d{1,2}\.\s*(?:The\s+word[s]?\b|Words?\s+omitted|Serial\s+"
    r"|Cl\.?\s*\(\s*\d+\s*\)|(?:The\s+)?Proviso\s+|Explanation\b"
    r"|Ins\s+by\b|Added\s+by\b)",
    re.I,
)

_FOOTNOTE_TITLE_RE = re.compile(
    r"^(The\s+Explanation|The\s+proviso|The\s+(?:first\s+)?proviso|The\s+last\s+paragraph|"
    r"The\s+brackets?\s+and\s+figure[s]?\s*[“”'\"]|The\s+Bill,\s+inter\s+alia|"
    r"Section\s+\d+\s*[A-Z]?\s+(?:re-?numbered|numbered|renumbered|shall\s+stand\s+ins)\b|"
    r"Sub-section|Sub-clause\s*\(\s*[A-Za-z\d]+\s*\)\s*(?:omitted|added|substituted|inserted|rep)\.?\s+by\b|"
    r"Clause\b|"
    r"Cls?\.?\s*\(\s*[A-Za-z\d]+\s*\)(?:\s+and\s+\(\s*[A-Za-z\d]+\s*\))*\s*(?:omitted|renumbered|added|substituted|inserted|rep)\.?(?:\s+by\b|\b)|"
    r"S\.\s*s\.\s*\(\s*[A-Za-z\d]+\s*\)(?:\s+and\s+\(\s*[A-Za-z\d]+\s*\))?\s*(?:omitted|added|substituted|inserted)\.?\s+by\b|"
    r"Original\s+cl\.?\s*\(\s*[A-Za-z\d]+\s*\)\s*(?:re-?numbered|renumbered)\s*\(\s*[A-Za-z\d]+\s*\)\s+by\b|"
    r"Serial\s+(?:No\.?s?\.?|numbers?)\s*\d|"
    r"Explanation\s*(?:I|II|III|IV|V|\d+)?\s*(?:omitted|added|substituted|rep)\.?|"
    r"Inserted by|Omitted by|Substituted by|Renumbered by|"
    r"Subs\.|Ins\.|Ins\s+by\b|Omitted\b|Sub\.|Sub-\s|Added by|Rep\.|Repealed by|"
    r"Proviso\s+(?:omitted|added|substituted|rep)\.?|"
    r"(?:First|Second|Third|Fourth|Fifth|Sixth|Seventh|Last)\s+paragraph\s+(?:omitted|added|substituted)\.?\s+by\b|"
    r"(?:Certain\s+)?words?\s+omitted\s+by\b|Words?\s+and\s+figures|The\s+word[s]?\b|"
    r"The\s+Act\s+has\s+been\s+extended|This\s+Act\s+has\s+been\s+extended|"
    r"\d{1,2}(?:st|nd|rd|th)?\s+(?:day\s+of\s+)?[A-Za-z]+,\s*\d{4}\s*(?:\.-|--|\.\s*[—\u2013\u2014\u2015-]|,?\s*\[|,?\s+(?:except|vide|Notifn|notifn|see))|"
    r"^\[[^\]]+\][.\s\-\u2013\u2014\u2015]*\s*(?:Omitted|Substituted|Inserted|Subs\.|Ins\.|Repealed|rep)\.?\b|"
    r"\d+\.\s*(?:Subs\.|Ins\.|Omitted))",
    re.I,
)

_DATE_TITLE_PATTERN = re.compile(
    r"^\d{1,2}(st|nd|rd|th)?\s+(January|February|March|April|May|June|July|"
    r"August|September|October|November|December)[,]?\s+\d{4}$",
    re.I,
)

# A full commencement-notification footnote block: starts "N. <date>.--"
# and runs until it hits a Gazette citation sentence terminator. Applied
# globally (re.sub, all occurrences) as a cleanup pass over final section
# text, rather than tracked as inter-match spans — this avoids the
# span-slicing bugs in the original implementation.
_FOOTNOTE_BLOCK_RE = re.compile(
    r"\d{1,2}\.\s+\d{1,2}(st|nd|rd|th)?\s+\w+,?\s*\d{4}\.?\s*[-–—.]{1,2}"
    r".*?(?:Extraordinary,?\s*Part\s*[IVX]+,?\s*sec\.\s*\d+\([a-z]+\)\.|"
    r"see Gazette of India[^.]*\.|vide notification[^.]*\.)",
    re.I | re.S,
)


def strip_footnotes(text: str) -> str:
    """Remove amendment/commencement-notification footnote text from a
    section body. Two passes: (1) whole notification-citation blocks via
    the block regex, (2) any remaining lines that still open with an
    unambiguous footnote marker (catches cases where page-break formatting
    keeps the block regex from matching end-to-end)."""
    text = _FOOTNOTE_BLOCK_RE.sub("", text)
    lines = text.split("\n")
    lines = [ln for ln in lines
             if not _FOOTNOTE_BODY_MARKERS.search(ln) and not _FOOTNOTE_STRIP_RE.search(ln)]
    return "\n".join(lines)


def is_footnote_title(title: str) -> bool:
    return bool(_FOOTNOTE_TITLE_RE.match(title.strip()))


def is_footnote_header_match(section_title: str, section_body_head: str) -> bool:
    """A 'section header' that's actually a commencement-notification
    footnote masquerading as one, e.g. '2. 24th July, 2020.-- S. 2 ...'"""
    if _DATE_TITLE_PATTERN.match(section_title.strip()):
        return True
    # Only the first line of the body is consulted: a genuine section opens
    # with operative prose, while a footnote header is immediately followed
    # by the rest of the notification (or a bracket-title continuation
    # ending in "Omitted by ...", "Rep. by ...", etc.). Scanning deeper
    # would let a footnote that merely appears INSIDE a real section's body
    # (e.g. MVA s.15) wrongly kill that section.
    first_line = section_body_head.split("\n", 1)[0][:120]
    if _FOOTNOTE_BODY_MARKERS.search(first_line):
        return True
    return False


# --------------------------------------------------------------------------
# Structural regexes
# --------------------------------------------------------------------------
# Section headers: line-start, number (with optional letter suffix for
# inserted sections like 10A / 10AA), period, then a title that starts
# with an uppercase letter, quote, or "(" — this single constraint kills
# most false positives (numbers mid-sentence, like "40 per cent of ...")
# because the character right after the digits+period in real prose is
# almost always lowercase.
HEADER_PATTERN = re.compile(
    r"(?m)^(?P<num>\d{1,3}[A-Z]{0,2})\.[ \t]+(?P<title>[^\n]{1,300})$"
)

CHAPTER_PATTERN = re.compile(
    r"(?m)^CHAPTER\s+([IVXLCDM]+|[0-9]+)\s*\n(.+)$"
)

SCHEDULE_PATTERN = re.compile(
    r"(?m)^\s*(?:THE\s+)?"
    r"(FIRST|SECOND|THIRD|FOURTH|FIFTH|SIXTH|SEVENTH|EIGHTH|NINTH|TENTH)\s+SCHEDULE\b",
    re.I,
)

CONSTITUTION_RE = re.compile(r"(?m)^(Article\s+\d{1,3}[A-Z]{0,2}\.)")


# --------------------------------------------------------------------------
# Text extraction / cleaning
# --------------------------------------------------------------------------
def extract_text_from_pdf(pdf_path: Path) -> str:
    log.info("Extracting text from: %s", pdf_path.name)
    pages_text = []
    with pdfplumber.open(pdf_path) as pdf:
        log.debug("  Pages: %d", len(pdf.pages))
        for page in pdf.pages:
            text = page.extract_text(x_tolerance=2, y_tolerance=3)
            if text:
                pages_text.append(text)
    return "\n".join(pages_text)


def clean_text(text) -> str:
    if text is None:
        return ""
    if isinstance(text, list):
        text = "\n".join(str(x) for x in text)
    text = str(text)

    lines = text.split("\n")
    cleaned_lines = [ln for ln in lines if not any(p.search(ln) for p in NOISE_PATTERNS)]
    text = "\n".join(cleaned_lines)

    # Join genuine word-wrap hyphenation (e.g. "gov-\nernment") but NOT the
    # "--" em-dash marker India Code uses after a section heading
    # ("Definitions.--\n..."), which must stay on its own line or the next
    # line's text gets swallowed into the header title.
    text = re.sub(r"(?<=[a-z])-\n(?=[a-z])", "", text)
    text = re.sub(r"\n+", "\n", text)
    return text.strip()


def remove_toc(text: str) -> str:
    """Strip the 'ARRANGEMENT OF SECTIONS' table of contents, which
    otherwise produces one false section-header match per TOC entry."""
    if "ARRANGEMENT OF SECTIONS" not in text:
        return text
    remainder = text.split("ARRANGEMENT OF SECTIONS", 1)[1]
    m = re.search(r"ACT NO\.\s+\d+\s+OF\s+\d+", remainder)
    return remainder[m.start():] if m else text


def detect_structure_type(act_metadata: dict, text: str) -> str:
    """Only the Constitution should ever get routed to the Article-based
    parser. Trust the registry's explicit 'structure' flag rather than
    sniffing for the words 'article' or 'part' in the first 8000 chars —
    those words show up constantly in ordinary acts (cross-references
    like "under article 32", or plain "PART I" chapter divisions), and
    that false-positive was routing 8 of 37 acts into the Constitution
    parser, which then fell back to 1-paragraph chunking for all of them.
    """
    if act_metadata.get("structure") == "constitution":
        return "constitution"
    if "constitution" in act_metadata.get("act_name", "").lower():
        return "constitution"
    return "standard"


# --------------------------------------------------------------------------
# Core section parser
# --------------------------------------------------------------------------
def parse_sections(full_text: str, act_metadata: dict) -> list[dict]:
    cleaned = remove_toc(clean_text(full_text))

    schedule_matches = list(SCHEDULE_PATTERN.finditer(cleaned))
    schedule_starts = [m.start() for m in schedule_matches]

    raw_headers = list(HEADER_PATTERN.finditer(cleaned))
    if not raw_headers:
        log.warning("No sections detected — falling back to paragraph chunking")
        return _paragraph_fallback(cleaned, act_metadata)

    log.debug("  %d raw header candidates before validation", len(raw_headers))

    # --- validate headers: keep only ones that look like real sections ---
    valid_headers = []
    for m in raw_headers:
        title = m.group("title").strip()
        if is_footnote_title(title):
            continue
        if len(title) < 3:
            continue
        peek = cleaned[m.end(): m.end() + 200]
        if is_footnote_header_match(title, peek):
            continue
        valid_headers.append(m)

    if not valid_headers:
        log.warning("All header candidates filtered as noise — falling back to paragraph chunking")
        return _paragraph_fallback(cleaned, act_metadata)

    log.debug("  %d headers kept after validation", len(valid_headers))

    chapter_matches = {m.start(): m.group(2).strip() for m in CHAPTER_PATTERN.finditer(cleaned)}
    chapter_positions = sorted(chapter_matches.keys())

    def chapter_at(pos: int) -> str:
        relevant = [p for p in chapter_positions if p <= pos]
        return chapter_matches[max(relevant)] if relevant else "General"

    header_positions = [m.start() for m in valid_headers]

    def next_boundary_after(pos: int) -> int:
        """End of a section = the next real header OR the next schedule,
        whichever comes first — this is what stops schedule text bleeding
        into the last operative section."""
        candidates = [p for p in header_positions if p > pos]
        candidates += [s for s in schedule_starts if s > pos]
        candidates.append(len(cleaned))
        return min(candidates)

    sections: list[dict] = []

    for i, match in enumerate(valid_headers):
        section_number = match.group("num").strip()
        section_title = match.group("title").strip()
        start = match.start()
        end = next_boundary_after(start)
        section_text = strip_footnotes(cleaned[start:end]).strip()

        if len(section_text) < 10:
            continue

        chapter = chapter_at(start)
        citation = f"{act_metadata['act_name']} \u203a Section {section_number} \u203a {section_title}"

        sections.append({
            "category": act_metadata.get("category", "unknown"),
            "act_name": act_metadata["act_name"],
            "short_name": act_metadata.get("short_name"),
            "year": act_metadata["year"],
            "ministry": act_metadata.get("ministry"),
            "chapter": chapter,
            "section_number": section_number,
            "section_title": section_title,
            "topics": act_metadata.get("relevance", []),
            "text": section_text,
            "citation": citation,
            "char_count": len(section_text),
            "is_schedule": False,
        })

    sections = _merge_duplicate_section_numbers(sections)
    def next_schedule_boundary(pos: int) -> int:
        """End of a schedule block = the next schedule OR the next real
        section header, whichever comes first — otherwise an operative
        section sitting between two schedules gets its text duplicated
        into (and diluted by) the preceding schedule chunk."""
        candidates = [s for s in schedule_starts if s > pos]
        candidates += [p for p in header_positions if p > pos]
        candidates.append(len(cleaned))
        return min(candidates)

    for i, sm in enumerate(schedule_matches):
        s_start = sm.start()
        s_end = next_schedule_boundary(s_start)
        s_text = clean_text(cleaned[s_start:s_end])
        if len(s_text) < 10:
            continue
        label = sm.group(1).title()
        sections.append({
            "category": act_metadata.get("category", "unknown"),
            "act_name": act_metadata["act_name"],
            "short_name": act_metadata.get("short_name"),
            "year": act_metadata["year"],
            "ministry": act_metadata.get("ministry"),
            "chapter": "Schedule",
            "section_number": f"Schedule-{label}",
            "section_title": f"{label} Schedule",
            "topics": act_metadata.get("relevance", []),
            "text": s_text,
            "citation": f"{act_metadata['act_name']} \u203a {label} Schedule",
            "char_count": len(s_text),
            "is_schedule": True,
        })

    _check_sequence_gaps([s for s in sections if not s["is_schedule"]])
    log.info("  Kept %d sections (%d schedule blocks)", len(sections),
              sum(s["is_schedule"] for s in sections))
    return sections


def parse_constitution(full_text: str, act_metadata: dict) -> list[dict]:
    cleaned = clean_text(full_text)
    matches = list(CONSTITUTION_RE.finditer(cleaned))
    if not matches:
        log.warning("Constitution parser found no Article headers — falling back")
        return _paragraph_fallback(cleaned, act_metadata)

    sections = []
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(cleaned)
        article_num = m.group(1).strip()
        text = strip_footnotes(cleaned[start:end]).strip()
        if len(text) < 10:
            continue
        sections.append({
            "category": act_metadata.get("category", "constitution"),
            "act_name": act_metadata["act_name"],
            "short_name": act_metadata.get("short_name"),
            "year": act_metadata["year"],
            "ministry": act_metadata.get("ministry"),
            "chapter": "Constitution",
            "section_number": article_num.rstrip("."),
            "section_title": article_num,
            "topics": [],
            "text": text,
            "citation": f"{act_metadata['act_name']} \u203a {article_num}",
            "char_count": len(text),
            "is_schedule": False,
        })
    return sections


def parse_document(full_text: str, act_metadata: dict) -> list[dict]:
    """Single dispatch point — no recursion, no separate 'hybrid' branch
    that could call back into itself."""
    structure_type = detect_structure_type(act_metadata, full_text)
    if structure_type == "constitution":
        log.info("Using Constitution parser")
        sections = parse_constitution(full_text, act_metadata)
    else:
        sections = parse_sections(full_text, act_metadata)

    for s in sections:
        nesting = s["text"].count("(1)") + s["text"].count("(a)") + s["text"].count("(i)")
        s["structure"] = "deep_nested" if nesting > 15 else "normal"
    return sections


# --------------------------------------------------------------------------
# Post-processing helpers
# --------------------------------------------------------------------------
def _check_sequence_gaps(sections: list[dict]) -> None:
    """Log (don't drop) suspicious gaps in numeric section numbers — a
    signal, not proof, that a section failed to match."""
    nums = []
    for s in sections:
        m = re.match(r"(\d+)", s["section_number"])
        if m:
            nums.append(int(m.group(1)))
    nums = sorted(set(nums))
    gaps = [(a, b) for a, b in zip(nums, nums[1:]) if b - a > 1]
    if gaps:
        log.info("Possible missing sections: %s", gaps)


def _merge_duplicate_section_numbers(sections: list[dict]) -> list[dict]:
    """Keep the longer/more complete entry when the same section_number
    appears twice (e.g. a page-break split a real section into two
    header matches)."""
    by_number: dict[str, dict] = {}
    order: list[str] = []
    for s in sections:
        num = s["section_number"]
        if num not in by_number:
            by_number[num] = s
            order.append(num)
        elif len(s["text"]) > len(by_number[num]["text"]):
            by_number[num] = s
    return [by_number[n] for n in order]


def _paragraph_fallback(text: str, act_metadata: dict) -> list[dict]:
    paragraphs = [p.strip() for p in text.split("\n\n") if len(p.strip()) > 100]
    log.warning("  Using paragraph fallback: %d chunks", len(paragraphs))
    return [
        {
            "category": act_metadata.get("category", "unknown"),
            "act_name": act_metadata["act_name"],
            "short_name": act_metadata.get("short_name"),
            "year": act_metadata["year"],
            "ministry": act_metadata.get("ministry"),
            "section_number": f"P{i + 1}",
            "section_title": "Paragraph",
            "chapter": "Unknown",
            "text": para,
            "citation": f"{act_metadata['act_name']} \u203a Paragraph {i + 1}",
            "topics": act_metadata.get("relevance", []),
            "char_count": len(para),
            "is_schedule": False,
        }
        for i, para in enumerate(paragraphs)
    ]


def check_health(sections: list[dict]) -> list[str]:
    issues = []
    body = [s for s in sections if not s.get("is_schedule")]
    if len(body) < 5:
        issues.append("TOO FEW SECTIONS")
    nums = [s["section_number"] for s in body]
    if nums and len(set(nums)) < len(nums) * 0.9:
        issues.append("DUPLICATE SECTION NUMBERS")
    short_sections = sum(len(s["text"]) < 30 for s in body)
    if short_sections > max(5, len(body) * 0.10):
        issues.append(f"TOO MANY SHORT SECTIONS ({short_sections})")
    return issues


def score_sections(sections: list[dict]) -> int:
    body = [s for s in sections if not s.get("is_schedule")]
    score = 100
    if len(body) < 5:
        score -= 40
    nums = []
    for s in body:
        m = re.match(r"(\d+)", s["section_number"])
        if m:
            nums.append(int(m.group(1)))
    if nums and len(set(nums)) < len(nums) * 0.7:
        score -= 30
    avg_len = sum(len(s["text"]) for s in body) / max(len(body), 1)
    if avg_len < 200:
        score -= 20
    return max(score, 0)


# --------------------------------------------------------------------------
# Per-act driver
# --------------------------------------------------------------------------
@dataclass
class ParseResult:
    pdf_name: str
    out_path: Optional[Path] = None
    score: int = 0
    sections: list[dict] = field(default_factory=list)
    issues: list[str] = field(default_factory=list)
    ok: bool = False


def parse_act(pdf_path: Path, category: str) -> ParseResult:
    stem = pdf_path.stem
    result = ParseResult(pdf_name=pdf_path.name)
    act_metadata = load_act_metadata(stem, category)

    try:
        full_text = extract_text_from_pdf(pdf_path)
    except Exception as e:
        log.error("PDF extraction failed for %s: %s", pdf_path.name, e)
        return result

    sections = parse_document(full_text, act_metadata)
    if not sections:
        log.error("No sections extracted from %s", pdf_path.name)
        return result

    result.sections = sections
    result.issues = check_health(sections)
    result.score = score_sections(sections)
    if result.issues:
        log.warning("Health issues in %s: %s", pdf_path.name, result.issues)
    log.info("Parser score for %s: %d/100", pdf_path.name, result.score)

    out_dir = PARSED_DIR / category
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{stem}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(sections, f, ensure_ascii=False, indent=2)

    result.out_path = out_path
    result.ok = True
    log.info("Parsed %d sections (incl. schedules) -> %s", len(sections), out_path)
    return result


# --------------------------------------------------------------------------
# Batch driver
# --------------------------------------------------------------------------
def run(only_stem: Optional[str] = None, show_unregistered: bool = False) -> None:
    if not RAW_PDF_DIR.exists():
        log.error("Raw PDF directory not found: %s", RAW_PDF_DIR)
        return

    pdf_files = sorted(RAW_PDF_DIR.rglob("*.pdf"))
    if only_stem:
        pdf_files = [p for p in pdf_files if p.stem == only_stem]
    if not pdf_files:
        log.error("No matching PDFs found in %s", RAW_PDF_DIR)
        return

    if show_unregistered:
        unregistered = [p.name for p in pdf_files if p.stem not in ACT_REGISTRY]
        print(f"\n{len(unregistered)} PDF(s) without ACT_REGISTRY metadata:")
        for u in unregistered:
            print(f"  - {u}")
        print()

    log.info("Found %d PDF(s) to parse", len(pdf_files))
    success, failed, bad = [], [], []

    for pdf_path in pdf_files:
        category = pdf_path.parent.name
        log.info("Parsing: %s [%s]", pdf_path.name, category)
        result = parse_act(pdf_path, category)

        if not result.ok:
            failed.append(pdf_path.name)
            continue

        is_bad = bool(result.issues or result.score < 70)
        if is_bad:
            bad.append(pdf_path.name)
            failed.append(pdf_path.name)
        else:
            success.append(pdf_path.name)

    print("\n\u2500\u2500 Parse Summary \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500")
    print(f"  Succeeded : {len(success)}")
    for s in success:
        print(f"    \u2713 {s}")
    if failed:
        print(f"  Failed    : {len(failed)}")
        for f in failed:
            print(f"    \u2717 {f}")
    print("\u2500" * 48)
    if bad:
        print("\n\u274c Needs review (health issues or score < 70):")
        for b in bad:
            print("  -", b)


def main() -> None:
    parser = argparse.ArgumentParser(description="Parse India Code Act PDFs into structured JSON.")
    parser.add_argument("--act", help="Only parse the PDF with this stem (filename without .pdf)")
    parser.add_argument("--verbose", action="store_true", help="Enable debug-level logging")
    parser.add_argument("--show-unregistered", action="store_true",
                         help="List PDFs found on disk that have no ACT_REGISTRY entry")
    args = parser.parse_args()

    configure_logging(args.verbose)
    run(only_stem=args.act, show_unregistered=args.show_unregistered)


if __name__ == "__main__":
    main()