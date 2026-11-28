"""
Component-level evaluation of the generator, in isolation from the retriever.

`eval_retriever.py` scores what comes back from Qdrant and never generates
anything. This does the opposite: it hands the generator context already known
to be correct, and scores only what the generator does with it.

That separation is the point. Run the generator on retrieved context and a low
faithfulness score has two possible owners -- the retriever put something
useless in the window, or the generator ignored what was there -- and the number
cannot say which. Hand it curated context and a low score has exactly one.

So this does not call `answer_question()`: that retrieves first, which would put
the retriever back in the loop. It calls the same system prompt, the same
`_format_sources`, and the same `complete()`, against `ideal_context` from the
golden set.

Reusing `_format_sources` rather than reproducing it is deliberate. The model
reads a numbered block with a header -- `[1] source=gmail | title=... |
date=2026-06-11` -- and prompt rule 2 ("sources are dated, prefer the most
recent when they disagree") has nothing to act on without it. A second copy of
that format here would be one more thing to keep in step; building Hit objects
instead leaves generate.py as the only place that knows the shape.

The judge sees the same formatted blocks. Hand it bare text and a date the model
correctly read from a header looks unsupported, which penalises the generator
for the eval's own omission.

    faithfulness      claims in the answer vs the context -- did it invent?
    answer relevancy  claims in the answer vs the question -- is it on topic?

Neither reads an expected answer, which is why the golden set has none. A claim
can be faithful and irrelevant at once: correctly lifted, and not what was
asked. The judge is OpenAI while the generator is Claude, deliberately -- a
model family grading its own output grades it generously.

Abstention is not measured here. The five missing_data questions are absent: a
refusal makes almost no claims, so faithfulness scores it trivially high and
learns nothing. That is a separate concern with its own golden file.

Usage:
    uv run python -m eval.eval_generator
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from deepeval import evaluate
from deepeval.evaluate import AsyncConfig
from deepeval.metrics import AnswerRelevancyMetric, FaithfulnessMetric
from deepeval.test_case import LLMTestCase

from atlas.config import settings
from atlas.generate import SYSTEM_PROMPT, _format_sources
from atlas.llm import complete
from atlas.store import Hit

GOLDEN = Path(__file__).parent / "faithfulness_dataset.json"
JUDGE = "gpt-4.1-mini"
THRESHOLD = 0.7


def as_hits(row: dict[str, Any]) -> list[Hit]:
    """
    Golden context as Hit objects, so that generate.py does the formatting.

    The scores are placeholders and nothing reads them: retrieval did not
    happen, so there is no ranking to record and inventing one would put a
    meaningless number in the archive.
    """
    return [
        Hit(
            score=0.0,
            rerank_score=None,
            text=text,
            doc_id=ref.split("#")[0],
            chunk_index=int(ref.split("#")[1]),
            source=meta.get("source", ""),
            title=meta.get("title", ""),
            date=meta.get("date", ""),
        )
        for text, ref, meta in zip(row["ideal_context"], row["source_chunks"], row["source_meta"])
    ]


def generate(question: str, hits: list[Hit]) -> tuple[str, int, int]:
    """The generation half of answer_question(), with retrieval removed."""
    user_prompt = f"Sources: \n\n{_format_sources(hits)}\n\nQuestion: {question}"
    response = complete(system=SYSTEM_PROMPT, user=user_prompt)
    return response.text, response.input_tokens, response.output_tokens


def archive(records: list[dict[str, Any]], hyperparameters: dict[str, Any]) -> Path:
    """
    Keep the generated answers beside the scores.

    deepeval records the score and the judge's reasoning, not the text that was
    judged. When faithfulness is low the first question is always "what did it
    actually say", and regenerating to find out costs money.
    """
    settings.results_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    out = settings.results_dir / f"generator-{stamp}.json"
    out.write_text(json.dumps(
        {"timestamp": stamp, "hyperparameters": hyperparameters, "answers": records},
        indent=2, ensure_ascii=False,
    ))
    return out


def main() -> None:
    golden = json.loads(GOLDEN.read_text())["questions"]
    print(f"scoring {len(golden)} questions on curated context (retriever not in the loop)")
    print(f"  generator {settings.generation_model}  temperature 0")
    print(f"  judge     {JUDGE}  threshold {THRESHOLD}\n")

    cases: list[LLMTestCase] = []
    records: list[dict[str, Any]] = []
    tokens_in = tokens_out = 0

    for row in golden:
        hits = as_hits(row)
        answer, t_in, t_out = generate(row["question"], hits)
        tokens_in, tokens_out = tokens_in + t_in, tokens_out + t_out

        cases.append(LLMTestCase(
            input=row["question"],
            actual_output=answer,
            # Formatted as the generator saw them, but kept apart rather than
            # joined: faithfulness attributes each claim to a source, and one
            # concatenated blob would lose which source supported what.
            #
            # `start=index` because formatting one hit at a time restarts the
            # numbering at [1], so every block claimed to be source [1] and an
            # answer citing [3] was judged against a context with no [3]. Run g1
            # was scored before this was fixed.
            retrieval_context=[
                _format_sources([hit], start=index)
                for index, hit in enumerate(hits, start=1)
            ],
        ))
        records.append({
            "id": row["id"],
            "shape": row["shape"],
            "question": row["question"],
            "answer": answer,
            "source_chunks": row["source_chunks"],
            "input_tokens": t_in,
            "output_tokens": t_out,
        })
        print(f"  {row['id']} {row['shape']:<10} {t_out:>4} out  {answer.splitlines()[0][:64]}")

    hyperparameters = {
        "golden_set": GOLDEN.name,
        "questions": len(golden),
        "generation_model": settings.generation_model,
        "temperature": 0,
        "judge_model": JUDGE,
        "threshold": THRESHOLD,
        "retriever_in_loop": False,
        "generation_tokens_in": tokens_in,
        "generation_tokens_out": tokens_out,
    }

    print(f"\ngenerated {len(cases)} answers: {tokens_in} in, {tokens_out} out. Judging...\n")

    # Same throttle as eval_retriever.py. Faithfulness decomposes every answer
    # into claims and verifies them one at a time, so judge calls outnumber
    # questions by a wide margin and the per-minute ceiling arrives sooner than
    # the question count suggests.
    evaluate(
        test_cases=cases,
        metrics=[
            FaithfulnessMetric(threshold=THRESHOLD, model=JUDGE, include_reason=True),
            AnswerRelevancyMetric(threshold=THRESHOLD, model=JUDGE, include_reason=True),
        ],
        hyperparameters=hyperparameters,
        async_config=AsyncConfig(max_concurrent=5, throttle_value=1),
    )

    print(f"\nanswers archived to {archive(records, hyperparameters)}")


if __name__ == "__main__":
    main()