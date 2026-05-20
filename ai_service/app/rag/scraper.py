"""
scraper.py — Downloads Indian legal Acts as PDFs from authoritative sources.

Sources (in priority order):
  1. legislative.gov.in  — Ministry of Law, official gazette PDFs
  2. indiacode.nic.in    — India Code repository
  3. labour.gov.in       — Labour Ministry for labour Acts

Run:
    python scraper.py

Downloads PDFs into datasets/raw_pdfs/<category>/
"""

import requests
import time
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parents[3]
RAW_PDF_DIR = BASE_DIR / "datasets" / "raw_pdfs"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/pdf,*/*",
    "Accept-Language": "en-US,en;q=0.9",
}

# ── Legal Acts to download ────────────────────────────────────────────────────
# Format:
#   category     : folder under datasets/raw_pdfs/
#   filename     : saved as this name (no extension)
#   urls         : tried in order; first 200 wins
#   description  : human-readable label for logs
# ─────────────────────────────────────────────────────────────────────────────
ACTS = [
    {
        "category": "consumer",
        "filename": "consumer_protection_act_2019",
        "description": "Consumer Protection Act, 2019",
        "urls": [
            "https://legislative.gov.in/sites/default/files/A2019-35.pdf",
            "https://www.indiacode.nic.in/bitstream/123456789/13451/1/consumer_protection_act_2019.pdf",
            "https://consumeraffairs.nic.in/sites/default/files/CP%20Act%202019.pdf",
        ],
    },
    {
        "category": "labour",
        "filename": "code_on_wages_2019",
        "description": "Code on Wages, 2019",
        "urls": [
            "https://legislative.gov.in/sites/default/files/A2019-29.pdf",
            "https://labour.gov.in/sites/default/files/TheCodeonWages2019.pdf",
            "https://www.indiacode.nic.in/bitstream/123456789/13212/1/a2019-29.pdf",
        ],
    },
    {
        "category": "labour",
        "filename": "payment_of_wages_act_1936",
        "description": "Payment of Wages Act, 1936",
        "urls": [
            "https://legislative.gov.in/sites/default/files/A1936-4.pdf",
            "https://www.indiacode.nic.in/bitstream/123456789/1485/1/193604.pdf",
        ],
    },
    {
        "category": "tenant",
        "filename": "transfer_of_property_act_1882",
        "description": "Transfer of Property Act, 1882 (Sections 105–117: Leases)",
        "urls": [
            "https://legislative.gov.in/sites/default/files/A1882-4.pdf",
            "https://www.indiacode.nic.in/bitstream/123456789/2338/1/188204.pdf",
        ],
    },
    {
        "category": "criminal",
        "filename": "bharatiya_nyaya_sanhita_2023",
        "description": "Bharatiya Nyaya Sanhita, 2023 (replaces IPC)",
        "urls": [
            "https://legislative.gov.in/sites/default/files/A2023-45.pdf",
            "https://www.indiacode.nic.in/bitstream/123456789/20062/1/a2023-45.pdf",
        ],
    },
    {
        "category": "consumer",
        "filename": "legal_metrology_act_2009",
        "description": "Legal Metrology Act, 2009 (weights, measures, MRP)",
        "urls": [
            "https://legislative.gov.in/sites/default/files/A2009-1.pdf",
            "https://www.indiacode.nic.in/bitstream/123456789/5466/1/200901.pdf",
        ],
    },
]


def download_pdf(act: dict) -> bool:
    """
    Try each URL in order. Save on first successful download.
    Returns True if downloaded, False if all URLs failed.
    """
    dest_dir = RAW_PDF_DIR / act["category"]
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / f"{act['filename']}.pdf"

    if dest_path.exists():
        log.info("Already exists, skipping: %s", dest_path.name)
        return True

    for url in act["urls"]:
        try:
            log.info("Trying: %s", url)
            response = requests.get(url, headers=HEADERS, timeout=30, stream=True, allow_redirects=True)
            if response.status_code == 200 and "pdf" in response.headers.get("content-type", "").lower():
                log.info("Final URL: %s", response.url)
            if response.status_code == 200:
                content_type = response.headers.get("content-type", "")
                if "pdf" not in content_type and "octet-stream" not in content_type:
                    log.warning("Unexpected content-type '%s' from %s", content_type, url)
                    continue

                with open(dest_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)

                size_kb = dest_path.stat().st_size / 1024
                log.info("✓ Downloaded %s (%.1f KB) → %s", act["description"], size_kb, dest_path)
                return True
            else:
                log.warning("HTTP %s from %s", response.status_code, url)

        except requests.RequestException as e:
            log.warning("Request failed for %s: %s", url, e)

        time.sleep(1)  # polite delay between attempts

    log.error("✗ All URLs failed for: %s", act["description"])
    return False


def run():
    log.info("Starting download of %d Acts...", len(ACTS))
    log.info("Output directory: %s", RAW_PDF_DIR)

    success, failed = [], []

    for act in ACTS:
        ok = download_pdf(act)
        (success if ok else failed).append(act["description"])
        time.sleep(0.5)

    print("\n── Download Summary ──────────────────────────")
    print(f"  Succeeded : {len(success)}")
    for s in success:
        print(f"    ✓ {s}")
    if failed:
        print(f"  Failed    : {len(failed)}")
        for f in failed:
            print(f"    ✗ {f}")
        print("\n  For failed Acts, manually download the PDF")
        print("  from https://legislative.gov.in or https://www.indiacode.nic.in")
        print("  and place it in datasets/raw_pdfs/<category>/")
    print("─────────────────────────────────────────────")


if __name__ == "__main__":
    run()