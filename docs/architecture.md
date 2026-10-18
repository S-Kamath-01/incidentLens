# Architecture

## Goal

Help a developer investigate PostgreSQL incidents using retrieved,
source-attributed evidence.

## Initial scope

- PostgreSQL 17
- Blocking transactions
- Deadlocks
- Connection exhaustion

## Input

- Problem description
- PostgreSQL version
- Optional sanitized error text

## Output

- Possible explanations
- Evidence supporting each explanation
- Missing diagnostic information
- Suggested diagnostic steps
- Source citations

## Knowledge preparation

1. Select approved documentation URLs.
2. Record version, source URL, retrieval timestamp, and content hash.
3. Extract text while preserving headings.
4. Create chunks with source metadata.
5. Build BM25 and dense retrieval indexes.

## Question answering

1. Validate input.
2. Retrieve relevant passages.
3. Combine and rank candidates.
4. Build a prompt containing selected evidence.
5. Generate a structured response.
6. Validate that cited source IDs were supplied to the model.
7. Return the answer and evidence.

Citation-ID validation checks provenance, not factual support.
Answer support will also require evaluation.

## Proposed components

- Python application logic
- FastAPI API
- Streamlit interface
- BM25 lexical retrieval
- Sentence-Transformers embeddings
- FAISS vector search
- Hosted LLM provider, to be selected
- Separate disposable PostgreSQL incident lab

## Evaluation

Compare BM25, dense retrieval, and hybrid retrieval.

Measure:
- Hit@k
- Recall@k
- Citation support
- Insufficient-evidence handling
- Response latency
- Token usage

Split related incident examples together when creating development and
test sets to reduce leakage.

## Security boundaries

- Approved documentation sources only
- Retrieved content is treated as untrusted data
- No model access to shell commands or production database credentials
- No automatic execution of generated SQL
- Secrets excluded from source control and logs
- Dependency and model licenses reviewed before adoption