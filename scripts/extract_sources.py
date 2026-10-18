import hashlib
import json
from logging import root
import re
from pathlib import Path

from bs4 import BeautifulSoup, Tag


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"
MANIFEST_PATH = PROJECT_ROOT / "docs" / "sources.json"

BLOCK_TYPES = {
    "h1": "heading",
    "h2": "heading",
    "h3": "heading",
    "h4": "heading",
    "h5": "heading",
    "h6": "heading",
    "p": "paragraph",
    "pre": "code",
    "table": "table",
    "dl": "definition_list",
    "ul": "unordered_list",
    "ol": "ordered_list",
}


def is_section(element: Tag) -> bool:
    return any(
        re.fullmatch(r"sect[1-6]", class_name)
        for class_name in element.get("class", [])
    )


def plain_text(element: Tag) -> str:
    return " ".join(element.get_text(" ", strip=True).split())


def section_details(element: Tag, root: Tag) -> list[dict]:
    sections = []
    current = element

    while isinstance(current, Tag):
        if is_section(current):
            heading = current.find(
                ["h1", "h2", "h3", "h4", "h5", "h6"]
            )
            sections.append(
                {
                    "id": current.get("id"),
                    "title": plain_text(heading) if heading else "",
                }
            )

        if current is root:
            break

        current = current.parent

    return list(reversed(sections))


def make_block(
    element: Tag,
    root: Tag,
    source: dict,
    position: int,
) -> dict:
    kind = BLOCK_TYPES[element.name]
    sections = section_details(element, root)

    anchor = element.get("id")

    if not anchor:
        for section in reversed(sections):
            if section["id"]:
                anchor = section["id"]
                break

    citation_url = source["url"]
    if anchor:
        citation_url += f"#{anchor}"

    if kind == "code":
        text = element.get_text().strip("\n")
    elif kind in {
        "table",
        "definition_list",
        "unordered_list",
        "ordered_list",
    }:
        text = element.get_text("\n", strip=True)
    else:
        text = plain_text(element)

    block = {
        "block_id": f"{source['id']}:b{position:04d}",
        "kind": kind,
        "section_path": sections,
        "citation_url": citation_url,
        "text": text,
    }

    if kind in {
        "table",
        "definition_list",
        "unordered_list",
        "ordered_list",
    }:
        block["html"] = str(element)

    return block


def collect_blocks(root: Tag, source: dict) -> list[dict]:
    blocks = []

    def walk(parent: Tag) -> None:
        for child in parent.children:
            if not isinstance(child, Tag):
                continue

            if child.name in BLOCK_TYPES:
                block = make_block(
                    child, root, source, len(blocks) + 1
                )

                if block["text"].strip():
                    blocks.append(block)

                # This block already contains its nested content.
                continue

            walk(child)

    walk(root)
    return blocks


def extract_source(source: dict, version: str) -> dict:
    source_id = source["id"]
    raw_path = RAW_DIR / f"{source_id}.html"
    metadata_path = RAW_DIR / f"{source_id}.metadata.json"

    content = raw_path.read_bytes()
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))

    if metadata["source_id"] != source_id:
        raise ValueError(f"Source ID mismatch: {source_id}")

    if metadata["source_url"] != source["url"]:
        raise ValueError(f"Source URL mismatch: {source_id}")

    if metadata["postgres_version"] != version:
        raise ValueError(f"Version mismatch: {source_id}")

    if (
        hashlib.sha256(content).hexdigest() != metadata["sha256"]
        or len(content) != metadata["size_bytes"]
    ):
        raise ValueError(f"Snapshot integrity check failed: {source_id}")

    soup = BeautifulSoup(content, "html.parser")
    roots = soup.select("#docContent > div.sect1")

    if len(roots) != 1:
        raise ValueError(f"Unexpected document structure: {source_id}")

    root = roots[0]

    # Remove executable/style content and the local table of contents.
    for unwanted in list(root.select("script, style, .toc")):
        if unwanted.parent is not None:
            unwanted.decompose()

    # Remove heading permalink controls, while retaining meaningful links.
    for heading in root.find_all(
        ["h1", "h2", "h3", "h4", "h5", "h6"]
    ):
        for link in list(heading.find_all("a")):
            if link.get_text(strip=True) == "#":
                link.decompose()

    blocks = collect_blocks(root, source)

    if not blocks:
        raise ValueError(f"No content extracted: {source_id}")

    return {
        "schema_version": 1,
        "source_id": source_id,
        "title": source["title"],
        "source_url": source["url"],
        "postgres_version": version,
        "retrieved_at_utc": metadata["retrieved_at_utc"],
        "raw_sha256": metadata["sha256"],
        "blocks": blocks,
    }


def main() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    documents = [
        extract_source(source, manifest["postgres_version"])
        for source in manifest["sources"]
    ]

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for document in documents:
        output_path = OUTPUT_DIR / f"{document['source_id']}.json"
        output_path.write_text(
            json.dumps(document, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

        counts = {}
        for block in document["blocks"]:
            kind = block["kind"]
            counts[kind] = counts.get(kind, 0) + 1

        print(f"\n{document['source_id']}")
        print(f"  Blocks: {len(document['blocks'])}")
        print(f"  Types: {counts}")

    print("\nExtraction complete.")


if __name__ == "__main__":
    main()