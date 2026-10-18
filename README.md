# IncidentLens

Evidence-backed PostgreSQL troubleshooting using retrieval-augmented generation.

## Overview

IncidentLens is being developed to help developers investigate PostgreSQL
incidents using relevant passages from official documentation.

Given a problem description and optional sanitized error text, it will retrieve
supporting documentation and generate an explanation with citations, possible
causes, missing diagnostic information, and suggested next checks.

## Status

Under development. The repository currently contains the initial project
structure and architecture documentation. Retrieval, generation, and the
application interface are not yet implemented.

## Initial scope

PostgreSQL 17 incidents involving:

- Blocked transactions
- Deadlocks
- Connection exhaustion

## Planned capabilities

- Search over a curated, versioned documentation collection
- Keyword and semantic retrieval
- Answers linked to supporting source passages
- Explicit handling of insufficient evidence
- Reproducible incident examples in an isolated local database
- Evaluation of retrieval quality, citation support, and response latency

## Architecture

The ingestion pipeline will extract documentation, preserve source metadata,
split content into passages, and build search indexes.

For each question, the application will retrieve relevant passages and provide
them to a language model. Generated responses will be checked for valid source
references before being displayed.

See [Architecture](docs/architecture.md) for design details.

## Development setup

Create a virtual environment:

```bash
python -m venv .venv
```

Application installation and launch instructions will be added when the first
runnable implementation is available.

## Data and operational boundaries

The initial corpus will use selected official PostgreSQL documentation.
Incident examples will use synthetic data or an isolated local database.

IncidentLens will not connect to production databases or execute generated SQL.
Suggested diagnostic steps require human review. Retrieved evidence does not
guarantee that a generated explanation is correct.

Do not submit credentials, personal information, or confidential production logs.

## Third-party materials

Source attribution and applicable license notices are recorded in
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).