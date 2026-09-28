"""
Second-stage reranking with a local cross-encoder.

THE DIFFERENCE FROM THE VECTOR SEARCH
-------------------------------------
The retriever is a bi-encoder: the chunk was turned into a vector at ingest time,
weeks before anyone asked anything, so that vector is one summary that has to
serve every possible future question. A cross-encoder instead reads the question
and the chunk *together* and emits a single relevance score, so it can notice
that a chunk about renewal pricing happens to contain the sentence answering a
question about user counts.

Measured example from this corpus: for "How many named users does Northwind have
now, versus at signature?", the chunk containing "gone from 40 to 58 active users
since signature" ranked fifth of five, at 0.345 against an irrelevant top hit at
0.393. The whole spread was 0.048 -- the dense scores could barely tell those
five apart. The answer is in the text; the summary vector does not say so.

WHY IT ONLY SEES A SHORTLIST
----------------------------
A cross-encoder cannot precompute anything. It runs once per (question, chunk)
pair at query time, so scoring a whole collection does not scale. The two stages
divide the work: the bi-encoder gets the answer into the candidate set, the
cross-encoder decides the order within it. That also changes what the retriever
is being asked for -- "somewhere in the top 20" rather than "first" -- which is
the easier job it is already good at.

It cannot rescue recall. If the answer is not in the candidates, no amount of
reordering invents it.
"""

from __future__ import annotations

from dataclasses import replace

from atlas.config import settings
from atlas.store import Hit

# The model is a few hundred MB and takes a second or two to load, so it is built
# on first use and kept. Importing this module must stay cheap -- ingest.py and
# the eval runner both import the package without necessarily reranking.
_model = None


def _get_model():
    global _model
    if _model is None:
        # Imported here rather than at module scope: sentence-transformers pulls
        # in torch, which is slow to import and unnecessary when reranking is off.
        from sentence_transformers import CrossEncoder

        _model = CrossEncoder(settings.reranker_model)
    return _model


def rerank(question: str, hits: list[Hit], top_k: int) -> list[Hit]:
    """
    Reorder `hits` by cross-encoder relevance and return the best `top_k`.

    The original cosine score stays on `Hit.score`; the new one lands on
    `rerank_score`. Keeping both means a results trace can show what moved.
    """
    if not hits:
        return []

    model = _get_model()
    scores = model.predict([(question, hit.text) for hit in hits])

    scored = [replace(hit, rerank_score=float(score)) for hit, score in zip(hits, scores)]
    scored.sort(key = lambda hit: hit.rerank_score, reverse=True)
    return scored[:top_k]
