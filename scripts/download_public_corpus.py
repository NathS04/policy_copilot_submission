"""Download a small, OGL-licensed public guidance corpus for the
Public Guidance Transfer Stress Test (Section 4.11 in the dissertation).

Sources are restricted to Crown-copyright, Open Government Licence v3.0
material from three UK public bodies whose terms permit reuse with
attribution:

  - National Cyber Security Centre (NCSC)         -- cyber security guidance
  - Information Commissioner's Office (ICO)       -- UK GDPR / data protection
  - ACAS                                          -- employment guidance

For each URL the script:
  1. Fetches the HTML page with a polite UA + 10s timeout
  2. Extracts the main article text using a small set of CSS selectors
     specific to each site (no scraping libraries -- only stdlib + a
     minimal HTML-stripping fallback if BeautifulSoup is unavailable)
  3. Saves a sanitised .txt file under
     ``data/public_transfer_corpus/raw/<doc_id>.txt``
  4. Records URL, title, license, access date, and content hash in
     ``data/public_transfer_corpus/provenance.csv``

The script is idempotent: existing .txt files are not re-downloaded
unless ``--refresh`` is passed.

Usage
-----

    python scripts/download_public_corpus.py
    python scripts/download_public_corpus.py --refresh
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import html
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import List


HERE = Path(__file__).resolve().parent.parent
RAW_DIR = HERE / "data" / "public_transfer_corpus" / "raw"
PROVENANCE_CSV = HERE / "data" / "public_transfer_corpus" / "provenance.csv"

UA = (
    "Mozilla/5.0 (compatible; PolicyCopilotResearch/1.0; "
    "academic dissertation; OGL v3.0 reuse)"
)


# Curated list of OGL-licensed public guidance pages.
# Each entry: (doc_id, source_org, title, url, theme, included_sections, exclusions, notes)
SOURCES: list[dict] = [
    {
        "doc_id": "ncsc_password_admin_guidance",
        "source_org": "NCSC",
        "title": "Password administration for system owners",
        "url": "https://www.ncsc.gov.uk/collection/passwords",
        "theme": "cyber security",
        "license": "Open Government Licence v3.0",
        "included_sections": "Main article body",
        "exclusions": "Navigation, footer, related-content widgets",
        "notes": "NCSC terms permit reuse with attribution and OGL link.",
    },
    {
        "doc_id": "ncsc_byod_guidance",
        "source_org": "NCSC",
        "title": "Bring your own device (BYOD) guidance",
        "url": "https://www.ncsc.gov.uk/collection/device-security-guidance/bring-your-own-device",
        "theme": "cyber security",
        "license": "Open Government Licence v3.0",
        "included_sections": "Main article body",
        "exclusions": "Navigation, footer, related-content widgets",
        "notes": "Aligned with synthetic corpus IT Security Addendum.",
    },
    {
        "doc_id": "ico_data_protection_principles",
        "source_org": "ICO",
        "title": "Data protection principles",
        "url": "https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/data-protection-principles/",
        "theme": "data protection",
        "license": "Open Government Licence v3.0",
        "included_sections": "Main article body",
        "exclusions": "Navigation, footer, in-page widgets",
        "notes": "ICO website content is OGL v3.0 unless otherwise stated.",
    },
    {
        "doc_id": "ico_lawful_basis",
        "source_org": "ICO",
        "title": "Lawful basis for processing (UK GDPR)",
        "url": "https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/lawful-basis/",
        "theme": "data protection",
        "license": "Open Government Licence v3.0",
        "included_sections": "Main article body",
        "exclusions": "Navigation, footer, in-page widgets",
        "notes": "Closest analogue to handbook \"data handling lawfulness\" guidance.",
    },
    {
        "doc_id": "ico_individual_rights_overview",
        "source_org": "ICO",
        "title": "Individual rights (UK GDPR)",
        "url": "https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/individual-rights/individual-rights/",
        "theme": "data protection",
        "license": "Open Government Licence v3.0",
        "included_sections": "Main article body",
        "exclusions": "Navigation, footer, in-page widgets",
        "notes": "Closest analogue to handbook \"data subject rights\" guidance.",
    },
    {
        "doc_id": "acas_disciplinary_procedure",
        "source_org": "ACAS",
        "title": "Disciplinary procedure: step by step",
        "url": "https://www.acas.org.uk/disciplinary-procedure-step-by-step",
        "theme": "employment",
        "license": "Open Government Licence v3.0",
        "included_sections": "Main article body",
        "exclusions": "Navigation, footer, related-pages widget",
        "notes": "Crown copyright per ACAS website terms.",
    },
    {
        "doc_id": "acas_holiday_pay",
        "source_org": "ACAS",
        "title": "Holiday entitlement and pay",
        "url": "https://www.acas.org.uk/checking-holiday-entitlement",
        "theme": "employment",
        "license": "Open Government Licence v3.0",
        "included_sections": "Main article body",
        "exclusions": "Navigation, footer, related-pages widget",
        "notes": "Aligned with synthetic Employee Handbook leave policy.",
    },
    {
        "doc_id": "acas_remote_hybrid_working",
        "source_org": "ACAS",
        "title": "Working from home and hybrid working",
        "url": "https://www.acas.org.uk/working-from-home-and-hybrid-working",
        "theme": "employment",
        "license": "Open Government Licence v3.0",
        "included_sections": "Main article body",
        "exclusions": "Navigation, footer, related-pages widget",
        "notes": "Aligned with synthetic Employee Handbook remote-work section.",
    },
]


def fetch(url: str, timeout: float = 15.0) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        charset = r.headers.get_content_charset() or "utf-8"
        return r.read().decode(charset, errors="replace")


# ----- HTML extraction (stdlib only) ---------------------------------

# Strip common surrounding wrappers that are not main content.
DROP_TAG_RE = re.compile(
    r"<(script|style|noscript|nav|header|footer|aside|form)\b[^>]*>"
    r".*?</\1>",
    re.IGNORECASE | re.DOTALL,
)
DROP_COMMENTS_RE = re.compile(r"<!--.*?-->", re.DOTALL)
ANY_TAG_RE = re.compile(r"<[^>]+>")
WS_COLLAPSE_RE = re.compile(r"\s+")


def html_to_text(raw_html: str) -> str:
    """Crude but reliable HTML -> plain-text reduction.

    1. Drop scripts / styles / nav / header / footer / aside / form blocks.
    2. Drop HTML comments.
    3. Replace block-level closers with newlines so paragraph
       boundaries survive.
    4. Strip remaining tags.
    5. Decode HTML entities and collapse runs of whitespace.

    The synthetic corpus's ingest pipeline expects double-newline
    paragraph separators, so we preserve those between block elements.
    """
    s = DROP_COMMENTS_RE.sub("", raw_html)
    s = DROP_TAG_RE.sub("", s)
    # Insert newlines around block elements
    block_close = re.compile(
        r"</(p|h1|h2|h3|h4|h5|h6|li|tr|table|section|article|div|blockquote)>",
        re.IGNORECASE,
    )
    s = block_close.sub(r"\n\n", s)
    s = re.sub(r"<br\s*/?>", "\n", s, flags=re.IGNORECASE)
    s = ANY_TAG_RE.sub("", s)
    s = html.unescape(s)
    # Normalise line endings
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    # Collapse 3+ blank lines into 2
    s = re.sub(r"\n{3,}", "\n\n", s)
    # Trim trailing whitespace per line
    s = "\n".join(line.rstrip() for line in s.split("\n"))
    return s.strip()


def slim_to_main_content(text: str) -> str:
    """Drop obvious chrome lines that survived HTML stripping
    (cookie banners, navigation breadcrumbs, "you are here" links,
    footer phrases, common boilerplate)."""
    drop_substrings = [
        "Skip to navigation", "Skip to main content", "Cookies on this site",
        "Accept all cookies", "Reject all cookies", "Manage cookies",
        "Sign in", "Search this website", "Subscribe to our",
        "Open Government Licence", "Crown copyright",
        "Was this page helpful", "Updated:", "Last updated",
        "Print this page", "Email this page",
        "All content is available under",
        "\u00a9 ICO", "\u00a9 Acas", "\u00a9 NCSC",
        "Hide this message", "Hide message",
    ]
    cleaned_lines: list[str] = []
    for line in text.split("\n"):
        stripped = line.strip()
        if not stripped:
            cleaned_lines.append("")
            continue
        if any(d in stripped for d in drop_substrings):
            continue
        # Short navigation-style fragments
        if len(stripped) < 4:
            continue
        cleaned_lines.append(stripped)
    out = "\n".join(cleaned_lines)
    out = re.sub(r"\n{3,}", "\n\n", out).strip()
    return out


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def write_provenance(rows: list[dict]) -> None:
    PROVENANCE_CSV.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "doc_id", "source_org", "title", "url", "theme", "license",
        "access_date", "char_len", "content_sha256_12",
        "included_sections", "exclusions", "notes",
    ]
    with PROVENANCE_CSV.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fields})


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--refresh", action="store_true",
                   help="Re-download even if the .txt already exists")
    p.add_argument("--sleep", type=float, default=1.0,
                   help="Polite delay between requests (seconds)")
    args = p.parse_args()

    RAW_DIR.mkdir(parents=True, exist_ok=True)

    rows: list[dict] = []
    today = datetime.now(timezone.utc).date().isoformat()

    for src in SOURCES:
        out_path = RAW_DIR / f"{src['doc_id']}.txt"
        if out_path.exists() and not args.refresh:
            print(f"  skip (cached): {out_path.name}")
            text = out_path.read_text(encoding="utf-8")
        else:
            print(f"  fetching: {src['url']}")
            try:
                raw = fetch(src["url"])
            except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
                print(f"    FAILED: {e}", file=sys.stderr)
                continue
            text = slim_to_main_content(html_to_text(raw))
            out_path.write_text(text, encoding="utf-8")
            time.sleep(args.sleep)

        rows.append({
            "doc_id": src["doc_id"],
            "source_org": src["source_org"],
            "title": src["title"],
            "url": src["url"],
            "theme": src["theme"],
            "license": src["license"],
            "access_date": today,
            "char_len": len(text),
            "content_sha256_12": content_hash(text),
            "included_sections": src["included_sections"],
            "exclusions": src["exclusions"],
            "notes": src["notes"],
        })

    write_provenance(rows)
    print(f"\nWrote {PROVENANCE_CSV} ({len(rows)} rows)")
    print(f"Raw text in {RAW_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
