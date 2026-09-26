# Evaluation results

A log of every evaluation run: what the configuration was, what it scored, and
what I changed next. The raw DeepEval output for each run is archived to
`eval/results/*.json` (gitignored — it is ~265 KB per run and unreadable in a
diff). This file is the part worth reading.

## How to read this

Evaluation happens at three levels, worked in order. A level is only meaningful
once the one below it has a number:

1. **Component** — the retriever alone, then the generator alone
2. **Pipeline** — both joined, scored on the RAG Triad
3. **Application** — correctness, completeness, style, cost

Only the retriever is being measured so far.

### Retriever metrics

- **Contextual Recall** — the ideal answer is broken into claims; the score is the
  fraction supported by the retrieved chunks. Low recall means the answer was
  never in the prompt, and nothing downstream can fix it.
- **Contextual Precision** — each retrieved chunk is judged against the ideal
  answer, **weighted by rank**. Two useful chunks at positions 1–2 score higher
  than the same two at positions 4–5.

23 of 28 golden questions are scored. The five `missing_data` questions are
excluded here — their ideal answer is "this is not in the corpus", which cannot
be attributed to retrieved chunks. They return at the generator stage, measured
with an abstention check.

Judge model is OpenAI while the system's generator is Claude, deliberately: a
model family grading its own output scores it generously.

---

## Runs

<!--
Template — copy for each run.

## Run N — <one-line description of what changed>

`top_k= · chunk_tokens= · overlap= · embedded_text= · embedding_model= · judge=`
Measured in <repo> against <collection> (<n> points).

| metric | score | vs previous |
|---|---|---|
| Contextual Recall | | |
| Contextual Precision | | |

**Weakest categories:**

**What I think is happening:**

**What I changed next, and why:**
-->

_No runs yet._

---

## Configuration reference

Values live in `.env` and are read through `src/atlas/config.py`. Every run
records them automatically in the archived JSON, so a score can always be traced
back to the configuration that produced it.

| knob | changing it requires |
|---|---|
| `TOP_K` | nothing — next run picks it up |
| `CHUNK_TOKENS` | a full re-ingest |
| `EMBEDDING_MODEL` | a full re-ingest |
| judge model / threshold | editing the constants in `eval/eval_retriever.py` |

Changing the judge mid-experiment invalidates comparison with earlier runs. If it
changes, say so in the run entry.
