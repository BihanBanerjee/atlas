"""
Component-level evaluation of the retriever, on its own.

This script never calls the generator. It embeds a question, pulls chunks out of
Qdrant, and hands those chunks to a judge. Nothing is synthesized, so a bad score
here can only be a retrieval problem -- which is the entire point of evaluating
components separately. A wrong final answer cannot tell you whether the retriever
missed or the model wandered; this can.

TWO METRICS, AND WHY THESE TWO
------------------------------
  Contextual Recall     -- decomposes the ideal answer into claims and asks how
                           many are supported by the retrieved chunks. Low recall
                           means the answer was never in the prompt, and nothing
                           downstream can rescue it.

  Contextual Precision  -- judges each retrieved chunk against the ideal answer,
                           weighted by rank. [relevant, relevant, noise, noise,
                           noise] scores higher than [noise, noise, noise,
                           relevant, relevant] even though both are 2 useful out
                           of 5. Rank matters because the generator reads from the
                           top.

Both are reference-based: they need `expected_answer` from the golden set, which
is why those answers were enriched to carry two or three claims each. A one-value
answer ("$940,000.") decomposes to a single claim and makes recall binary.

WHAT IS NOT MEASURED HERE
-------------------------
The five `missing_data` questions are excluded. Their ideal answer is "this is not
in the corpus", and asking a judge to attribute that to retrieved chunks produces
noise rather than a score. Refusal behaviour belongs to the generator evaluation,
as a binary did-it-decline check. 23 of 28 questions are scored.

`actual_output` is deliberately not set on the test cases. Neither metric lists it
in `_required_params` (verified against deepeval 4.2.6), and omitting it keeps the
script honest: no generator ran, so no generator output is pretended.

COST
----
Measured on a comparable run: roughly $0.003 per question for both metrics with a
small judge, so a full 23-question pass is around $0.07. Cheap enough to run on
the whole set while tuning rather than sampling.

Usage:
    uv run python -m eval.eval_retriever

Takes no arguments. To tune, change the value in .env and run it again -- the
config is the single source of truth for what the system is actually doing, and
every value that could move a score is read from it and recorded with the result.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from deepeval import evaluate
from deepeval.metrics import (
    ContextualPrecisionMetric, 
    ContextualRecallMetric
)
from deepeval.test_case import LLMTestCase

from atlas.config import settings
from atlas.retrieve import retrieve

# Constants, not flags, on purpose. Swapping judges between runs moves scores for
# reasons that have nothing to do with retrieval, and the threshold only decides
# whether a case prints as pass or fail -- it never changes the score being
# recorded. Change either here, deliberately, and note it in the results log.
JUDGE = "gpt-4.1-mini"
THRESHOLD = 0.7

# deepeval writes the full record of the most recent run here and overwrites it
# on the next one. Tuning is a sequence of runs, so each is copied out before the
# next can clobber it.
LATEST_RUN = Path(".deepeval/.latest_test_run.json")


def load_questions() -> list[dict]:
    """The 23 scoreable questions: everything except the deliberate refusals."""
    data = json.loads(settings.golden_dataset.read_text())
    return [q for q in data["questions"] if not q.get("expect_refusal")]

def build_test_cases(questions: list[dict], k:int) -> tuple[list[LLMTestCase], list[dict]]:
    """
    Retrieve once per question and wrap each result as a deepeval test case.

    `retrieval_context` is passed in the order the retriever returned it. Sorting
    or deduplicating it here would destroy exactly what contextual precision is
    measuring.
    """

    cases: list[LLMTestCase] = []
    records: list[dict] = []

    for question in questions:
        hits = retrieve(question["question"], k=k)
        cases.append(
            LLMTestCase(
                name=question["id"],
                input=question["question"],
                expected_output=question["expected_answer"],
                retrieval_context=[hit.text for hit in hits]
            )
        )

        records.append(
            {
                "id": question["id"],
                "category": question["category"],
                "retrieved": [
                    {"doc_id": hit.doc_id, "chunk_index": hit.chunk_index, "score": hit.score} 
                    for hit in hits
                ],
            }
        )

    return cases, records

def archive_run(label: str, records: list[dict], hyperparameters: dict) -> Path | None:
    """
    Copy deepeval's run file somewhere permanent, with the retrieval trace beside it.

    deepeval records scores and the judge's reasoning but not which documents came
    back. When a score is low the first question is always "what did it actually
    retrieve", so that goes in the same file.
    """
    settings.results_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    out = settings.results_dir / f"retriever-{stamp}-{label}.json"

    payload: dict = {"label": label, "timestamp": stamp, "hyperparameters": hyperparameters}
    if LATEST_RUN.exists():
        payload["deepeval_run"] = json.loads(LATEST_RUN.read_text())
    else:
        payload["deepeval_run"] = None
        print(f"warning: {LATEST_RUN} not found -- scores were not archived")

    payload["retrieval"] = records
    out.write_text(json.dumps(payload, indent=2))
    return out

def main() -> None:
    # No arguments, deliberately. Every tunable is read from settings, which is
    # what the application itself reads -- a --top-k flag would let this script
    # measure k=8 while synthesize.py still ran k=5, and the score would not
    # describe the system. Change .env, then run this.
    top_k = settings.top_k

    # The archived filename carries the knob most likely to have changed, so a
    # results folder is readable without opening anything.
    label = f"k{top_k}"

    questions = load_questions()

    print(f"scoring {len(questions)} questions (5 refusal questions excluded)")
    print(f"  top_k={top_k}  judge={JUDGE}  collection={settings.qdrant_collection}")


    cases, records = build_test_cases(questions, k=top_k)

    metrics = [
        ContextualRecallMetric(threshold=THRESHOLD, model=JUDGE, include_reason=True), 
        ContextualPrecisionMetric(threshold=THRESHOLD, model=JUDGE, include_reason=True),
    ]

    # Everything that could move a score, recorded with the score, and read from
    # settings at runtime rather than typed by hand -- a log that says "precision
    # 0.48" without saying which top_k or chunk size produced it is unreadable a
    # week later, and one maintained by hand eventually says the wrong thing.
    
    hyperparameters = {
        "top_k": top_k,
        "chunk_tokens": settings.chunk_tokens,
        "chunk_overlap": 0,
        "chunk_strategy": "fixed_token_window",
        "embedded_text": "body_only",
        "embedding_model": settings.embedding_model,
        "embedding_dim": settings.embedding_dim,
        "distance": "cosine",
        "judge_model": JUDGE,
        "threshold": THRESHOLD,
        "collection": settings.qdrant_collection,
        "questions_scored": len(questions),
    }

    evaluate(test_cases=cases, metrics=metrics, hyperparameters=hyperparameters)

    out = archive_run(label, records, hyperparameters)
    print(f"\narchived to {out}")


if __name__ == "__main__":
    main()