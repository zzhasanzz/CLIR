import csv
import json
import os

# --------------------------------------------------
# PATH FIX (same pattern as your other converters)
# --------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# go up TWO levels → news_crawler/news_crawler/
BASE_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))

INPUT_CSV = os.path.join(BASE_DIR, "dhakapost.csv")
OUTPUT_JSONL = os.path.join(BASE_DIR, "bangla_corpus.jsonl")

DEFAULT_AUTHOR = "Dhaka Post"

# --------------------------------------------------
# Helpers
# --------------------------------------------------
def safe_str(x):
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
# Convert CSV → JSONL
# --------------------------------------------------
added = 0
skipped = 0

with open(INPUT_CSV, "r", encoding="utf-8", newline="") as fin, \
     open(OUTPUT_JSONL, "a", encoding="utf-8") as fout:

    reader = csv.DictReader(fin)

    for row_num, row in enumerate(reader, start=2):
        url = safe_str(row.get("url"))

        if not url or url in existing_urls:
            skipped += 1
            continue

        title = safe_str(row.get("title"))
        body = safe_str(row.get("body"))

        if not title or not body:
            skipped += 1
            continue

        author = safe_str(row.get("author")) or DEFAULT_AUTHOR
        section = safe_str(row.get("section")).lower()
        language = safe_str(row.get("language")) or "bn"

        # token handling: trust CSV if present, else recompute
        token_raw = safe_str(row.get("tokens"))
        if token_raw.isdigit():
            tokens = int(token_raw)
        else:
            tokens = len(body.split())

        doc = {
            "title": title,
            "body": body,
            "url": url,
            "date": safe_str(row.get("date")),
            "language": language,
            "author": author,
            "tokens": tokens,
            "section": section
        }

        fout.write(json.dumps(doc, ensure_ascii=False) + "\n")
        existing_urls.add(url)
        added += 1

# --------------------------------------------------
# Report
# --------------------------------------------------
print("✅ DhakaPost CSV conversion finished")
print(f"➕ Added: {added}")
print(f"⏭️ Skipped (duplicates / bad rows): {skipped}")
