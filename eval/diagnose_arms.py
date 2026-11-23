"""
Measure each retrieval arm on its own, against the golden sources.

Why this exists
---------------
`eval_retriever.py` scores the pipeline end to end and gives one recall and one
precision number. When those move, it cannot say *which stage* moved them. Row 8
recorded hybrid retrieval as a regression and attributed it to RRF displacing good
dense candidates out of the reranker's shortlist. That attribution was a reasonable
inference from an aggregate score, and it was wrong: measuring the arms separately
showed RRF's own ordering was the best of the three, and the loss came after it.

So this reports four orderings over the same questions and the same index:

    dense      dense vectors only
    sparse     BM25 only, computed server-side by Qdrant
    fused      RRF over both, which is what `search()` returns when hybrid is on
    pipeline   whatever `retrieve()` actually does, reranker included

The gap between `fused` and `pipeline` is the reranker's contribution, with its
sign.

Metrics are document-level against `acceptable_sources`, not the LLM-judged
contextual metrics:

    hit@k   did any acceptable source appear at all  -- a retrieval question
    rank1   was an acceptable source placed first    -- an ordering question
    MRR     1/rank of the first acceptable source    -- ordering, less brittle

These deliberately do not replace the judged metrics. Document-level scoring was
dropped from the main harness because relevance is per (question, document) and a
single document can be a valid source for one question and a distractor for
another. Here that is acceptable: every arm is scored against the same qrels, so
the *comparison between arms* is sound even where an absolute number is not.

Cost: one query embedding per question, roughly $0.00002 for the whole run. BM25
costs nothing -- Qdrant computes it from the raw question text. Nothing is written.

Usage:
    uv run python -m eval.diagnose_arms
"""

from __future__ import annotations

import json
from pathlib import Path

from qdrant_client import QdrantClient
from qdrant_client.models import Document, Fusion, FusionQuery, Prefetch

from atlas.config import settings
from atlas.embeddings import embed_query
from atlas.retrieve import retrieve
from atlas.store import BM25_MODEL, DENSE, SPARSE

GOLDEN = Path(__file__).parent / "golden_dataset.json"

_client = QdrantClient(url=settings.qdrant_url)


def load_questions() -> list[dict]:
    """Questions with known sources. Refusal questions list none and are skipped."""
    raw = json.loads(GOLDEN.read_text())
    items = raw if isinstance(raw, list) else raw["questions"]
    return [q for q in items if q.get("acceptable_sources")]


def _doc_ids(response) -> list[str]:
    return [point.payload["doc_id"] for point in response.points]


def dense_arm(question: str, vector: list[float], k: int) -> list[str]:
    return _doc_ids(
        _client.query_points(
            settings.qdrant_collection, query=vector, using=DENSE, limit=k, with_payload=True
        )
    )


def sparse_arm(question: str, vector: list[float], k: int) -> list[str]:
    return _doc_ids(
        _client.query_points(
            settings.qdrant_collection,
            query=Document(text=question, model=BM25_MODEL),
            using=SPARSE,
            limit=k,
            with_payload=True,
        )
    )


def fused_arm(question: str, vector: list[float], k: int) -> list[str]:
    return _doc_ids(
        _client.query_points(
            settings.qdrant_collection,
            prefetch=[
                Prefetch(query=vector, using=DENSE, limit=settings.hybrid_prefetch),
                Prefetch(
                    query=Document(text=question, model=BM25_MODEL),
                    using=SPARSE,
                    limit=settings.hybrid_prefetch,
                ),
            ],
            query=FusionQuery(fusion=Fusion.RRF),
            limit=k,
            with_payload=True,
        )
    )


def pipeline_arm(question: str, vector: list[float], k: int) -> list[str]:
    """The real thing, via retrieve() -- so it always matches shipped behaviour."""
    return [hit.doc_id for hit in retrieve(question, k=k)]


def first_rank(got: list[str], want: set[str]) -> int | None:
    for index, doc_id in enumerate(got, start=1):
        if doc_id in want:
            return index
    return None


def main() -> None:
    k = settings.top_k
    questions = load_questions()

    arms = {"dense": dense_arm, "sparse": sparse_arm}
    if settings.hybrid_enabled:
        arms["fused"] = fused_arm
    arms["pipeline"] = pipeline_arm

    print(f"collection   {settings.qdrant_collection}")
    print(f"chunking     {settings.chunk_strategy}")
    print(f"hybrid       {settings.hybrid_enabled}")
    print(
        f"reranker     {settings.reranker_model if settings.rerank_enabled else 'off'}"
        f"  (candidates {settings.rerank_candidates if settings.rerank_enabled else '-'})"
    )
    print(f"questions    {len(questions)}  top_k {k}\n")

    scores = {name: {"hit": 0, "at1": 0, "rr": 0.0} for name in arms}
    ranks: dict[str, dict[str, int | None]] = {}

    for question in questions:
        vector = embed_query(question["question"])
        want = set(question["acceptable_sources"])
        ranks[question["id"]] = {}
        for name, arm in arms.items():
            rank = first_rank(arm(question["question"], vector, k), want)
            ranks[question["id"]][name] = rank
            if rank is not None:
                scores[name]["hit"] += 1
                scores[name]["rr"] += 1.0 / rank
                if rank == 1:
                    scores[name]["at1"] += 1

    n = len(questions)
    print(f"{'arm':<10} {f'hit@{k}':<16} {'rank1':<16} {'MRR'}")
    for name, s in scores.items():
        print(
            f"{name:<10} {s['hit']}/{n} = {s['hit'] / n:>4.0%}      "
            f"{s['at1']}/{n} = {s['at1'] / n:>4.0%}      {s['rr'] / n:.3f}"
        )

    # The question this script was written to answer.
    before = "fused" if settings.hybrid_enabled else "dense"
    if settings.rerank_enabled:
        b, a = scores[before], scores["pipeline"]
        d_hit = (a["hit"] - b["hit"]) / n
        d_at1 = (a["at1"] - b["at1"]) / n
        d_mrr = (a["rr"] - b["rr"]) / n
        verdict = "IMPROVES" if d_mrr > 0 else "DEGRADES" if d_mrr < 0 else "no change in"
        print(
            f"\nThe reranker {verdict} the {before} ordering: "
            f"hit {d_hit:+.0%}, rank1 {d_at1:+.0%}, MRR {d_mrr:+.3f}"
        )
        moved = [
            (q, r[before], r["pipeline"])
            for q, r in ranks.items()
            if r[before] != r["pipeline"]
        ]
        worse = [(q, b_, a_) for q, b_, a_ in moved if (a_ or 99) > (b_ or 99)]
        better = [(q, b_, a_) for q, b_, a_ in moved if (a_ or 99) < (b_ or 99)]
        print(f"  questions it improved: {len(better)}   worsened: {len(worse)}")
        for label, rows in (("worsened", worse), ("improved", better)):
            for q, b_, a_ in rows:
                print(f"    {label:<9} {q}: rank {b_} -> {a_}")


if __name__ == "__main__":
    main()
