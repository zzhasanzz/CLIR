This README provides a comprehensive overview of the **Cross-Lingual Information Retrieval (CLIR)** pipeline for Bangla and English, specifically focusing on the advanced **Query Processing** logic.

---

# Cross-Lingual Query Processor (Bangla-English)

This repository contains a sophisticated query processing pipeline designed to bridge the linguistic gap between Bangla and English. It uses a hybrid approach combining **Sparse (BM25-ready)** and **Dense (Semantic)** representations.

## How to Set Up on Kaggle

To run this notebook successfully, you need to upload your pre-computed embeddings and corpora as Kaggle Datasets.

### 1. Prepare your files
Ensure you have the following files ready from your local preprocessing:
*   **Corpora:** `bangla_corpus.jsonl`, `english_corpus.jsonl`
*   **Embeddings:** `bangla_embeddings.npy`, `english_embeddings.npy`
*   **Mapping:** `bangla_doc_ids.json`, `english_doc_ids.json`
*   **Knowledge Base:** `transliteration.json` (manual dict) and `transliteration_or_similar.json` (auto-generated dict).

### 2. Create Kaggle Datasets
1.  Go to [Kaggle Datasets](https://www.kaggle.com/datasets) and click **"New Dataset"**.
2.  **Dataset A (/kaggle/input/clir-news):** Upload the `.jsonl` files.
3.  **Dataset B (/kaggle/input/labse-embeddings):** Upload the `.npy` files.
4.  **Dataset C (/kaggle/input/doc-ids):** Upload the `bangla_doc_ids.json` and `english_doc_ids.json` mapping files.
5.  **Dataset D (/kaggle/input/transliteration-or-similar):** Upload the two transliteration `.json` files.
6.  In your Kaggle Notebook, click **"Add Data"** in the right sidebar and search for your newly created datasets.

---

## 🛠 The Query Processing Workflow

The `QueryProcessor` class implements an 11-step pipeline to transform a raw, potentially mixed-script query into a high-recall retrieval object.

### 1. Language Detection
Uses Unicode range analysis (Bangla vs. Latin) to detect the dominant language. It handles mixed-script queries by calculating the ratio of Bangla characters.

### 2. Normalization
*   **NFC Normalization:** Ensures Bangla Unicode characters are consistent.
*   **Stopword Removal:** Strips high-frequency, low-meaning words (e.g., "এবং", "the") to clean the sparse index.

### 3. Named Entity Recognition (NER)
Uses the `xlm-roberta-large-ner-hrl` model to identify Persons, Organizations, and Locations. This ensures proper nouns are treated with high priority.

### 4. Cross-Lingual Entity Mapping
Extracted entities are translated specifically. For example, if "শেখ হাসিনা" is detected, the system maps it to "Sheikh Hasina" to ensure matching in the English corpus.

### 5. Bangla Morphology (Stemming)
A custom rule-based stemmer handles Bangla's inflectional nature. It identifies roots by stripping common suffixes (যেমন: `নির্বাচনের` -> `নির্বাচন`) and handles variations like `নির্বাচন` -> `নির্বাচনী`.

### 6. Transliteration Expansion (Dual Layer)
This is a critical bridge for news retrieval:
*   **Manual Layer:** High-frequency news terms (e.g., "Cricket" -> "ক্রিকেট").
*   **Auto-Semantic Layer:** Uses **LaBSE** to find words in the English and Bangla vocabularies that have a cosine similarity > 0.83 (e.g., finding that "vaccine" and "ভ্যাকসিন" are semantically identical).

### 7. Full Query Translation
The entire normalized query is translated to the target language using `deep_translator` library to provide a base for the cross-lingual search.

### 8. Unified Representation
The processor creates a **"Bag of Augmented Terms"** including:
`[Original Tokens] + [Synonyms] + [Morphological Roots] + [Translated Tokens] + [Transliterated Terms] + [Mapped Entities]`

---

## Retrieval Strategy

### Sparse Retrieval (BM25)
The `bm25_query` attribute is a space-separated string of the **Unified Representation**. This "Term Heaviness" approach ensures that a Bangla query can match an English document even if the translation isn't perfect, as long as the transliterated or entity terms match.

### Dense Retrieval (Semantic)
The `dense_query_text` creates a multi-aspect string:
`Original Query | Translated Query | Expanded Terms`
This is fed into **LaBSE** (Language-Agnostic BERT Sentence Embedding). Since LaBSE maps 109+ languages into the same vector space, the resulting embedding can be compared directly against the `.npy` document embeddings using dot product similarity.

---

## 💻 Example Output
**Input:** `"Dhaka আবহাওয়া"`

1.  **Detected:** `bn` 
2.  **NER:** `[('Dhaka', 'LOC')]`
3.  **Expanded:** `['weather']`
4.  **Translation:** `Translated (bn->en): 'dhaka weather'`
5.  **Unified:** `3 terms`

---

## 📦 Dependencies
*   `transformers`: For XLM-Roberta NER.
*   `sentence-transformers`: For LaBSE embeddings.
*   `deep-translator`: For query translation.
*   `numpy` & `scikit-learn`: For vector math and similarity.