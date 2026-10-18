from copy import deepcopy
import json
from pathlib import Path

from bs4 import BeautifulSoup


PROJECT_ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "entries"
    / "explicit-locking.json"
)
OUTPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "normalized"
    / "explicit-locking.json"
)

TABLE_SPECS = {
    "Conflicting Lock Modes": {
        "scope": "table-level",
        "headers": [
            "ACCESS SHARE",
            "ROW SHARE",
            "ROW EXCL.",
            "SHARE UPDATE EXCL.",
            "SHARE",
            "SHARE ROW EXCL.",
            "EXCL.",
            "ACCESS EXCL.",
        ],
    },
    "Conflicting Row-Level Locks": {
        "scope": "row-level",
        "headers": [
            "FOR KEY SHARE",
            "FOR SHARE",
            "FOR NO KEY UPDATE",
            "FOR UPDATE",
        ],
    },
}


def text_of(element) -> str:
    return " ".join(element.get_text(" ", strip=True).split())


def full_label(label: str) -> str:
    return label.replace("EXCL.", "EXCLUSIVE")


def convert_table(block: dict) -> list[dict]:
    soup = BeautifulSoup(block["html"], "html.parser")
    table = soup.find("table")

    if table is None:
        raise ValueError(f"Missing table: {block['block_id']}")

    title = table.get("summary", "")

    if title not in TABLE_SPECS:
        raise ValueError(f"Unrecognized lock table: {title}")

    spec = TABLE_SPECS[title]
    header_rows = table.select("thead > tr")
    body_rows = table.select("tbody > tr")

    if len(header_rows) != 2:
        raise ValueError(f"Unexpected header structure: {title}")

    header_cells = header_rows[1].find_all(
        ["th", "td"], recursive=False
    )
    headers = [text_of(cell) for cell in header_cells]

    if headers != spec["headers"]:
        raise ValueError(f"Unexpected column labels: {title}")

    if len(body_rows) != len(headers):
        raise ValueError(f"Unexpected row count: {title}")

    passages = []

    for position, row in enumerate(body_rows, start=1):
        cells = row.find_all(["th", "td"], recursive=False)

        if len(cells) != len(headers) + 1:
            raise ValueError(f"Unexpected cell count: {title}, row {position}")

        if any(
            cell.get("rowspan", "1") != "1"
            or cell.get("colspan", "1") != "1"
            for cell in cells
        ):
            raise ValueError(f"Unexpected merged body cells: {title}")

        requested_label = text_of(cells[0])

        if requested_label != headers[position - 1]:
            raise ValueError(f"Unexpected row label: {title}, row {position}")

        markers = [text_of(cell) for cell in cells[1:]]

        if any(marker not in {"", "X"} for marker in markers):
            raise ValueError(f"Unexpected conflict marker: {title}")

        conflicts = [
            full_label(header)
            for header, marker in zip(headers, markers)
            if marker == "X"
        ]

        if not conflicts:
            raise ValueError(f"Unexpected empty conflict row: {title}")

        requested = full_label(requested_label)
        scope = spec["scope"]

        passage = {
            "block_id": f"{block['block_id']}:r{position:03d}",
            "parent_block_id": block["block_id"],
            "kind": "lock_conflict",
            "section_path": deepcopy(block["section_path"]),
            "citation_url": block["citation_url"],
            "table_title": title,
            "lock_scope": scope,
            "requested_mode": requested,
            "conflicting_existing_modes": conflicts,
            "text": (
                f"PostgreSQL 17 {scope} lock conflict matrix. "
                f"Requested lock mode {requested} conflicts with these "
                f"existing lock modes on the same resource: "
                f"{', '.join(conflicts)}."
            ),
        }

        passages.append(passage)

    return passages


def main() -> None:
    document = json.loads(INPUT_PATH.read_text(encoding="utf-8"))

    if document["postgres_version"] != "17":
        raise ValueError("This converter expects PostgreSQL 17.")

    normalized = deepcopy(document)
    normalized_blocks = []
    converted_tables = 0

    for block in document["blocks"]:
        if block["kind"] == "table":
            normalized_blocks.extend(convert_table(block))
            converted_tables += 1
        else:
            normalized_blocks.append(deepcopy(block))

    if converted_tables != 2:
        raise ValueError(
            f"Expected two lock tables, found {converted_tables}"
        )

    normalized["blocks"] = normalized_blocks
    normalized["normalization_version"] = 1

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(normalized, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    passages = [
        block
        for block in normalized_blocks
        if block["kind"] == "lock_conflict"
    ]

    print(f"Converted tables: {converted_tables}")
    print(f"Generated lock-conflict passages: {len(passages)}")

    for scope in ["table-level", "row-level"]:
        example = next(
            passage for passage in passages
            if passage["lock_scope"] == scope
        )
        print(f"\n{example['text']}")
        print(f"Source: {example['citation_url']}")


if __name__ == "__main__":
    main()