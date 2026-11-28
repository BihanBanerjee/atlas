"""
Pipeline-level evaluation: the retriever and the generator, together.

The two component evals each cut the system in half on purpose. `eval_retriever`
calls `retrieve()` and stops, so a bad score is a retrieval problem and nothing
else. `eval_generator` skips retrieval entirely and feeds the model curated
context from the golden file, so a bad score is a generation problem and nothing
else. One owner per number, which is what made g1's four failures diagnosable.

This gives that up deliberately, and the one line that does it is the context:

    eval_generator.py    retrieval_context  <- row["ideal_context"], from a file
    eval_rag_pipeline.py retrieval_context  <- answer.hits, from Qdrant

Nothing else about the measurement changes. Same judge, same threshold, same
formatting, two of the same three metrics. The context stops being curated and
starts being whatever the retriever actually found, which is the only thing a
user ever gets.

THE TRIAD, AND WHY ALL THREE ONLY MAKE SENSE HERE
-------------------------------------------------
  Contextual Relevancy  -- splits the RETRIEVED CONTEXT into statements and asks
                           of each whether it is relevant to the question.
                           Relevant / total. This metric cannot exist at
                           component level: the generator eval's context was
                           hand-picked, so scoring its relevance would be
                           scoring the person who picked it.

  Faithfulness          -- splits the ANSWER into claims and checks each against
                           the context. Supported / total.

  Answer Relevancy      -- splits the ANSWER into claims and asks of each whether
                           it helps answer the question. It never sees the
                           context.

All three are reference-free: none of them reads `expected_answer`. The golden
set is used here only as a list of questions. (`ContextualRelevancyMetric` does
require `actual_output` on the test case even though it never judges it -- a
deepeval requirement, not a conceptual one.)

WHICH GOLDEN SET, AND WHY THIS ONE
----------------------------------
`faithfulness_dataset.json` -- the same 24 questions the generator eval uses,
not the 45 in `golden_dataset.json`. Only the questions are read: `ideal_context`
sits unused, which is precisely the point.

That makes this file and `eval_generator.py` differ in exactly one variable. Run
them back to back and the only thing that changed is where the context came
from, so the gap between the two faithfulness numbers is attributable to the
retriever and nothing else. Using the 45-question set instead would have changed
the questions *and* the context source at once, and the gap would mean two
things.

The cost of that choice: these 24 were written to be easy to retrieve for -- the
near-duplicate and recency traps that make `golden_dataset.json` hard were
deliberately left out, because a question that is hard to retrieve for stops
testing the generator once the context is perfect. So the retrieval here is
gentler than the corpus's real difficulty, and the pipeline score will be
optimistic as an absolute. It is a controlled comparison, not a field report.

WHAT THE NUMBER IS FOR
----------------------
Faithfulness and answer relevancy were already measured at component level: run
g1 scored 0.94 and 0.92 on curated context. Re-measuring them on retrieved
context is not a repeat. **The delta between the two is the retriever's cost to
generation quality** -- the amount of answer quality lost between perfect
context and real context. That number does not exist anywhere else, and it is
the reason this file is worth its API spend.

For that subtraction to be legitimate the two runs must differ in exactly one
thing. So this file keeps g1's question set, g1's judge (`gpt-4.1-mini`), g1's
threshold (0.70) and g1's context formatting, and changes only where the context
comes from.

WHY THE CONTEXT CARRIES ITS SOURCE HEADERS
------------------------------------------
`retrieval_context` is built with `_format_sources`, so each entry looks like

    [2] source=gmail | title=Northwind renewal | date=2026-06-11
    <chunk text>

rather than bare chunk text. Two reasons, one of which is a tradeoff:

  1. The generator is told "sources are dated, prefer the one covering the
     asked-about period". That date exists only in the header. Hand the judge
     bare text and a correctly dated claim reads as unsupported -- the eval would
     penalise the generator for the eval's own omission.

  2. g1 was scored this way, and the g1 comparison above is the point of the run.

The tradeoff: contextual relevancy extracts its statements from this same text,
so header lines are likely to be counted as statements and judged irrelevant to
the question. That inflates the denominator and biases contextual relevancy
*down* by an unmeasured amount. It is recorded here rather than silently
accepted, and it is a reason to read contextual relevancy as a relative number
between runs rather than an absolute.

The `start=` argument is load-bearing: formatting each hit on its own restarts
the numbering, so every block comes out as [1] and an answer citing [3] is
judged against a context where [3] does not exist.

WHAT IS NOT MEASURED HERE
-------------------------
Abstention. This set carries no refusal questions -- the five `missing_data`
goldens live in `golden_dataset.json` and are not read here. That is not an
accident of the set choice: a refusal asserts almost nothing, so faithfulness
scores it ~1.00 whatever it says, and v0.1 measured RAGAS zeroing honest hedges
on answer relevancy. Abstention needs its own golden file and its own check.

Also not measured: the hard retrieval cases. q43's recency failure and the
monthly-ARR near-duplicates are in `golden_dataset.json` and stay there. The
retriever eval is where those are scored.

COST
----
Extrapolated from g1 ($0.088 for the same 24 questions with two of these three
metrics): generation is g1's $0.027 plus retrieval, and judging adds a third
metric that decomposes five chunks per question rather than one answer. Call it
**$0.15-0.20 per run**, with contextual relevancy the expensive part.

Unlike the generator eval, this one needs Qdrant running and the collection
built with the config in `.env`. If `hybrid_enabled` was turned on after the
index was built, rebuild it first: hybrid changes the collection schema.

Usage:
    uv run python -m eval.eval_rag_pipeline
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from deepeval import evaluate
from deepeval.evaluate import AsyncConfig
from deepeval.metrics import (
    AnswerRelevancyMetric,
    ContextualRelevancyMetric,
    FaithfulnessMetric,
)
from deepeval.test_case import LLMTestCase

from atlas.config import settings
from atlas.generate import _format_sources, answer_question

# Same two constants as the other evals, and for the same reason: a judge or
# threshold that moves between runs moves the scores for reasons that have
# nothing to do with the system. The g1 comparison depends on these matching
# eval_generator.py exactly.
JUDGE = "gpt-4.1-mini"
THRESHOLD = 0.7

# settings.model_dump() is the config record, so the two credential fields have
# to come out of it -- the archive is committed.
SECRETS = {"anthropic_api_key", "openai_api_key"}

# The generator eval's set, read for its questions only. Same constant as
# eval_generator.py, deliberately: the two runs are a matched pair.
GOLDEN = Path(__file__).parent / "faithfulness_dataset.json"

LATEST_RUN = Path(".deepeval/.latest_test_run.json")


def archive(records: list[dict[str, Any]], hyperparameters: dict[str, Any]) -> Path:
    """
    deepeval's run file, plus the answers and the chunks that produced them.

    deepeval keeps the score and the judge's reasoning but neither the answer nor
    what was retrieved, and those are exactly what a low score sends you looking
    for. Two of g1's four failures were shown to be judge errors by re-reading
    the archived answers; regenerating them would have cost another run.
    """
    settings.results_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    out = settings.results_dir / f"pipeline-{stamp}.json"
    out.write_text(json.dumps({
        "timestamp": stamp,
        "hyperparameters": hyperparameters,
        "deepeval_run": json.loads(LATEST_RUN.read_text()) if LATEST_RUN.exists() else None,
        "answers": records,
    }, indent=2, ensure_ascii=False))
    return out


def main() -> None:
    # Questions only. `ideal_context` is in this file and is deliberately not
    # read -- that substitution is the entire difference from eval_generator.py.
    # Because here we are doing the pipeline evaluation, the retriever and the evaluator are connected, forming a pipeline. 
    # This is a pipeline-level evaluation. That's why we will not be taking into consideration the golden contexts that were crafted by us. 
    # Rather, I would like the retriever to retrieve the context so that the whole pipeline gets evaluated.
    golden = json.loads(GOLDEN.read_text())["questions"]

    print(f"full pipeline on {len(golden)} questions from {GOLDEN.name}  "
          f"collection={settings.qdrant_collection} hybrid={settings.hybrid_enabled} "
          f"rerank={settings.reranker_model if settings.rerank_enabled else 'off'}")

    cases: list[LLMTestCase] = []
    records: list[dict[str, Any]] = []

    for question in golden:
        answer = answer_question(question["question"])
        cases.append(LLMTestCase(
            name=question["id"],
            input=question["question"],
            actual_output=answer.text,
            # Per hit, not joined: faithfulness attributes each claim to a
            # source, and one concatenated blob would lose which supported what.
            retrieval_context=[
                _format_sources([hit], start=index)
                for index, hit in enumerate(answer.hits, start=1)
            ],
        ))
        records.append({
            "id": question["id"],
            "shape": question["shape"],
            "question": question["question"],
            "answer": answer.text,
            "retrieved": [f"{hit.doc_id}#{hit.chunk_index}" for hit in answer.hits],
            "tokens_in": answer.input_tokens,
            "tokens_out": answer.output_tokens,
        })

    # The whole config, read from the object the application itself reads. A
    # hand-written dict here drifts the moment a setting is added, and an
    # archived run labelled with the wrong chunk strategy is worse than one
    # labelled with none.
    hyperparameters = settings.model_dump(exclude=SECRETS) | {
        "golden_set": GOLDEN.name,
        "judge_model": JUDGE,
        "threshold": THRESHOLD,
        # The flag that distinguishes this run from g1 in the archive. Same set,
        # same judge, same formatting -- this is the one thing that differs.
        "retriever_in_loop": True,
        "questions_scored": len(cases),
        "generation_tokens_in": sum(r["tokens_in"] for r in records),
        "generation_tokens_out": sum(r["tokens_out"] for r in records),
    }

    print(f"generated {len(cases)} answers, "
          f"{hyperparameters['generation_tokens_out']} output tokens. Judging...\n")

    # Three metrics, and contextual relevancy decomposes every retrieved chunk
    # rather than one answer -- so judge load is higher here than in either
    # component eval. Same throttle, same measured reason: 23 questions passed
    # unthrottled and 40 returned 429 against the 200k TPM ceiling.
    evaluate(
        test_cases=cases,
        metrics=[
            ContextualRelevancyMetric(threshold=THRESHOLD, model=JUDGE, include_reason=True),
            FaithfulnessMetric(threshold=THRESHOLD, model=JUDGE, include_reason=True),
            AnswerRelevancyMetric(threshold=THRESHOLD, model=JUDGE, include_reason=True),
        ],
        hyperparameters=hyperparameters,
        async_config=AsyncConfig(max_concurrent=5, throttle_value=1),
    )

    print(f"\narchived to {archive(records, hyperparameters)}")


if __name__ == "__main__":
    main()
