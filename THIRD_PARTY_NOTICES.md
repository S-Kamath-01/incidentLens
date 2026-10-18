# Third-party notices

## PostgreSQL documentation

Source: https://www.postgresql.org/docs/17/
Version: PostgreSQL 17
License: PostgreSQL License
License source: https://www.postgresql.org/about/licence/
Local notice: licenses/postgresql-LICENSE.txt

Selected source pages are listed in docs/sources.json.

The ingestion pipeline downloads HTML snapshots and records source URLs,
retrieval timestamps, file sizes, and SHA-256 hashes.

Derived content removes navigation, separates definition entries,
converts supported tables into labeled records, and assembles candidate
passages. These transformations are performed by IncidentLens and are
not official PostgreSQL documentation edits.

Downloaded and processed documents are excluded from Git. Any distribution
of those documents or derived passages must retain the applicable notices.

## Python dependencies

Installed package versions are recorded in requirements.txt.
Dependencies retain their respective licenses.

## Models

No model weights are bundled in this repository.
Model revisions and applicable notices will be recorded when integrated.