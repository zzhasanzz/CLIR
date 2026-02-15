#  Hybrid Cross-Lingual Retriever (`see the retrieval_system_final.ipynb`)

The **Retriever** module is designed to perform high-speed, high-accuracy searches by combining traditional lexical matching with modern semantic vector space modeling. It operates on a **Hybrid Architecture**, leveraging the strengths of multiple scoring algorithms to bridge the gap between English and Bangla.

##  Key Features

### 1. Multi-Modal Retrieval (Hybrid Search)
The system calculates relevance by fusing three distinct scoring signals:
*   **BM25 (Sparse):** Best-in-class token matching using the `rank_bm25` algorithm.
*   **LaBSE (Dense):** Uses **Language-Agnostic BERT Sentence Embeddings** to find documents that are semantically related, even if they share zero common keywords (e.g., matching "Healthcare" to "স্বাস্থ্য").
*   **Fuzzy (Lexical):** Uses Levenshtein distance and N-Gram containment to handle spelling variations, script transliteration mismatches, and minor typos.

### 2. Efficiency Upgrade: Top-100 Re-ranking
To maintain real-time performance, the retriever uses a **two-stage pipeline**:
1.  **Filtering:** BM25 and Semantic search identify the top candidates across the entire corpus in milliseconds.
2.  **Re-ranking:** The computationally expensive Fuzzy logic is applied **only to the Top 100 candidates**. 
*   **Impact:** This reduced Fuzzy Search latency from ~2.5 seconds to ~94ms, enabling a total end-to-end response time of **<160ms**.

### 3. Cross-Corpus Fusion
The retriever searches both the **Bangla Corpus** and the **English Corpus** simultaneously. Results are normalized and merged into a single global ranking list, allowing users to find the best information regardless of the source language.

---

##  System Architecture

The retrieval process follows these logical steps:

1.  **Query Augmentation:** Receives a `ProcessedQuery` object (containing expanded terms, translations, and named entities).
2.  **Signal Generation:**
    *   Generates a LaBSE vector for the augmented query.
    *   Generates BM25 scores for the unified term list.
3.  **Scoring & Normalization:** Scores from different algorithms (0–100+ for BM25 vs. 0–1 for LaBSE) are normalized to a standard `[0, 1]` scale.
4.  **Weighted Sum Fusion:** Scores are combined using a configurable weighting strategy (Default: 30% BM25, 50% Semantic, 20% Fuzzy).
5.  **Global Ranking:** Final results are sorted and truncated to the requested `top_k`.

---

##  Component Breakdown

### Sparse Scoring (BM25 & TF-IDF)
*   **BM25Okapi:** The primary lexical engine.
*   **TF-IDF:** Included as a standalone comparison mode, utilizing `ngram_range=(1, 2)` to capture phrases.

### Dense Scoring (Semantic)
*   **LaBSE:** Encodes queries into 768-dimensional vectors.
*   **Dot Product:** Used for similarity measurement against pre-computed document embeddings (stored in `.npy` format).

### Lexical Scoring (Fuzzy)
*   **SequenceMatcher:** Calculates the Levenshtein ratio between the query and document titles.
*   **N-Gram Containment:** Measures how many 3-character sequences from the query appear in the title (excellent for partial matches).
*   **Jaccard Similarity:** Measures token overlap in the document body.

---

##  Performance Benchmarks (Average)

| Stage | Latency |
| :--- | :--- |
| **Semantic Embedding** | 11.01 ms |
| **BM25 Search** | 35.35 ms |
| **Fuzzy Re-ranking (Top 100)** | 94.33 ms |
| **Score Fusion & Ranking** | 1.42 ms |
| **Total Retrieval Time** | **~143.48 ms** |

---

## Usage Example

```python
# Initialize the retriever
retriever = Retriever(
    bangla_corpus_path="bangla_corpus.jsonl",
    english_corpus_path="english_corpus.jsonl",
    query_processor=processor,
    bangla_emb_path="bangla_embeddings.npy",
    english_emb_path="english_embeddings.npy"
)

# Perform a Hybrid Search
results = retriever.search(
    query="Dhaka আবহাওয়া", 
    mode="hybrid", 
    top_k=5
)

# Display Results
for r in results:
    print(f"[{r['language'].upper()}] Score: {r['score']:.4f} | Title: {r['title']}")
```

---

## Dependencies
*   `rank_bm25`: For BM25 indices.
*   `scikit-learn`: For TF-IDF and similarity metrics.
*   `numpy`: For high-speed vector operations.
*   `difflib`: For fuzzy string matching.