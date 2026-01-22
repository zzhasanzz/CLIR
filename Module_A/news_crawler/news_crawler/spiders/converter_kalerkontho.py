import csv
import json
import os
import re
import html
from datetime import datetime
from urllib.parse import urlparse, urlunparse
from bs4 import BeautifulSoup

# --------------------------------------------------
# Paths
# --------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
input_csv = os.path.join(BASE_DIR, "kalerkantho_raw_documents.csv")
output_jsonl = os.path.join(BASE_DIR, "bangla_corpus.jsonl")

DEFAULT_AUTHOR = "নিজস্ব প্রতিবেদক"

# --------------------------------------------------
# Bangla date helpers
# --------------------------------------------------
BN_DIGITS = str.maketrans("0123456789", "০১২৩৪৫৬৭৮৯")

BN_MONTHS = {
    "January": "জানুয়ারি",
    "February": "ফেব্রুয়ারি",
    "March": "মার্চ",
    "April": "এপ্রিল",
    "May": "মে",
    "June": "জুন",
    "July": "জুলাই",
    "August": "আগস্ট",
    "September": "সেপ্টেম্বর",
    "October": "অক্টোবর",
    "November": "নভেম্বর",
    "December": "ডিসেম্বর"
}

def to_bangla_date(date_str: str) -> str:
    """
    Input: 2026-01-19 08:37:00
    Output: ১৯ জানুয়ারি ২০২৬, ০৮:৩৭
    """
    try:
        dt = datetime.strptime(date_str.strip(), "%Y-%m-%d %H:%M:%S")
    except:
        return date_str.strip()

    eng = dt.strftime("%d %B %Y, %H:%M")

    for en, bn in BN_MONTHS.items():
        eng = eng.replace(en, bn)

    return eng.translate(BN_DIGITS)

# --------------------------------------------------
# Helpers
# --------------------------------------------------
def normalize_url(url: str) -> str:
    if not url:
        return ""

    parsed = urlparse(url.strip())
    normalized = parsed._replace(
        scheme="https",
        query="",
        fragment=""
    )
    return urlunparse(normalized).rstrip("/")


def clean_html(text: str) -> str:
    if not text:
        return ""

    text = html.unescape(text)
    soup = BeautifulSoup(text, "lxml")

    for tag in soup.find_all([
        "script", "style", "img", "figure", "iframe",
        "svg", "button", "input", "form", "nav"
    ]):
        tag.decompose()

    cleaned = soup.get_text(separator=" ")
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    return cleaned

# --------------------------------------------------
# 1️⃣ Load existing URLs (dedup by URL ONLY)
# --------------------------------------------------
existing_urls = set()

if os.path.exists(output_jsonl):
    with open(output_jsonl, "r", encoding="utf-8") as f:
        for line in f:
            try:
                obj = json.loads(line)
                url = normalize_url(obj.get("url", ""))
                if url:
                    existing_urls.add(url)
            except:
                pass

print(f"🔍 Existing documents: {len(existing_urls)}")

# --------------------------------------------------
# 2️⃣ Convert CSV → JSONL
# --------------------------------------------------
added = 0
skipped_dup = 0
skipped_empty = 0
skipped_bad = 0

with open(input_csv, "r", encoding="utf-8", newline="") as fin, \
     open(output_jsonl, "a", encoding="utf-8") as fout:

    reader = csv.DictReader(fin)

    for row in reader:
        url = normalize_url(row.get("url", ""))

        if not url:
            skipped_bad += 1
            continue

        if url in existing_urls:
            skipped_dup += 1
            continue

        body_clean = clean_html(row.get("body", ""))

        if not body_clean:
            skipped_empty += 1
            continue

        author = row.get("author", "").strip()
        if not author:
            author = DEFAULT_AUTHOR

        doc = {
            "title": row.get("title", "").strip(),
            "body": body_clean,
            "url": url,
            "date": to_bangla_date(row.get("date", "")),
            "language": "bn",
            "author": author,
            "tokens": len(body_clean.split()),
            "section": row.get("category", "").lower()
        }

        fout.write(json.dumps(doc, ensure_ascii=False) + "\n")
        existing_urls.add(url)
        added += 1

# --------------------------------------------------
# Report
# --------------------------------------------------
print("✅ Conversion finished")
print(f"➕ Added: {added}")
print(f"⏭️ Skipped (duplicates): {skipped_dup}")
print(f"⏭️ Skipped (empty body): {skipped_empty}")
print(f"⏭️ Skipped (bad rows): {skipped_bad}")
