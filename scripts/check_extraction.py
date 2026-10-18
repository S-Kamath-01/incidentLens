import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"


def main() -> None:
    path = PROCESSED_DIR / "explicit-locking.json"
    document = json.loads(path.read_text(encoding="utf-8"))

    problems = []

    for block in document["blocks"]:
        block_id = block["block_id"]

        if block["kind"] == "heading" and block["text"].endswith(" #"):
            problems.append(f"{block_id}: heading permalink remains")

        for section in block["section_path"]:
            if section["title"].endswith(" #"):
                problems.append(f"{block_id}: section permalink remains")

        if 'class="toc"' in block.get("html", ""):
            problems.append(f"{block_id}: table of contents remains")

        if not block["citation_url"].startswith(
            document["source_url"] + "#"
        ):
            problems.append(f"{block_id}: unexpected citation URL")

    tables = [
        block
        for block in document["blocks"]
        if block["kind"] == "table"
    ]

    if len(tables) != 2:
        problems.append(
            f"Expected two locking conflict tables; found {len(tables)}"
        )

    for table in tables:
        if "<table" not in table.get("html", ""):
            problems.append(
                f"{table['block_id']}: original table structure missing"
            )

    if problems:
        raise ValueError("\n".join(problems))

    print("Locking-document extraction checks passed.")

    for phrase in ["insituations", "ACCESSSHARE"]:
        matches = [
            block["block_id"]
            for block in document["blocks"]
            if phrase in block["text"]
        ]
        print(f"Exact text {phrase!r}: {matches}")

    print("\nFirst three blocks:")
    for block in document["blocks"][:3]:
        print(f"{block['kind']}: {block['text'][:180]}")


if __name__ == "__main__":
    main()