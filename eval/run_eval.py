"""
Run the golden dataset against the pipeline and score it.

WHY RETRIEVAL METRICS ARE NOT COMPUTED BY RAGAS
-----------------------------------------------
RAGAS estimates context recall and precision with an LLM judge, because most
projects have no per-question document labels. This one does:
golden_dataset.json carries `acceptable_sources` for every question -- real
qrels, written by hand against the corpus.

So retrieval is scored exactly, by set arithmetic, with zero LLM calls. That's
cheaper, deterministic, and more trustworthy than paying a model to guess at
something I already know the answer to. RAGAS earns its place only on the two
metrics that genuinely need a judge: faithfulness and answer relevancy.

Scoring rules follow golden_dataset.json's `_meta.source_semantics`:
  acceptable_sources -- supplies a necessary part of the answer
  partial_sources    -- corroborates a fragment; retrieving one is NOT a recall
                        success and must NOT count as a precision failure
  expect_refusal     -- no sources exist; the correct behaviour is to decline

The judge is OpenAI while synthesis is Claude, deliberately. A model family
grading its own output scores it generously -- so the grader and the graded
should not come from the same lab.

Usage:
    uv run python eval/run_eval.py                # all 28 questions
    uv run python eval/run_eval.py --subset 5     # 5, spread across categories
"""