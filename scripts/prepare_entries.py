from copy import deepcopy
import json
from pathlib import Path

from bs4 import BeautifulSoup, Tag


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_DIR = PROCESSED_DIR / "entries"
MANIFEST_PATH = PROJECT_ROOT / "docs" / "sources.json"


def readable_text(element: Tag) -> str:
    return " ".join(element.get_text(" ", strip=True).split())


def split_definition_list(block: dict) -> list[dict]:
    soup = BeautifulSoup(block["html"], "html.parser")
    definition_list = soup.find("dl")

    if definition_list is None:
        raise ValueError(f"Missing definition list: {block['block_id']}")

    groups = []
    terms = []
    descriptions = []

    for child in definition_list.find_all(recursive=False):
        if child.name == "dt":
            # A new term after a description starts a new entry.
            if descriptions:
                groups.append((terms, descriptions))
                terms = []
                descriptions = []

            terms.append(child)

        elif child.name == "dd":
            if not terms:
                raise ValueError(
                    f"Description without a term: {block['block_id']}"
                )

            descriptions.append(child)

        else:
            raise ValueError(
                f"Unexpected direct child <{child.name}> "
                f"in {block['block_id']}"
            )

    if terms or descriptions:
        if not terms or not descriptions:
            raise ValueError(
                f"Incomplete definition entry: {block['block_id']}"
            )

        groups.append((terms, descriptions))

    if not groups:
        raise ValueError(f"Empty definition list: {block['block_id']}")

    entries = []

    for position, (terms, descriptions) in enumerate(groups, start=1):
        term_text = " / ".join(readable_text(term) for term in terms)

        description_text = "\n\n".join(
            description.get_text("\n", strip=True)
            for description in descriptions
        )

        entry = deepcopy(block)
        entry["parent_block_id"] = block["block_id"]
        entry["block_id"] = f"{block['block_id']}:d{position:03d}"
        entry["kind"] = "definition_entry"
        entry["term"] = term_text
        entry["text"] = f"{term_text}\n\n{description_text}"

        # Keep the HTML structure for later handling of nested content.
        entry["html"] = (
            "<dl>"
            + "".join(str(element) for element in terms + descriptions)
            + "</dl>"
        )

        entry["contains_table"] = any(
            description.find("table") is not None
            for description in descriptions
        )
        entry["contains_code"] = any(
            description.find("pre") is not None
            for description in descriptions
        )

        entries.append(entry)

    return entries


def prepare_document(document: dict) -> dict:
    prepared = deepcopy(document)
    prepared_blocks = []

    for block in document["blocks"]:
        if block["kind"] == "definition_list":
            prepared_blocks.extend(split_definition_list(block))
        else:
            prepared_blocks.append(deepcopy(block))

    prepared["blocks"] = prepared_blocks
    prepared["preparation_version"] = 1

    return prepared


def main() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    prepared_documents = []

    for source in manifest["sources"]:
        input_path = PROCESSED_DIR / f"{source['id']}.json"
        document = json.loads(input_path.read_text(encoding="utf-8"))
        prepared_documents.append(prepare_document(document))

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for document in prepared_documents:
        output_path = OUTPUT_DIR / f"{document['source_id']}.json"
        output_path.write_text(
            json.dumps(document, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

        entries = [
            block
            for block in document["blocks"]
            if block["kind"] == "definition_entry"
        ]

        print(f"\n{document['source_id']}")
        print(f"  Total blocks: {len(document['blocks'])}")
        print(f"  Definition entries: {len(entries)}")
        print(
            "  Entries containing tables: "
            f"{sum(entry['contains_table'] for entry in entries)}"
        )
        print(
            "  Entries containing code: "
            f"{sum(entry['contains_code'] for entry in entries)}"
        )

    print("\nDefinition-entry preparation complete.")


if __name__ == "__main__":
    main()