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
from qdrant_client.models import (
    Distance, 
    Document,
    Fusion,
    FusionQuery,
    Modifier,
    PointStruct,
    Prefetch,
    SparseVectorParams,
    VectorParams
)

from atlas.config import settings

# Vector names. Anonymous vectors are fine with one per point; two need names,
# and the names are part of the collection schema -- changing them means a rebuild.
DENSE = "dense"
SPARSE = "bm25"

# Computed by the Qdrant server, not locally. Sending a Document instead of a
# vector is what keeps BM25 free of any Python dependency.
BM25_MODEL = "Qdrant/bm25"

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
    # Filled in by the reranker when it runs; None means dense scores only. Kept
    # beside `score` rather than replacing it so a results trace shows both the
    # original cosine rank and the reranked one.
    rerank_score: float | None = None


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

        if settings.hybrid_enabled:
            # Named vectors, because a point now carries two of them. The sparse
            # side is BM25 with the IDF modifier, which is what makes a rare term
            # like "Kothari" outweigh a common one like "board" -- Qdrant keeps
            # the corpus statistics and computes it server-side.
            _client.create_collection(
                collection_name=settings.qdrant_collection,
                vectors_config={
                    DENSE: VectorParams(
                        size=settings.embedding_dim, distance=Distance.COSINE
                    )
                },
                sparse_vectors_config={
                    SPARSE: SparseVectorParams(modifier=Modifier.IDF)
                },
            )
        else:
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

    if settings.hybrid_enabled:
        # The sparse vector is not computed here. A Document is a promise that
        # the server will tokenise this text and build the BM25 vector itself,
        # which is why hybrid needs no extra Python dependency.
        points = [
            PointStruct(
                id=index,
                vector={
                    DENSE: vector,
                    SPARSE: Document(text=payload["text"], model=BM25_MODEL)
                },
                payload=payload
            ) for index, (vector, payload) in enumerate(zip(vectors, payloads))
        ]
    else:        
        points = [
            PointStruct(id=index, vector=vector, payload=payload) 
            for index, (vector, payload) in enumerate(zip(vectors, payloads))
        ]

    _client.upsert(collection_name=settings.qdrant_collection, points=points)

    return len(points)


def search(
        query_vector: list[float], 
        limit: int | None = None,
        query_text: str | None = None,
        ) -> list[Hit]:
    """
    Nearest neighbours: dense only, or dense fused with BM25 when hybrid is on.

    Hybrid needs `query_text` as well as the vector, because BM25 matches strings
    rather than geometry. The two arms search the same corpus independently and
    Reciprocal Rank Fusion combines them -- RRF reads only the positions, never
    the scores, which is what lets a cosine similarity of 0.51 and a BM25 score of
    4.6 be compared at all.
    """

    top_k = limit or settings.top_k

    if not settings.hybrid_enabled or query_text is None:
        response = _client.query_points(
            collection_name=settings.qdrant_collection,
            query=query_vector,
            limit=top_k,
            with_payload=True
        )
        return [Hit.from_point(point) for point in response.points]

    response = _client.query_points(
        collection_name=settings.qdrant_collection,
        prefetch=[
            Prefetch(query=query_vector, using=DENSE, limit=settings.hybrid_prefetch),
            Prefetch(
                query=Document(text=query_text, model=BM25_MODEL),
                using=SPARSE,
                limit=settings.hybrid_prefetch
            ),
        ],
        query=FusionQuery(fusion=Fusion.RRF),
        limit=top_k,
        with_payload=True
    )
    return [Hit.from_point(point) for point in response.points]

def count_points() -> int:
    return _client.count(settings.qdrant_collection).count