import json
import os
from datetime import datetime

# --------------------------------------------------
# PATH FIX
# --------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))

OUTPUT_JSONL = os.path.join(BASE_DIR, "bangla_corpus.jsonl")

PROTHOMALO_FILES = [
    "prothomalo_sports.json",
    "prothomalo_politics.json",
    "prothomalo_world.json",
    "prothomalo_latest.json",
    "prothomalo_entertainment.json",
    "prothomalo_business.json",
    "prothomalo_bangladesh.json",
]

MAX_PER_FILE = 300
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

def iso_to_bangla_date(iso_str):
    """
    Input: ISO string or None
    Output: Bangla formatted date or ""
    """
    if not iso_str or not isinstance(iso_str, str):
        return ""

    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", ""))
    except Exception:
        return iso_str.strip()

    eng = dt.strftime("%d %B %Y, %H:%M")

    for en, bn in BN_MONTHS.items():
        eng = eng.replace(en, bn)

    return eng.translate(BN_DIGITS)

# --------------------------------------------------
# SAFE STRING HELPER (CRITICAL)
# --------------------------------------------------
def safe_str(x):
    """
    Converts None / non-string → safe cleaned string
    """
    if not x:
        return ""
    return str(x).strip()

# --------------------------------------------------
# Load existing URLs (dedup)
# --------------------------------------------------
existing_urls = set()

if os.path.exists(OUTPUT_JSONL):
    with open(OUTPUT_JSONL, "r", encoding="utf-8") as f:
        for line in f:
            try:
                obj = json.loads(line)
                if "url" in obj:
                    existing_urls.add(obj["url"])
            except:
                pass

print(f"🔍 Existing documents: {len(existing_urls)}")

# --------------------------------------------------
# Convert Prothom Alo JSONs
# --------------------------------------------------
total_added = 0
total_skipped = 0

for filename in PROTHOMALO_FILES:
    path = os.path.join(BASE_DIR, filename)

    if not os.path.exists(path):
        print(f"⚠️ Missing file: {filename}")
        continue

    with open(path, "r", encoding="utf-8") as f:
        articles = json.load(f)

    print(f"📂 Processing {filename} ({len(articles)} articles)")

    added_here = 0

    with open(OUTPUT_JSONL, "a", encoding="utf-8") as out:
        for art in articles:
            if added_here >= MAX_PER_FILE:
                break

            url = safe_str(art.get("url"))
            if not url or url in existing_urls:
                total_skipped += 1
                continue

            title = safe_str(art.get("title"))
            body = safe_str(art.get("body"))

            if not title or not body:
                total_skipped += 1
                continue

            author = safe_str(art.get("author")) or DEFAULT_AUTHOR
            section = safe_str(art.get("section")).lower()

            doc = {
                "title": title,
                "body": body,
                "url": url,
                "date": iso_to_bangla_date(art.get("date")),
                "language": "bn",
                "author": author,
                "tokens": len(body.split()),
                "section": section
            }

            out.write(json.dumps(doc, ensure_ascii=False) + "\n")
            existing_urls.add(url)
            added_here += 1
            total_added += 1

    print(f"   ➕ Added {added_here}")

# --------------------------------------------------
# Report
# --------------------------------------------------
print("✅ Prothom Alo conversion finished")
print(f"➕ Total added: {total_added}")
print(f"⏭️ Skipped (duplicates / bad rows): {total_skipped}")
