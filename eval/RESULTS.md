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

## Method

**One variable per run.** Runs 2 and 3 moved `chunk_tokens` and `chunk_overlap`
together, which is why neither says anything about overlap on its own.

**Write the prediction down first.** Run 2 was predicted to be a no-op because it
changed only nine chunks; retrieval changed for 22 of 23 questions. That surprise
was the most useful thing in the run — chunk *count* turned out to be the wrong
predictor of impact, because the documents long enough to split are the
information-dense ones the questions ask about. A prediction on record is what
makes a surprise legible.

**The noise floor is effectively zero, and it belongs to the judge.** Six
questions with byte-identical retrieval across Runs 2 and 3 scored identically to
two decimals. So any delta here is real. This has to be re-established if the
judge model ever changes.

**Verify the change actually reached retrieval** before interpreting a delta. The
archived traces make this a two-second check:

| retrieval | score | means |
|---|---|---|
| identical | moved | judge noise — should not happen now |
| identical | same | the change was a no-op |
| changed | either | a real effect; interpret it |

**Read the biggest regression, not the mean.** Run 2 netted +0.058 while two
questions each lost 0.50. The judge's reasoning on the worst loser is where the
next hypothesis comes from.

**Sweep coarse before fine.** 512 → 750 → 1000 located a peak in three runs.
Tuning between 700 and 800 would chase differences smaller than the metric can
resolve at n=23.

### Cost per experiment

| knob | needs | cost |
|---|---|---|
| `top_k`, judge, threshold | nothing | $0.08 |
| `chunk_tokens`, `chunk_overlap`, embedded text | re-ingest | $0.085 |
| embedding model | a new collection | $0.09 |

Cheap knobs first when the expected gain is comparable.

### A caveat on these numbers

**Every decision here is made by looking at all 23 test questions.** There is no
held-out set — 23 is too few to split usefully — so with enough iterations these
scores would measure how well the configuration fits *this* golden set rather than
how well retrieval works. Two mitigations: keep the number of tuning runs small
(five to eight per component), and prefer changes that have a stated mechanism
("embed the title because subject lines carry the customer name") over changes
that merely scored well. The numbers below should be read as optimistic.

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

## Run 1 — baseline

`top_k=5 · chunk_tokens=512 · overlap=0 · embedded_text=body_only · text-embedding-3-small · judge=gpt-4.1-mini · threshold=0.70`
23 questions, `atlas_mine_v01` (272 chunks from 256 documents). $0.075, 9.1s.

| metric | average | pass rate |
|---|---|---|
| Contextual Recall | **0.96** | 22/23 |
| Contextual Precision | **0.68** | 11/23 |

**Recall is effectively solved; precision is the bottleneck.** The answer reaches
the prompt in 22 of 23 questions. What it does not do is reach the *top* of the
prompt.

### By category

| category | n | recall | precision |
|---|---|---|---|
| signal_lookup | 13 | 0.92 | **0.57** |
| hybrid_retrieval | 1 | 1.00 | 0.58 |
| reranking_near_duplicate | 3 | 1.00 | 0.75 |
| pii_redaction | 2 | 1.00 | 0.79 |
| multi_hop | 4 | 1.00 | **0.96** |

The ranking inverts what you would expect, and the reason is structural rather
than a retrieval defect. A multi-hop question needs four or five chunks, so most
of a top-5 is genuinely relevant and precision is naturally high. A
`signal_lookup` question needs a single fact, so four of the five retrieved
chunks are surplus by definition and precision is capped low however good the
retrieval is. **Contextual precision penalises single-fact questions for reasons
that have nothing to do with retrieval quality** — worth remembering before
reading 0.57 as a failure.

### The one recall failure — a buried fact, not a corpus gap

> **Corrected after Run 2.** The original diagnosis here claimed the notice-period
> fact existed only in YAML frontmatter and was never indexed. That was wrong: it
> came from grepping for the exact phrase `"notice period"`, which only the
> frontmatter uses. The bodies state it in ordinary prose and **are** indexed. The
> corrected analysis follows.

q17 asks for the notice-period difference between the two Head of Engineering
candidates. Recall scored 0.00 — yet all four of its sources carry the fact in
their body text:

```
comp-discussion-vasquez   "My notice is eight weeks, which I know is longer than ideal."
comp-discussion-brennan   "Notice is four weeks."
resume-elena-vasquez      "- Available with eight weeks notice"
resume-tom-brennan        "- Available with four weeks notice"
```

None were retrieved. What came back instead was `notion-hiring-pipeline`,
`drive-compensation-benchmarking`, `gmail-recruiter-outreach` — documents about
hiring and compensation in general.

So this is a **genuine retrieval failure of the buried-fact kind**. In a
500-token email about salary, equity and timing, one sentence mentions notice.
The chunk embedding averages over everything in the chunk, and a single line gets
swamped by the surrounding topic. The retrieved documents are *more* about
"Head of Engineering candidates" as a subject; the ones holding the answer are
about compensation, and only glance at notice in passing.

This is the strongest argument in the run for smaller chunks — a shorter window
would give that sentence a vector less diluted by its neighbours.

### The real ranking problem

Reading the judge's reasoning across the precision failures, one pattern repeats:

| question | relevant chunk at rank | precision |
|---|---|---|
| q05 | 5 | 0.20 |
| q09 | 4 | 0.25 |
| q06 | 3 | 0.33 |
| q01 | 3 and 4 | 0.42 |

The correct chunks are retrieved and then ranked below noise. This is not a
`top_k` problem — lowering k to 3 would raise precision while dropping the answer
entirely for q05 and q09, trading the strong metric for the weak one.

**Most likely cause:** subject lines and titles are not embedded. `ingest.py`
stores `title`, `date` and `source` in the payload but passes only the body to
the embedder. q05 asks when Northwind's contract is up for renewal, and
`drive-northwind-msa` — a document titled Master Services Agreement containing
"Effective Date: 30 September 2025" — ranked fifth.

### Next

1. Add chunk overlap, so a fact split across a boundary survives whole in one
   chunk, and raise the window to 750.
2. Later: prepend title/subject and date to the chunk text before embedding.
   `ingest.py` stores them in the payload but passes only the body to the
   embedder, so a subject line contributes nothing to matching.

---

## Run 2 — chunk window 750, overlap 100

`top_k=5 · chunk_tokens=750 · overlap=100 · embedded_text=body_only · text-embedding-3-small · judge=gpt-4.1-mini · threshold=0.70`
23 questions, `atlas_mine_v01` (263 chunks, down from 272). $0.084, 8.4s.

| metric | Run 1 | Run 2 | delta |
|---|---|---|---|
| Contextual Recall | 0.957 | **0.946** | −0.011 |
| Contextual Precision | 0.680 | **0.738** | **+0.058** |
| precision pass rate | 11/23 | 15/23 | +4 |

### The change was far larger than the chunk count suggested

Raising the window from 512 to 750 merges nine chunks — 272 down to 263, with
seven documents still splitting instead of sixteen. On that basis this looked
like it would barely register.

**Retrieval changed for 22 of the 23 questions.** Counting chunks was the wrong
way to predict the effect. The sixteen documents long enough to split are the
information-dense ones — the MSA, the financial model, the board decks, the pitch
decks, the compensation threads — which is to say precisely the documents the
golden questions ask about. Re-chunking them changes their embeddings, which
changes their similarity scores, which reshuffles the top five almost everywhere.

A useful check came out of this: comparing the retrieval traces between runs, **no
question had identical retrieval with a different score**. So the movement is a
real consequence of the configuration, not judge variance.

### But the result is directional, not proven
<!-- superseded by Run 3: the judge turned out to be deterministic, so this
     movement is real. Kept for the record. -->


The per-question movement is much larger than the average suggests:

| gained | | lost | |
|---|---|---|---|
| q10 | +0.50 | q15 | −0.50 |
| q22 | +0.50 | q23 | −0.50 |
| q14 | +0.50 | q17 | −0.30 |
| q11 | +0.42 | q12 | −0.25 |
| q16 | +0.42 | q07 | −0.17 |

Five questions gained around 0.45 and five lost around 0.35, netting +0.058. With
one run per configuration and swings an order of magnitude larger than the
effect, this is a direction rather than a measurement. A repeat run at the same
settings would separate configuration effect from judge noise — worth doing
before treating 0.74 as the new baseline.

### Recall slipped, and it is q14

q14 (pitch deck v3 vs v4) fell from 1.00 to 0.75 — one of its claims dropped out
of the retrieved set. This is the cost side of larger chunks: `drive-pitch-deck-v3`
is now a single 600-token chunk rather than two, so it competes for one slot
instead of two, and a claim that used to arrive in the second chunk no longer
arrives at all.

### q17 half-moved

`drive-resume-elena-vasquez` now appears at rank 5, so the judge can see Elena's
eight weeks. Tom's four weeks is still missing, and the question needs both, so
recall stays 0.00. Progress that the metric cannot express — worth noting before
concluding nothing changed.

### Next

1. Push the window further, to 1000, and see whether precision keeps climbing.
2. Embed title and date with the body.

---

## Run 3 — chunk window 1000, overlap 150

`top_k=5 · chunk_tokens=1000 · overlap=150 · embedded_text=body_only · text-embedding-3-small · judge=gpt-4.1-mini · threshold=0.70`
23 questions, 256 chunks. $0.090, **93.2s**.

| | 512 / 0 | 750 / 100 | 1000 / 150 |
|---|---|---|---|
| chunks | 272 | 263 | 256 |
| documents that split | 16 | 7 | **0** |
| Contextual Recall | 0.957 | 0.946 | 0.950 |
| Contextual Precision | 0.680 | **0.738** | 0.693 |
| eval duration | 9.1s | 8.4s | 93.2s |

**750 is a real optimum, and precision falls either side of it.**

### The judge is deterministic — which settles the earlier doubt

Six questions had byte-identical retrieval across Runs 2 and 3. All six scored
identically, to two decimals:

```
q08 0.75→0.75   q09 0.25→0.25   q12 0.25→0.25
q15 0.50→0.50   q17 0.70→0.70   q18 1.00→1.00
```

Same input, same score, six for six. So judge variance is not what moves these
numbers — every difference between runs is caused by retrieval actually changing.
That retroactively confirms Run 2's +0.058 was real, and removes the need for a
repeat run to size the noise.

### Why 1000 is worse

At a 1000-token window **no document splits** — the longest body in the corpus is
976 tokens. So the largest documents (the MSA, the financial model, the board
decks) become single ~900-token vectors that average over many topics at once.
They match weakly on everything and outrank tighter chunks that are actually
*about* the thing being asked. At 750 those same documents split into halves with
a subject each.

The tradeoff in one line: **larger chunks preserve context but dilute the vector.**

### Latency is a cost of chunk size too

9.1s → 8.4s → 93.2s. Not retrieval — the judge. Contextual Precision reads every
retrieved chunk, so a question now ships ~4,500 tokens instead of ~2,000, and 23
questions in parallel hit rate limits and back off. An 11× slowdown for a worse
score.

### Next

1. **Revert to 750 / 100** — the best configuration measured.
2. Try a **smaller window (256)** for the other end of the curve. Both recall
   failures so far — q17's buried notice period, q14's dropped claim — suggest
   large chunks bury single facts. 95 documents split at 256.
3. Embed title and date with the body.

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
