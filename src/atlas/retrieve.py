"""
Query -> vector -> nearest neighbours, optionally reordered by a cross-encoder.

v0.1 was dense-only: one embedding, one cosine search, top 5. Measuring it showed
recall of 0.95 against precision of 0.75 -- the right chunks were coming back and
landing at ranks 3 to 5, below chunks that were merely on-topic. That is a ranking
problem, and no retrieval parameter fixed it: sweeping chunk size, overlap and
top_k moved nothing outside the judge's noise floor.

So when `rerank_enabled` is on this becomes two stages. The vector search widens
to `rerank_candidates` and stops being asked to rank -- it only has to get the
answer into the shortlist, which it already does well. The cross-encoder then
reads each candidate against the question and decides the order.

Still missing, and both are later versions:

  v0.3 (hybrid)    -- dense embeddings blur exact strings. "Fernpath" and
                      "Northwind" are distinctive tokens that BM25 matches
                      exactly and cosine similarity smears together.
"""


from __future__ import annotations


from atlas.config import settings
from atlas.embeddings import embed_query
from atlas.store import Hit, search as vector_search


def retrieve(question: str, k: int | None = None) -> list[Hit]:
    """Return the top-k chunks for a question, most similar first."""
    top_k = k or settings.top_k
    query_vector = embed_query(question)

    if not settings.rerank_enabled:
        return vector_search(query_vector, limit=top_k)

    # Imported lazily so that turning reranking off keeps torch out of the
    # process entirely.
    from atlas.rerank import rerank

    # Never fetch fewer candidates than the caller asked to keep, or the
    # reranker would be handed less than it has to return.
    candidates = vector_search(query_vector, limit=max(settings.rerank_candidates, top_k))
    return rerank(question, candidates, top_k)
        