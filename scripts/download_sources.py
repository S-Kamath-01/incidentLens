import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import (
    HTTPRedirectHandler,
    Request,
    build_opener,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = PROJECT_ROOT / "docs" / "sources.json"
RAW_DIR = PROJECT_ROOT / "data" / "raw"

MAX_DOWNLOAD_BYTES = 5 * 1024 * 1024
TIMEOUT_SECONDS = 30


class RejectRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError(
            f"Unexpected redirect to {newurl}. Review the source URL."
        )


def validate_url(url: str, version: str) -> None:
    parts = urlsplit(url)

    if parts.scheme != "https" or parts.netloc != "www.postgresql.org":
        raise ValueError(f"Unapproved source URL: {url}")

    if parts.query or parts.fragment:
        raise ValueError(f"Use a URL without query or fragment: {url}")

    is_document = (
        parts.path.startswith(f"/docs/{version}/")
        and parts.path.endswith(".html")
    )
    is_license = parts.path == "/about/licence/"

    if not (is_document or is_license):
        raise ValueError(f"Unapproved source path: {url}")


def download_html(url: str, version: str) -> bytes:
    validate_url(url, version)

    request = Request(
        url,
        headers={
            "User-Agent": "IncidentLens/0.1 (documentation downloader)",
            "Accept": "text/html",
        },
    )

    opener = build_opener(RejectRedirects())

    with opener.open(request, timeout=TIMEOUT_SECONDS) as response:
        content_type = response.headers.get_content_type()

        if content_type != "text/html":
            raise ValueError(f"Expected HTML, received {content_type}: {url}")

        content = response.read(MAX_DOWNLOAD_BYTES + 1)

    if not content:
        raise ValueError(f"Empty response: {url}")

    if len(content) > MAX_DOWNLOAD_BYTES:
        raise ValueError(f"Download exceeds the size limit: {url}")

    return content


def save_source(source: dict, version: str) -> None:
    source_id = source["id"]

    if not re.fullmatch(r"[a-z0-9-]+", source_id):
        raise ValueError(f"Invalid source ID: {source_id}")

    html_path = RAW_DIR / f"{source_id}.html"
    metadata_path = RAW_DIR / f"{source_id}.metadata.json"

    if html_path.exists() or metadata_path.exists():
        raise FileExistsError(
            f"Snapshot already exists for {source_id}. "
            "Keep it unchanged; review existing files before downloading again."
        )

    content = download_html(source["url"], version)

    metadata = {
        "source_id": source_id,
        "title": source["title"],
        "source_url": source["url"],
        "postgres_version": version,
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "sha256": hashlib.sha256(content).hexdigest(),
        "size_bytes": len(content),
        "raw_file": html_path.relative_to(PROJECT_ROOT).as_posix(),
    }

    html_path.write_bytes(content)
    metadata_path.write_text(
        json.dumps(metadata, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"Saved {source_id}: {len(content):,} bytes")


def main() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    version = manifest["postgres_version"]

    if version != "17":
        raise ValueError("This initial corpus is restricted to PostgreSQL 17.")

    sources = [
        {
            "id": "postgresql-license",
            "title": "PostgreSQL License",
            "url": manifest["license_url"],
        },
        *manifest["sources"],
    ]

    ids = [source["id"] for source in sources]

    if len(ids) != len(set(ids)):
        raise ValueError("The manifest contains duplicate source IDs.")

    RAW_DIR.mkdir(parents=True, exist_ok=True)

    for source in sources:
        save_source(source, version)

    print("Download complete: license snapshot and three documentation pages.")


if __name__ == "__main__":
    main()