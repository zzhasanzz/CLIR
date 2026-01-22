# CLIR System Overview: Query Processor Pipeline

## 1. High-Level Architecture
The Cross-Lingual Information Retrieval (CLIR) system is designed to bridge the gap between English and Bangla information spaces. It operates as a unified pipeline consisting of two main stages:

1.  **Module B: Query Processor** (Understanding & Transformation)
2.  **Module C: Hybrid Matcher** (Retrieval & Ranking)

**Workflow:**
`User Query` $\rightarrow$ `Language Detection` $\rightarrow$ `Spell Correction` $\rightarrow$ `Translation` $\rightarrow$ `Hybrid Search` $\rightarrow$ `Top-K Ranked Documents (Native + Translated)`

---

## 2. Module B: Advanced Query Processing
This module is responsible for "cleaning" and "preparing" the user's raw input before it touches the search index.

### Key Concepts:

#### A. Language Detection (Unicode Analysis)
*   **Theory**: Text is analyzed at the character level. If a significant portion of characters falls within the Bengali Unicode block (`U+0980` to `U+09FF`), the language is classified as Bangla (`bn`); otherwise, it is English (`en`).
*   **Purpose**: Determines which corpus to search immediately and which translation direction is needed.

#### B. Fuzzy Spell Correction
*   **Theory**: Uses **Levenshtein Distance** (Edit Distance) to calculate the minimum number of single-character edits (insertions, deletions, substitutions) required to change one word into another.
*   **Purpose**: Corrects user typos (e.g., "vacine" $\rightarrow$ "vaccine") to ensure the downstream models (Translation/Search) receive valid tokens.

#### C. Neural Machine Translation (NLLB-200)
*   **Model**: `facebook/nllb-200-distilled-600M` ("No Language Left Behind").
*   **Theory**: A Transformer-based Sequence-to-Sequence (Seq2Seq) model trained on massive multilingual datasets. It encodes the source sentence into a vector representation and decodes it into the target language.
*   **Purpose**: Enables the system to search the *other* language's corpus. If a user asks in English, we translate to Bangla to fetch relevant local news.

#### D. Named Entity Recognition (NER)
*   **Model**: `XLM-Roberta` (Transformer).
*   **Theory**: A token classification task that identifies specific entities like **PER** (Person), **ORG** (Organization), and **LOC** (Location) within the text.
*   **Purpose**: (Optional/Future) Can be used to strictly filter results (e.g., if "Dhaka" is detected, strongly penalize documents that don't satisfy that location).

---

## 3. Module C: Hybrid Search Engine
This module retrieves the most relevant documents using a weighted combination of three distinct retrieval algorithms.

### Key Metrics:

#### A. Fuzzy Matching (Textual / Lexical)
*   **Theory**: Focuses on surface-level character overlap.
    *   **Levenshtein Ratio**: How similar are the title strings?
    *   **N-gram Containment**: Do the trigrams (3-character sequences) of the query appear in the document?
    *   **Jaccard Similarity**: Intersection over Union of the set of words in the query vs. the document body.
*   **Strengths**: Robust against minor variants and exact keyword matches.
*   **Weaknesses**: Fails on synonyms (e.g., "car" vs "automobile").

#### B. Semantic Search (Vector / Neural)
*   **Model**: `sentence-transformers/LaBSE` (Language-agnostic BERT Sentence Embedding).
*   **Theory**: Maps sentences into a 768-dimensional dense vector space. Similar concepts end up close together in this space, even if they share no common words. Similarity is measured using **Cosine Similarity**.
*   **Strengths**: Captures conceptual meaning and cross-lingual similarity (English query vector matches Bangla document vector).
*   **Weaknesses**: Can drift if concepts are vaguely related (e.g., "tiger" might match "cat" too strongly).

#### C. BM25 (Probabilistic)
*   **Algorithm**: Okapi BM25 (Best Matching 25).
*   **Theory**: An integrated scoring function based on:
    *   **TF (Term Frequency)**: How often the term appears in the document (linear saturation).
    *   **IDF (Inverse Document Frequency)**: How rare the term is across the entire corpus (penalizes "the", "and", rewards "microchip", "pandemic").
    *   **Field Length Normalization**: Penalizes very long documents to prevent them from dominating just because they have more words.
*   **Strengths**: The industry standard for keyword search; highly effective for precise specific queries.

### The Hybrid Formula
The final relevance score is calculated as:

$$ \text{Final Score} = (0.3 \times \text{BM25}) + (0.5 \times \text{Semantic}) + (0.2 \times \text{Fuzzy}) $$

*   **Logic**:
    *   **50% Semantic**: Priority on understanding *meaning*.
    *   **30% BM25**: ensures specific *keywords* are respected.
    *   **20% Fuzzy**: Handles *typos* and exact title matches as a fallback.

---

## 4. Execution Strategy
When a query (e.g., "dhaka air quality") runs through `query_processor.ipynb`:

1.  **Pre-processing**:
    *   Detected: English.
    *   Typos fixed.
    *   Translated to Bangla: "ঢাকা বায়ুর মান".
2.  **Native Search**:
    *   System searches the **English Corpus** using the English query.
    *   Returns **Top 5** results.
3.  **Cross-Lingual Search**:
    *   System searches the **Bangla Corpus** using the Translated query.
    *   Returns **Top 2** results.
4.  **Presentation**:
    *   User sees the best local documents + relevant cross-lingual insights side-by-side with confidence scores.
