import json
from datetime import datetime
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
# points to: news_crawler/news_crawler/

input_file = os.path.join(BASE_DIR, "daily_sun_raw_documents.jsonl")
output_file = os.path.join(BASE_DIR, "english_corpus.jsonl")

DEFAULT_AUTHOR = "Daily Sun Desk"

def format_date(date_str):
    """
    Input:  2026-01-22 13:32:00
    Output: 22 January 2026, 01:32 PM
    """
    dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    return dt.strftime("%d %B %Y, %I:%M %p")

# --------------------------------------------------
# 1️⃣ Load existing URLs (for deduplication)
# --------------------------------------------------
existing_urls = set()

if os.path.exists(output_file):
    with open(output_file, "r", encoding="utf-8") as f:
        for line in f:
            try:
                obj = json.loads(line)
                if "url" in obj:
                    existing_urls.add(obj["url"])
            except:
                pass  # skip corrupted lines safely

print(f"🔍 Found {len(existing_urls)} existing documents")

# --------------------------------------------------
# 2️⃣ Process input & append new docs only
# --------------------------------------------------
added = 0
skipped = 0

with open(input_file, "r", encoding="utf-8") as fin, \
     open(output_file, "a", encoding="utf-8") as fout:

    for line_num, line in enumerate(fin, 1):
        try:
            doc = json.loads(line)
            url = doc.get("url")

            if not url or url in existing_urls:
                skipped += 1
                continue

            normalized = {
                "title": doc.get("title", "").strip(),
                "body": doc.get("body", "").strip(),
                "url": url,
                "date": format_date(doc["date"]) if "date" in doc else "",
                "language": doc.get("language", "en"),
                "author": DEFAULT_AUTHOR,
                "section": doc.get("category", "").lower(),
                "tokens": len(doc.get("tokens", []))
            }

            fout.write(json.dumps(normalized, ensure_ascii=False) + "\n")
            existing_urls.add(url)
            added += 1

        except Exception as e:
            print(f"❌ Error on line {line_num}: {e}")

print(f"✅ Added {added} new documents")
print(f"⏭️ Skipped {skipped} duplicates")
