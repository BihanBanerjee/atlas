"""
Corpus -> chunks -> vectors -> Qdrant.

WHY THE FULL CORPUS AND NOT THE FIXTURES
----------------------------------------
Started out pointing this at eval/fixtures/*.json -- the curated 48-document
subset, 63 chunks. Switched to the full corpus instead.

The fixture set is clean: almost everything in it is relevant to some question.
But the corpus is roughly half noise by design (PERSONA.md), and that noise is
concentrated in exactly the neighbourhoods the questions live in -- financials,
compensation, renewals, identity. Indexing only the clean subset means testing
retrieval against a problem that's easier than the one the corpus was built to
pose.

256 documents -> 272 chunks, 53% of them noise tier. If retrieval can find the
right chunk in that, the number means something.

The golden dataset needed no changes: acceptable_sources are document ids, and
all of those documents are in the corpus. Did check the five expect_refusal
questions against the 208 documents that weren't in the fixture set -- none of
them answers a deliberate gap, so the refusals still hold.

One thing to be careful about: whatever's indexed has to stay fixed. Change the
size of the index halfway through and any before/after comparison is measuring
two different things at once.

Run:  uv run python -m atlas.ingest
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from atlas.chunking import chunk_text
from atlas.config import settings
from atlas.embeddings import embed_texts
from atlas.store import count_points, ensure_collection, upsert_chunks

CORPUS_DIRS = ["gmail", "notion", "drive"]

def parse_doc(path: Path) -> dict[str, Any]:
    """
    Split a corpus file into its YAML frontmatter plus body.

    Same logic as scripts/build_fixtures.py -- deliberately duplicated rather
    than imported, because scripts/ is tooling that runs standalone and src/ is
    the application. Importing across that line would make the package depend on
    a script directory that is not part of it.
    """
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        raise ValueError(f"{path} has no frontmatter")
    _, frontmatter_text, body = text.split("---", 2)
    doc = yaml.safe_load(frontmatter_text) or {}
    doc["body"] = body.strip()
    doc["_file"] = path.name
    return doc

def _doc_meta(doc: dict[str, Any]) -> tuple[str, str]:
    """
    Pull (title, date) out of a corpus document.

    The three sources do not share field names -- each inherited whatever its
    own frontmatter used:

      gmail  -> subject,          date
      notion -> title,   created/updated
      gdrive -> title,   created/updated

    Note also that `source` is "gdrive", not "drive". Hard-coding either
    assumption gives you silently empty payload fields rather than an error.
    """
    title = doc.get("title") or doc.get("subject") or doc.get("_file", "")
    date = doc.get("date") or doc.get("updated") or doc.get("created") or ""
    return str(title), str(date)

def load_corpus() -> list[dict[str, Any]]:
    """Read every markdown file under data/corpus/{gmail,notion,drive}"""
    docs: list[dict[str, Any]] = []
    for name in CORPUS_DIRS:
        directory = settings.corpus_dir / name
        if not directory.exists():
            raise FileNotFoundError(f"{directory} missing")
        for path in sorted(directory.glob("*.md")):
            docs.append(parse_doc(path))
    return docs

def build_chunks(docs: list[dict[str, Any]]) -> tuple[list[str], list[dict[str, Any]]]:
    """Flatten documents into parallel lists of chunk text and payloads."""
    texts: list[str] = []
    payloads: list[dict[str, Any]] = []

    for doc in docs:
        title, date = _doc_meta(doc)
        for index, chunk in enumerate(chunk_text(doc.get("body", ""))):
            texts.append(chunk)
            payloads.append(
                {
                "text": chunk,
                "doc_id": doc["id"],
                "source": doc.get("source", ""),
                "title": title,
                "date": date,
                "tier": doc.get("tier", ""),
                "chunk_index": index
                }
            )

    return texts, payloads


def main() -> None:
    docs = load_corpus()
    print(f"loaded {len(docs)} corpus documents")

    texts, payloads = build_chunks(docs)

    tiers: dict[str, int] = {}
    for payload in payloads:
        tiers[payload["tier"]] = tiers.get(payload["tier"], 0) + 1 

    print(f"produced {len(texts)} chunks at {settings.chunk_tokens} tokens each")
    print(f" by tier: {tiers}")


    print(f"embedding with {settings.embedding_model} ...")
    vectors = embed_texts(texts)


    # recreate=True: re-running with different chunking would otherwise leave 
    # stale points behind and mix two chunkings in one collection.
    ensure_collection(recreate=True)
    written = upsert_chunks(vectors, payloads)

    print(f"upserted {written} points into '{settings.qdrant_collection}'")
    print(f"collection now holds {count_points()} points")


if __name__ == "__main__":
    main()