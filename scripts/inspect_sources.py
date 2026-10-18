import hashlib
import json
from pathlib import Path

from bs4 import BeautifulSoup


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
MANIFEST_PATH = PROJECT_ROOT / "docs" / "sources.json"


def inspect_source(source: dict) -> None:
    source_id = source["id"]

    html_path = RAW_DIR / f"{source_id}.html"
    metadata_path = RAW_DIR / f"{source_id}.metadata.json"

    content = html_path.read_bytes()
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))

    actual_hash = hashlib.sha256(content).hexdigest()

    if actual_hash != metadata["sha256"]:
        raise ValueError(f"Downloaded file has changed: {source_id}")

    if len(content) != metadata["size_bytes"]:
        raise ValueError(f"File size does not match metadata: {source_id}")

    soup = BeautifulSoup(content, "html.parser")

    print(f"\nSOURCE: {source_id}")
    print("Snapshot integrity: OK")

    page_title = soup.title.get_text(" ", strip=True) if soup.title else ""
    print(f"Page title: {page_title}")

    containers = soup.select("#docContent")
    print(f"Elements matching #docContent: {len(containers)}")

    if len(containers) != 1:
        raise ValueError(
            f"Expected one documentation container for {source_id}; "
            "inspect the HTML before extracting."
        )

    container = containers[0]

    print("Element counts:")
    for tag in ["h1", "h2", "h3", "h4", "p", "pre", "table", "dl"]:
        print(f"  {tag}: {len(container.find_all(tag))}")

    print("First eight headings:")
    headings = container.find_all(["h1", "h2", "h3", "h4"])

    for heading in headings[:8]:
        print(f"  {heading.name}: {heading.get_text(' ', strip=True)}")

    print("Direct child elements:")
    for child in container.find_all(recursive=False):
        classes = " ".join(child.get("class", []))
        print(f"  tag={child.name}, id={child.get('id', '')}, class={classes}")


def main() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    for source in manifest["sources"]:
        inspect_source(source)


if __name__ == "__main__":
    main()