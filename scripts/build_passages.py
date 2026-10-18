import hashlib
import json
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString, Tag


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

INPUT_PATHS = [
    PROCESSED_DIR / "normalized" / "explicit-locking.json",
    PROCESSED_DIR / "entries" / "runtime-config-connection.json",
    PROCESSED_DIR / "normalized" / "monitoring-stats.json",
]

OUTPUT_PATH = PROCESSED_DIR / "passages.jsonl"


def render_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")

    for link in list(soup.find_all("a")):
        if link.get_text(strip=True) == "#":
            link.decompose()

    # Nested tables require structural conversion before use.
    if soup.find("table") is not None:
        raise ValueError(
            "A definition or list contains a nested table. "
            "Review it before building passages."
        )

    boundary_tags = {
        "p", "dt", "dd", "li", "ul", "ol", "dl", "div"
    }

    def render(node) -> str:
        if isinstance(node, NavigableString):
            return str(node)

        if not isinstance(node, Tag):
            return ""

        if node.name == "pre":
            return "\n\n" + node.get_text().strip("\n") + "\n\n"

        if node.name == "br":
            return "\n"

        content = "".join(render(child) for child in node.children)

        if node.name in boundary_tags:
            return "\n\n" + content + "\n\n"

        return content

    # This renderer is for prose/list content. Do not flatten code.
    if soup.find("pre") is not None:
        raise ValueError(
            "A definition or list contains a code block. "
            "Review it before prose normalization."
        )

    paragraphs = []

    for part in render(soup).split("\n\n"):
        text = " ".join(part.split())
        if text:
            paragraphs.append(text)

    return "\n\n".join(paragraphs)


def make_passage(document: dict, block: dict) -> dict:
    kind = block["kind"]

    if kind in {
        "definition_entry",
        "unordered_list",
        "ordered_list",
    }:
        text = render_html(block["html"])
    elif kind == "code":
        text = block["text"].strip("\n")
    else:
        text = block["text"].strip()

    if not text:
        raise ValueError(f"Empty passage: {block['block_id']}")

    sections = [
        section["title"]
        for section in block["section_path"]
        if section["title"]
    ]

    context = (
        f"PostgreSQL {document['postgres_version']}\n"
        + " > ".join(sections)
    )

    return {
        "passage_id": block["block_id"],
        "source_id": document["source_id"],
        "source_title": document["title"],
        "postgres_version": document["postgres_version"],
        "source_url": document["source_url"],
        "citation_url": block["citation_url"],
        "raw_sha256": document["raw_sha256"],
        "kind": kind,
        "section_path": block["section_path"],
        "context": context,
        "text": text,
        "text_sha256": hashlib.sha256(
            text.encode("utf-8")
        ).hexdigest(),
        "character_count": len(text),
        "token_count": None,
    }


def main() -> None:
    passages = []

    for input_path in INPUT_PATHS:
        document = json.loads(input_path.read_text(encoding="utf-8"))
        source_passages = []

        for block in document["blocks"]:
            if block["kind"] == "heading":
                continue

            if block["kind"] in {"table", "definition_list"}:
                raise ValueError(
                    f"Unprepared block remains: {block['block_id']}"
                )

            try:
                passage = make_passage(document, block)
            except ValueError as error:
                raise ValueError(
                    f"{block['block_id']}: {error}"
                ) from error

            source_passages.append(passage)

        passages.extend(source_passages)
        print(
            f"{document['source_id']}: "
            f"{len(source_passages)} candidate passages"
        )

    ids = [passage["passage_id"] for passage in passages]

    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate passage IDs found.")

    OUTPUT_PATH.write_text(
        "".join(
            json.dumps(passage, ensure_ascii=False) + "\n"
            for passage in passages
        ),
        encoding="utf-8",
    )

    print(f"\nTotal candidate passages: {len(passages)}")
    print("Token sizing: pending")

    print("\nFive longest passages by character count:")
    longest = sorted(
        passages,
        key=lambda passage: passage["character_count"],
        reverse=True,
    )[:5]

    for passage in longest:
        print(
            f"  {passage['passage_id']}: "
            f"{passage['character_count']} characters"
        )


if __name__ == "__main__":
    main()