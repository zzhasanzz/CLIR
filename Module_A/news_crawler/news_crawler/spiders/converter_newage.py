import csv
import json
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
# points to: news_crawler/news_crawler/

input_csv = os.path.join(BASE_DIR, "newage_raw_documents.csv")
output_jsonl = os.path.join(BASE_DIR, "english_corpus.jsonl")


DEFAULT_AUTHOR = "New Age Desk"

def format_date(date_str):
    """
    Input:  2026-01-10
    Output: 10 January 2026
    """
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return dt.strftime("%d %B %Y")
    except:
        return date_str  # fallback if format changes

# --------------------------------------------------
# 1️⃣ Load existing URLs for deduplication
# --------------------------------------------------
existing_urls = set()

if os.path.exists(output_jsonl):
    with open(output_jsonl, "r", encoding="utf-8") as f:
        for line in f:
            try:
                obj = json.loads(line)
                if "url" in obj:
                    existing_urls.add(obj["url"])
            except:
                pass

print(f"🔍 Found {len(existing_urls)} existing documents")

# --------------------------------------------------
# 2️⃣ Process CSV & append non-duplicates
# --------------------------------------------------
added = 0
skipped = 0

with open(input_csv, "r", encoding="utf-8", newline="") as fin, \
     open(output_jsonl, "a", encoding="utf-8") as fout:

    reader = csv.DictReader(fin)

    for row_num, row in enumerate(reader, 2):  # header is row 1
        url = row.get("url", "").strip()

        if not url or url in existing_urls:
            skipped += 1
            continue

        try:
            normalized = {
                "title": row.get("title", "").strip(),
                "body": row.get("body", "").strip(),
                "url": url,
                "date": format_date(row.get("date", "")),
                "language": row.get("language", "en"),
                "author": DEFAULT_AUTHOR,
                "section": row.get("category", "").lower(),
                "tokens": int(row.get("tokens", 0))
            }

            fout.write(json.dumps(normalized, ensure_ascii=False) + "\n")
            existing_urls.add(url)
            added += 1

        except Exception as e:
            print(f"❌ Error on CSV row {row_num}: {e}")

print(f"✅ Added {added} new documents")
print(f"⏭️ Skipped {skipped} duplicates")
