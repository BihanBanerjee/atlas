"""
Build eval/faithfulness_dataset.json — the generator's golden set.

WHAT THIS DATASET IS FOR
------------------------
Component-level evaluation of the generator, in isolation. The retriever is not
in the loop. Each row pairs a question with a *golden context*: the chunks that
genuinely answer it, chosen by hand rather than returned by a search. The
generator is then run on that context, and a judge scores the answer.

Isolation is the whole point. If the generator scores badly on retrieved
context, the cause could be the generator or the retriever and the number cannot
tell you which. Hand the generator context that is already correct and a bad
score has exactly one owner.

Two metrics read these rows, and neither needs an ideal answer:

    faithfulness      answer vs context  -- is every claim supported?
    answer relevancy  answer vs question -- is every claim on topic?

So a row carries an id, a question, and a context. Nothing else. The reference
implementation this follows (CampusX rag-eval-deepeval) does the same, and its
retriever goldens carry `ideal_answer` while its faithfulness goldens carry
`ideal_context` -- the schema is the metric's requirement, not a house style.

WHY A SCRIPT RATHER THAN A HAND-WRITTEN JSON
--------------------------------------------
The curation is the hand work: deciding which chunks answer a question, and
writing questions that tempt a model into saying more than the context supports.
That judgement lives in QUESTIONS below. Copying 20-odd chunk bodies into JSON
by hand is not judgement, it is transcription, and transcription introduces
silent drift between the dataset and the index.

Same convention as scripts/build_fixtures.py: edit the curated list at the top,
re-run the script.

HOW THE QUESTIONS WERE CHOSEN
-----------------------------
Not by reusing golden_dataset.json. Those 45 were written to stress *retrieval*
-- near-duplicates, reranking, lexical matching over paraphrase. Hand the
generator perfect context and most of that difficulty disappears, so they would
measure the generator on difficulty that is no longer in play. The reference
repo reaches the same conclusion the same way: zero overlap between its
retriever and faithfulness question sets.

What a faithfulness question wants instead is to be easy to retrieve for and
*tempting to embellish*. Four shapes do that, and each question below is tagged
with which one it is:

    gap        the context answers the question and pointedly omits an adjacent
               fact the model is likely to know is missing
    why        asks for a reason, inviting an invented rationale
    near-miss  several similar figures sit in the context; only one is the answer
    partial    the context supports part of the answer and not the rest

The five missing_data refusal questions are deliberately absent. A refusal makes
almost no claims, so faithfulness scores it trivially high and learns nothing.
Abstention is its own concern and gets its own golden file.

Usage:
    QDRANT_COLLECTION=atlas_mine_v01 uv run python scripts/build_faithfulness_dataset.py
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from qdrant_client import QdrantClient

from atlas.config import settings

# --------------------------------------------------------------------------- #
# The curated set. `context` is (doc_id, chunk_index) -- the text is pulled from
# the index at build time so it is always byte-identical to what is stored.
# --------------------------------------------------------------------------- #

QUESTIONS: list[dict[str, Any]] = [
    {
        "id": "f01",
        "shape": "near-miss",
        "question": "What did Tensile commit to Northwind on SAML SSO, and by what date?",
        "context": [("gmail-northwind-sso-commitment", 2)],
        "tempts": "The same chunk also promises audit log export by end of August. "
                  "An unfaithful answer merges the two dates or attributes the "
                  "September date to both.",
    },
    {
        "id": "f02",
        "shape": "why",
        "question": "Why was SAML SSO deferred out of the Q3 roadmap?",
        "context": [("notion-roadmap-q3-2026", 0)],
        "tempts": "The reason given is capacity and an auth-path migration. A model "
                  "reaching for completeness adds commercial consequences, the "
                  "Northwind renewal, or a revenue figure -- none of which is here.",
    },
    {
        "id": "f03",
        "shape": "partial",
        "question": "How long is the SAML SSO build estimated to take, and when would it finish?",
        "context": [("notion-roadmap-q4-2026", 1)],
        "tempts": "5-7 weeks and mid-to-late November are both stated. Whether it "
                  "would land before Northwind's 30 September renewal is not, and "
                  "is the obvious thing to volunteer.",
    },
    {
        "id": "f04",
        "shape": "partial",
        "question": "What did Linda Marsh say she needs before she will discuss the renewal price?",
        "context": [("gmail-northwind-renewal", 1)],
        "tempts": "Her condition is stated precisely. Whether Tensile can meet it is "
                  "not in this chunk, and a model that knows the roadmap answer "
                  "will want to supply it.",
    },
    {
        "id": "f05",
        "shape": "near-miss",
        "question": "What renewal price did Marcus propose to Northwind, and what did he give as justification?",
        "context": [("gmail-northwind-renewal", 0)],
        "tempts": "$84,000, $96,000, 40 users and 58 users all appear in one short "
                  "passage. The uplift percentage is not stated and invites "
                  "arithmetic presented as a quoted figure.",
    },
    {
        "id": "f06",
        "shape": "gap",
        "question": "According to the customer commitments log, what has Tensile committed to Northwind Logistics?",
        "context": [("notion-customer-commitments-log", 0)],
        "tempts": "The sharpest trap in the set. The log records audit log export "
                  "and a closed onboarding session. It does NOT record the SAML SSO "
                  "promise -- that absence is the point of the document in the "
                  "corpus. A model that has seen SSO discussed everywhere else will "
                  "want to list it here.",
    },
    {
        "id": "f07",
        "shape": "why",
        "question": "Why does the customer commitments log exist, and what problem is it meant to prevent?",
        "context": [("notion-customer-commitments-log", 1)],
        "tempts": "The stated reason is general. Naming Northwind or SSO as the "
                  "incident behind it would be invention -- the chunk says only "
                  "'gaps in this page have caused problems before'.",
    },
    {
        "id": "f08",
        "shape": "near-miss",
        "question": "What were Fernpath's headline terms in the term sheet?",
        "context": [("gmail-fernpath-term-sheet", 1)],
        "tempts": "$12M, $52M, 12%, one board seat, five board members, thirty days, "
                  "21 August. Seven figures in one short chunk; the 12% pool was "
                  "later renegotiated, but not in this chunk.",
    },
    {
        "id": "f09",
        "shape": "why",
        "question": "Why did Ravi object to the 12% option pool?",
        "context": [("gmail-fernpath-term-sheet", 2)],
        "tempts": "His reasoning is explicit, including the $6M characterisation and "
                  "the 6.5% the hiring plan needs. What Fernpath settled on is in a "
                  "different chunk and is the natural thing to append.",
    },
    {
        "id": "f10",
        "shape": "partial",
        "question": "What option pool did Fernpath propose, and what did they agree to?",
        "context": [("gmail-fernpath-term-sheet", 1), ("gmail-fernpath-term-sheet", 3)],
        "tempts": "Needs both chunks: 12% proposed, 10.5% agreed. Ravi asked for 10%, "
                  "which is in neither -- a model that states 10% as the outcome has "
                  "filled a gap rather than read one.",
    },
    {
        "id": "f11",
        "shape": "partial",
        "question": "What did Aster Ventures indicate they would offer, and why did the conversation end?",
        "context": [("gmail-aster-competing-interest", 0), ("gmail-aster-competing-interest", 1)],
        "tempts": "$10M at $45M post is stated as directional and explicitly not yet "
                  "reliable. The exclusivity that ended it is in the second chunk. "
                  "Naming Fernpath as the source of the term sheet would be "
                  "invention -- Ravi never names them to James.",
    },
    {
        "id": "f12",
        "shape": "near-miss",
        "question": "What is Elena Vasquez asking for, and how does it compare to the approved band?",
        "context": [("gmail-comp-discussion-vasquez", 0), ("gmail-comp-discussion-vasquez", 2)],
        "tempts": "$248,000 current, $265,000 asking, $240,000 band, 0.9% and 0.8%, "
                  "plus a 15% bonus. The $25,000 gap is derivable and correct to "
                  "state; a model that quotes it as though the context said it is "
                  "still faithful, one that invents a different gap is not.",
    },
    {
        "id": "f13",
        "shape": "gap",
        "question": "What did Tom Brennan say he has not done before?",
        "context": [("gmail-comp-discussion-brennan", 0)],
        "tempts": "He is specific: never owned a hiring plan or a quarterly planning "
                  "process, led six engineers only informally. The comparison to "
                  "Elena is not in this chunk and is what a model will reach for.",
    },
    {
        "id": "f14",
        "shape": "gap",
        "question": "What did the July investor update report for runway, and what did Ravi say about it?",
        "context": [("gmail-investor-update-2026-07", 1), ("gmail-investor-update-2026-07", 2)],
        "tempts": "The context says eight months. Seven months appears elsewhere in "
                  "the corpus as the August figure, and a model that answers seven "
                  "has used knowledge the context does not contain.",
    },
    {
        "id": "f15",
        "shape": "why",
        "question": "Why do the Q3 OKRs leave enterprise identity out of the enterprise-readiness objective?",
        "context": [("notion-okrs-q3-2026", 1)],
        "tempts": "The stated reason is capacity and a refusal to commit to what "
                  "cannot be done. The Q4 schedule is mentioned; the 5-7 week "
                  "estimate and the Northwind consequences are not.",
    },
    {
        "id": "f16",
        "shape": "gap",
        "question": "What does the Northwind master services agreement say about renewal?",
        "context": [("drive-northwind-msa", 0)],
        "tempts": "No automatic renewal, a new Order Form required before expiry, "
                  "term ending 30 September 2026. The contract contains no "
                  "commitment about SSO or identity at all -- that absence is "
                  "load-bearing in this corpus, and a model that has read the "
                  "renewal thread will want to connect the two.",
    },
    {
        "id": "f17",
        "shape": "gap",
        "question": "What did Dana tell Northwind about SOC 2 in the security questionnaire response?",
        "context": [("gmail-northwind-security-review", 1)],
        "tempts": "No report, auditor selected, observation window from October, "
                  "report roughly mid-2027. Karin's verdict that it is 'noted but "
                  "not blocking' is in the next chunk and is the natural thing to "
                  "append as reassurance.",
    },
    {
        "id": "f18",
        "shape": "gap",
        "question": "What does the Head of Engineering scorecard list as must-haves for the role?",
        "context": [("notion-head-of-engineering-scorecard", 0)],
        "tempts": "Four must-haves are listed, with nice-to-haves beside them to be "
                  "confused for them. The approved band is in the next chunk and "
                  "neither candidate is named anywhere here.",
    },
    {
        "id": "f19",
        "shape": "why",
        "question": "Why was the Head of Engineering band set where it was?",
        "context": [("notion-head-of-engineering-scorecard", 1)],
        "tempts": "The reason is concrete and slightly odd -- losing candidates at "
                  "the 40th percentile and six weeks per attempt. Generic market "
                  "reasoning in its place would be invention.",
    },
    {
        "id": "f20",
        "shape": "why",
        "question": "Why does pitch deck v4 describe the enterprise gap as a capacity problem rather than a research problem?",
        "context": [("drive-pitch-deck-v4", 1)],
        "tempts": "Because the builds are known, scoped and six-to-eight weeks. Note "
                  "that figure disagrees with the Q4 roadmap's 5-7 weeks for SSO -- "
                  "faithful here means quoting what this chunk says, not the "
                  "estimate the corpus gives elsewhere.",
    },
    {
        "id": "f21",
        "shape": "near-miss",
        "question": "What did Dana report about audit logging in the security questionnaire?",
        "context": [("gmail-northwind-security-review", 1)],
        "tempts": "Ninety days, internal only, no customer-facing export. Twelve "
                  "months is the figure everywhere else in the corpus -- it is what "
                  "Northwind asked for and what Tensile later promised. Answering "
                  "twelve months here is reading the requirement as the reality.",
    },
    {
        "id": "f22",
        "shape": "near-miss",
        "question": "What is Tensile asking to raise, and what does the deck say the money buys?",
        "context": [("drive-pitch-deck-v4", 2)],
        "tempts": "$12M, $52M post, twenty-four months of runway, five engineering "
                  "hires, three commercial, and five percentages that must sum "
                  "to 100. Dense enough to drop a line or round one, and the "
                  "headcount and the fund split are easy to conflate.",
    },
    {
        "id": "f23",
        "shape": "partial",
        "question": "What are the fee terms in the Northwind master services agreement?",
        "context": [("drive-northwind-msa", 0)],
        "tempts": "$84,000 annually, forty Named Users included, $150 per user per "
                  "month above that, net thirty. The 58 users they have grown to and "
                  "the $96,000 proposal are both elsewhere and both tempting.",
    },
    {
        "id": "f24",
        "shape": "partial",
        "question": "What did Northwind put on their remediation register after the security review, and did anything block continued use?",
        "context": [("gmail-northwind-security-review", 2)],
        "tempts": "Two items and an explicit no-blocking-findings verdict. The "
                  "September dates, the renewal and the eventual SSO commitment are "
                  "not in this chunk; the register is a requirements list, not a "
                  "timeline.",
    },
]


def fetch_chunks(client: QdrantClient, collection: str) -> dict[tuple[str, int], dict[str, Any]]:
    """
    Every stored chunk, keyed by (doc_id, chunk_index).

    That key has to be unique for this to be a lookup rather than a guess, and
    nothing in Qdrant enforces it -- the point id is the unique field, and it
    is not this one. I was treating a convention as a constraint.

    A normal ingest calls ensure_collection(recreate=True) and starts from
    empty, so duplicates cannot come from that. They would come from a partial
    re-ingest, or an upsert after the point-id scheme changes.

    So both ways the key can go wrong now raise. `out[key] = payload` let the
    last writer win, which means the dataset would have been built from
    whichever chunk came back last in scroll order -- and every faithfulness
    number after it computed against text nobody picked.
    """
    out: dict[tuple[str, int], dict[str, Any]] = {}
    offset = None
    while True:
        points, offset = client.scroll(
            collection_name=collection, limit=256, offset=offset,
            with_payload=True, with_vectors=False,
        )
        for point in points:
            payload = point.payload or {}
            doc_id, chunk_index = payload.get("doc_id"), payload.get("chunk_index")

            if doc_id is None or chunk_index is None:
                raise SystemExit(
                    f"point {point.id} has doc_id={doc_id!r} chunk_index={chunk_index!r}. "
                    "Both are needed to address a chunk; without them every such "
                    "point collapses onto one key."
                )

            key = (doc_id, chunk_index)
            if key in out:
                raise SystemExit(
                    f"two points share ({doc_id}, {chunk_index}) in {collection}. "
                    "Chunk addresses have to be unique. Re-ingest to rebuild the "
                    "collection from scratch rather than upserting over it."
                )
            out[key] = payload

        if offset is None:
            break
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the generator's faithfulness golden set.")
    parser.add_argument("--out", type=Path, default=Path("eval/faithfulness_dataset.json"))
    args = parser.parse_args()

    client = QdrantClient(url=settings.qdrant_url)
    collection = settings.qdrant_collection
    if not client.collection_exists(collection):
        raise SystemExit(f"collection {collection!r} not found at {settings.qdrant_url}")

    chunks = fetch_chunks(client, collection)

    rows: list[dict[str, Any]] = []
    for spec in QUESTIONS:
        ideal_context: list[str] = []
        sources: list[str] = []
        source_meta: list[dict[str, Any]] = []
        for doc_id, chunk_index in spec["context"]:
            payload = chunks.get((doc_id, chunk_index))
            if payload is None:
                # Loud, not silent. A missing chunk means the index was rebuilt
                # with different boundaries and the curation needs revisiting --
                # quietly dropping it would leave a question with thinner context
                # than it was written for, and the score would move for a reason
                # nobody could see.
                raise SystemExit(
                    f"{spec['id']}: chunk ({doc_id}, {chunk_index}) is not in {collection}. "
                    "The index has been re-chunked since this set was curated."
                )
            ideal_context.append(payload["text"])
            sources.append(f"{doc_id}#{chunk_index}")
            # The generator does not see bare text. ingest.py stores these
            # fields and generate.py renders them into the source header the
            # model reads, and prompt rule 2 ("sources are dated") depends on
            # the date being there. Carried here so the eval can reproduce the
            # production prompt exactly rather than a stripped version of it.
            source_meta.append({
                "source": payload.get("source"),
                "title": payload.get("title"),
                "date": str(payload.get("date", "")),
            })

        rows.append({
            "id": spec["id"],
            "question": spec["question"],
            "ideal_context": ideal_context,
            "source_chunks": sources,
            "source_meta": source_meta,
            "shape": spec["shape"],
            "tempts": spec["tempts"],
        })

    payload = {
        "_meta": {
            "description": "Golden question/context pairs for component-level evaluation "
                           "of the generator, in isolation from the retriever.",
            "built_by": "scripts/build_faithfulness_dataset.py",
            "metrics": ["faithfulness", "answer relevancy"],
            "no_ideal_answer": "Neither metric reads an expected answer. Faithfulness "
                               "compares the answer to the context; answer relevancy "
                               "compares it to the question.",
            "context_is_verbatim": f"Chunk text copied from {collection} at build time, "
                                   "byte-identical to what is indexed.",
            "collection_points": len(chunks),
            # The local repo's settings, NOT a property of the collection, which
            # does not record how its chunks were made. These usually match --
            # but the script can be run from a repo whose .env points somewhere
            # else, and then this describes the machine rather than the data.
            # Recorded because the chunk shape is worth knowing, labelled so it
            # is not mistaken for a fact about the index.
            "local_chunking_config": {
                "strategy": settings.chunk_strategy,
                "boundary_encoder": settings.boundary_encoder,
                "percentile": settings.semantic_percentile,
                "min_tokens": settings.semantic_min_tokens,
                "max_tokens": settings.semantic_max_tokens,
            },
            "caveat": "The context reflects the chunking live when this was built. It "
                      "stays valid for measuring the generator, because the text is "
                      "frozen here -- but after a re-chunk it no longer describes what "
                      "retrieval would return, and must not be read as though it does.",
            "excludes": "The five missing_data refusal questions. A refusal makes almost "
                        "no claims, so faithfulness scores it trivially. Abstention is a "
                        "separate concern with its own golden file.",
            "questions": len(rows),
        },
        "questions": rows,
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, ensure_ascii=False))

    shapes: dict[str, int] = {}
    for r in rows:
        shapes[r["shape"]] = shapes.get(r["shape"], 0) + 1
    ctx_counts = [len(r["ideal_context"]) for r in rows]

    print(f"wrote {len(rows)} questions to {args.out}")
    print(f"  source      {collection}")
    print(f"  contexts    {sum(ctx_counts)} chunks, "
          f"{min(ctx_counts)}-{max(ctx_counts)} per question, "
          f"mean {sum(ctx_counts)/len(ctx_counts):.1f}")
    for shape in ("gap", "why", "near-miss", "partial"):
        if shape in shapes:
            print(f"  {shape:<11}{shapes[shape]:>3}")


if __name__ == "__main__":
    main()
