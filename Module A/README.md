# Module A

A specialized web scraping system designed for Windows environments to build a bilingual (Bangla & English) news corpus from major Bangladeshi news portals. This system was used to generate the **CLIR Dataset**.

---

## Dataset Access
If you do not wish to run the scrapers manually, the complete processed dataset (Bangla & English) is available here:
**[CLIR Dataset on Kaggle](https://www.kaggle.com/datasets/tanjilhasankhan/clir-dataset)**
Visit this link and inside the dataset's news directory the *jsonl files can be found
Embeddings, Transliterations, Annotations are also added.

---

## Overview
This module automates the collection of news articles from 10+ Bangladeshi news websites. It is optimized for Windows 10/11 using Python and Scrapy to build:
- **Bangla Corpus**: ~5,700 articles (Prothom Alo, Bangla Tribune, etc.)
- **English Corpus**: ~3,800 articles (The Daily Star, Dhaka Tribune, etc.)

Each article includes metadata: Title, Body, URL, Date, Language, Author, Section, and Token Count.

---

## Windows System Requirements
- **OS**: Windows 10 or 11 (64-bit)
- **Python**: 3.8 or higher ([Download from Python.org](https://www.python.org/downloads/windows/))
- **Terminal**: PowerShell (Recommended)
- **Storage**: 2GB free space

---

## Installation Guide

### 1. Python Setup
During installation, you **must** check the box: **"Add Python to PATH"**.

### 2. Install Scrapy & Dependencies
Open **PowerShell** and run:
```powershell
# Install core scraping framework
pip install scrapy cloudscraper itemadapter

# Install requirements for standalone scripts (New Age, Daily Sun)
pip install aiohttp asyncio beautifulsoup4 nest-asyncio tqdm lxml
```

### 3. Project Setup
```powershell
git clone https://github.com/zzhasanzz/CLIR.git
cd news_crawler\news_crawler
```

---

## Scraping Guide

### Phase 1: Bangla News Sources
Run these commands from the `news_crawler\news_crawler` directory:

| Source | Command |
| :--- | :--- |
| **Bangla Tribune** | `scrapy crawl banglatribune_latest -o ../data/bt.jsonl` |
| **Prothom Alo** | `scrapy crawl prothomalo_latest -o ../data/pa.json` |
| **Dhaka Post** | `scrapy crawl dhakapost_alltopics_500 -o ../data/dp.csv` |
| **Kaler Kantho** | `python spiders/kalerkantho_crawler.py` |

### Phase 2: English News Sources

| Source | Command |
| :--- | :--- |
| **Dhaka Tribune** | `scrapy crawl dhakatribune_bangladesh -o ../data/dt.jsonl` |
| **The Daily Star** | `scrapy crawl thedailystar_economy -o ../data/tds.jsonl` |
| **Daily New Nation** | `scrapy crawl dailynewnation_national -o ../data/dnn.jsonl` |
| **Daily Sun** | `python spiders/daily_sun_crawler.py` |
| **New Age** | `python spiders/newage_crawler.py` |

---

## Data Unification (Windows Commands)
Since different sites output different formats (CSV/JSON), use the provided converters to unify them into the final `.jsonl` format used in the Kaggle dataset:

```powershell
# Convert Prothom Alo JSON to Unified Format
python spiders/converter_prothomalo.py

# Convert Dhaka Post CSV to Unified Format
python spiders/converter_dhakapost.py

# Convert Daily Sun results
python spiders/converter_dailysun.py
```

---

**Last Updated:** February 2026  
**Dataset Source:** [Kaggle/tanjilhasankhan/clir-dataset](https://www.kaggle.com/datasets/tanjilhasankhan/clir-dataset)