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
- FastAPI backend
- React + TypeScript interface, developed with Vite
- BM25 lexical retrieval
- BAAI/bge-small-en-v1.5 embeddings, loaded through Sentence Transformers
- Local CPU execution for embeddings
- FAISS vector search
- Local answer generation through Ollama
- Gemma 3 4B as the initial generator candidate, subject to hardware testing
- Separate disposable PostgreSQL incident lab

## Execution and distribution

The interface, backend, retrieval pipeline, and answering model run on
the user's computer. The initial version requires no hosted inference API.

GitHub contains source code, setup instructions, and project documentation.
Downloaded model weights, generated indexes, credentials, and personal study
notes are excluded from version control.

Public application hosting is outside the initial scope.
## Security boundaries

- Approved documentation sources only
- Retrieved content is treated as untrusted data
- No model access to shell commands or production database credentials
- No automatic execution of generated SQL
- Secrets excluded from source control and logs
- Dependency and model licenses reviewed before adoption

## Implemented ingestion pipeline

1. A source manifest identifies selected PostgreSQL 17 documentation pages.
2. The downloader saves HTML snapshots and provenance metadata.
3. Snapshot hashes and sizes are checked before extraction.
4. The extractor selects the document body and preserves structured blocks.
5. Definition lists are separated into individual entries.
6. Lock matrices and supported monitoring tables become labeled passages.
7. Candidate passages are consolidated into JSONL records.

Intermediate files retain table and list HTML for inspection.
Derived records retain source identity, section context, and citations.

The current output is not an embedding index. Token-aware sizing and
splitting are pending. References between passages are not automatically
resolved, and section-level citations do not prove factual support.

Scripts currently provide the ingestion entry points. Reusable pipeline
logic can move into src/incidentlens as application integration develops.