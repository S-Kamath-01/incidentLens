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
    / "monitoring-stats.json"
)
OUTPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "normalized"
    / "monitoring-stats.json"
)


def text_of(element) -> str:
    return " ".join(element.get_text(" ", strip=True).split())


def require_unmerged(cells, label: str) -> None:
    for cell in cells:
        if (
            cell.get("rowspan", "1") != "1"
            or cell.get("colspan", "1") != "1"
        ):
            raise ValueError(f"Merged cells require review: {label}")


def convert_table(block: dict) -> list[dict]:
    soup = BeautifulSoup(block["html"], "html.parser")
    table = soup.find("table")

    if table is None:
        raise ValueError(f"Missing table: {block['block_id']}")

    title = table.get("summary", "").strip()
    header_rows = table.select("thead > tr")
    body_rows = table.select("tbody > tr")

    if not title or len(header_rows) != 1 or not body_rows:
        raise ValueError(
            f"Unsupported table structure: {block['block_id']}"
        )

    header_cells = header_rows[0].find_all(
        ["th", "td"], recursive=False
    )
    require_unmerged(header_cells, title)

    headers = [text_of(cell) for cell in header_cells]

    if not all(headers):
        raise ValueError(f"Empty column heading: {title}")

    entries = []

    for position, row in enumerate(body_rows, start=1):
        cells = row.find_all(["th", "td"], recursive=False)
        require_unmerged(cells, title)

        if len(cells) != len(headers):
            raise ValueError(
                f"Header/cell count mismatch: {title}, row {position}"
            )

        if row.find("table") is not None:
            raise ValueError(f"Nested table requires review: {title}")

        if row.find("pre") is not None:
            raise ValueError(f"Code block requires review: {title}")

        fields = []

        # Catalog-style table: field, type and description in one cell.
        definition = (
            cells[0].find("p", class_="column_definition")
            if len(cells) == 1
            else None
        )

        if definition is not None:
            name = definition.find("code", class_="structfield")
            data_type = definition.find("code", class_="type")

            if name is None or data_type is None:
                raise ValueError(
                    f"Unrecognized field definition: {title}, row {position}"
                )

            field_name = text_of(name)
            field_type = text_of(data_type)

            description_cell = deepcopy(cells[0])
            description_cell.find(
                "p", class_="column_definition"
            ).decompose()

            description = text_of(description_cell)

            if not description:
                raise ValueError(f"Missing description: {title}, {field_name}")

            fields = [
                {"label": "Column", "value": field_name},
                {"label": "Type", "value": field_type},
                {"label": "Description", "value": description},
            ]
        else:
            fields = [
                {"label": header, "value": text_of(cell)}
                for header, cell in zip(headers, cells)
            ]

        entry = {
            "block_id": f"{block['block_id']}:r{position:03d}",
            "parent_block_id": block["block_id"],
            "kind": "table_entry",
            "section_path": deepcopy(block["section_path"]),
            "citation_url": block["citation_url"],
            "table_title": title,
            "fields": fields,
            "text": (
                f"PostgreSQL 17. {title}.\n"
                + "\n".join(
                    f"{field['label']}: {field['value']}"
                    for field in fields
                )
            ),
            "row_html": str(row),
        }

        entries.append(entry)

    return entries


def main() -> None:
    document = json.loads(INPUT_PATH.read_text(encoding="utf-8"))

    if document["postgres_version"] != "17":
        raise ValueError("This converter expects PostgreSQL 17.")

    normalized = deepcopy(document)
    blocks = []
    table_count = 0
    entry_count = 0

    for block in document["blocks"]:
        if block["kind"] == "table":
            entries = convert_table(block)
            blocks.extend(entries)
            table_count += 1
            entry_count += len(entries)
        else:
            blocks.append(deepcopy(block))

    normalized["blocks"] = blocks
    normalized["normalization_version"] = 1

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(normalized, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print(f"Converted monitoring tables: {table_count}")
    print(f"Generated table entries: {entry_count}")

    for block in blocks:
        if (
            block["kind"] == "table_entry"
            and block["table_title"] == "pg_stat_activity View"
            and any(
                field["label"] == "Column"
                and field["value"] == "wait_event_type"
                for field in block["fields"]
            )
        ):
            print("\nExample entry:")
            print(block["text"])
            print(f"Source: {block['citation_url']}")


if __name__ == "__main__":
    main()