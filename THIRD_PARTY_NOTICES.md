# Third-party notices

## PostgreSQL documentation

- **Source:** [PostgreSQL 17 documentation](https://www.postgresql.org/docs/17/)
- **Version:** PostgreSQL 17
- **License:** PostgreSQL License
- **License source:** [Official license notice](https://www.postgresql.org/about/licence/)
- **Local notice:** [postgresql-LICENSE.txt](licenses/postgresql-LICENSE.txt)
- **Source manifest:** [sources.json](docs/sources.json)

### Collection and provenance

The ingestion pipeline downloads HTML snapshots and records:

- Source URLs
- Retrieval timestamps
- File sizes
- SHA-256 hashes

### Content transformations

IncidentLens processes the documentation by:

- Removing navigation elements
- Separating definition entries
- Converting supported tables into labeled records
- Assembling candidate passages

These transformations are performed by IncidentLens and are not official
PostgreSQL documentation edits.

### Distribution

Downloaded and processed documents are excluded from Git.

Any distribution of those documents or derived passages must retain the
applicable notices.

## Python dependencies

Installed package versions are recorded in [requirements.txt](requirements.txt).

Dependencies retain their respective licenses.

## Models

No model weights are bundled in this repository.

Model revisions and applicable notices will be recorded when integrated.