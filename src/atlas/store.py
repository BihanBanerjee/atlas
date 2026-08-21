"""
Qdrant -- where the vectors live.

Vocabulary, since it took me a minute to keep these straight:

  collection -- a named bucket of vectors that all share one size and one
                distance metric. Mine is 1536-dim cosine, because that's what
                text-embedding-3-small hands back.

  point      -- one stored thing: an id, a vector, and a payload.

  payload    -- a JSON dict stored alongside the vector on the same point. A bare
                vector is useless on its own -- a search only returns nearest-
                neighbour ids and scores unless something says what each vector
                represents. We put the chunk text and its provenance (doc_id,
                source, title, date, chunk_index) in the payload so a search
                result already carries what synthesis needs, instead of a second
                lookup to fetch the original document by id.

Qdrant indexes with HNSW rather than comparing the query against every stored
vector. Brute force is exact but linear in collection size; HNSW is approximate
and roughly logarithmic. At 48 documents brute force would be fine -- the point
of using the real index now is that nothing changes when the corpus grows.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from atlas.config import settings

_client = QdrantClient(url=settings.qdrant_url)


@dataclass
class Hit:
    """One retrieved chunk, flattened so callers never touch Qdrant return format types."""

    score: float
    text: str
    doc_id: str
    source: str
    title: str
    date: str
    chunk_index: int


    @classmethod
    def from_point(cls, point: Any) -> "Hit":
        payload = point.payload or {}
        return cls(
            score=point.score,
            text=payload.get("text", ""),
            doc_id=payload.get("doc_id", ""),
            source=payload.get("source", ""),
            title=payload.get("title", ""),
            date=payload.get("date", ""),
            chunk_index=payload.get("chunk_index", -1)
        )


def ensure_collection(recreate: bool = False) -> None:
    """
    Create the collection if it isn't there already.

    recreate=True drops it first. Ingest uses that, because re-running with a
    different chunk size leaves the old points sitting in the collection
    alongside the new ones. Nothing errors -- searches just start returning a
    mix of two different chunkings, which is worse than an error.

    """

    exists = _client.collection_exists(settings.qdrant_collection)

    if exists and recreate:
        _client.delete_collection(settings.qdrant_collection)
        exists = False

    if not exists:
        _client.create_collection(
            collection_name=settings.qdrant_collection,
            vectors_config=VectorParams(
                size=settings.embedding_dim,
                distance=Distance.COSINE
            ),
        )


def upsert_chunks(
        vectors: list[list[float]],
        payloads: list[dict[str, Any]]
) -> int:
    """Store vectors with their payloads. Returns the number of points written."""
    if len(vectors) != len(payloads):
        raise ValueError(
            f"vector/payload length mismatch: {len(vectors)} vs {len(payloads)}"
        )

    points = [
        PointStruct(id=index, vector=vector, payload=payload) 
        for index, (vector, payload) in enumerate(zip(vectors, payloads))
    ]

    _client.upsert(collection_name=settings.qdrant_collection, points=points)

    return len(points)


def search(query_vector: list[float], limit: int | None = None) -> list[Hit]:
    """Nearest neighbours by cosine similarity. Straight top-k, nothing filtered or re-scored afterwards."""
    response = _client.query_points(
        collection_name=settings.qdrant_collection,
        query=query_vector,
        limit=limit or settings.top_k,
        with_payload=True
    )

    return [Hit.from_point(point) for point in response.points]

def count_points() -> int:
    return _client.count(settings.qdrant_collection).count