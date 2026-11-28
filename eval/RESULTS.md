# Retriever evaluation

Component-level evaluation of the retriever alone — no generator, no synthesis.
23 of 28 golden questions; the 5 `missing_data` questions are excluded because
"this is not in the corpus" cannot be attributed to retrieved chunks.

**Contextual Recall** — fraction of the ideal answer's claims supported by the
retrieved chunks. **Contextual Precision** — each retrieved chunk judged against
the ideal answer, weighted by rank. Judge: `gpt-4.1-mini` (OpenAI, deliberately a
different family from the Claude generator). Raw runs in `eval/results/*.json`.

**Noise floor:** repeating a configuration unchanged moves aggregate precision by
up to **±0.06** and recall by **±0.011** on the dense 23-question set. *Corrected
after row 8:* on the 40-question set with a reranker the spread is **±0.03** on
both metrics, not the ±0.013 I quoted earlier — that figure came from three runs
on 23 questions and did not survive the larger set. Differences smaller than
±0.03 are not results.

---

## All runs

| # | chunk | ovl | top_k | embedded | reranker | n | recall | Δ | precision | Δ | cost | time |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 512 | 0 | 5 | body | — | 1 | 0.957 | — | 0.680 | — | $0.075 | 9s |
| 2 | 750 | 100 | 5 | body | — | 3 | 0.953 | −0.004 | 0.755 | +0.075 | $0.084 | 9s |
| 3 | 1000 | 150 | 5 | body | — | 1 | 0.950 | −0.003 | 0.693 | −0.062 | $0.090 | 93s |
| 4 | 750 | 100 | 5 | title+date | — | 3 | 0.934 | −0.019 | 0.642 | −0.113 | $0.081 | 9s |
| 5a | 750 | 100 | **3** | body | — | 1 | **0.783** | **−0.170** | 0.837 | +0.082 | $0.060 | 8s |
| 5b | 750 | 100 | **8** | body | — | 1 | 0.942 | −0.011 | 0.716 | −0.039 | $0.115 | 27s |
| 6a | 750 | 100 | 5 | body | MiniLM-L-6 | 3 | 0.913 | −0.040 | 0.767 | +0.012 | $0.084 | 20s |
| 6b | **750** | **100** | **5** | **body** | **bge-base** | **3** | **0.954** | **+0.001** | **0.903** | **+0.148** | $0.084 | 23s |
| 7 | 750 | 100 | 5 | body | bge-base | 2 | 0.962 | — | 0.852 | — | $0.142 | 59s |
| 8 | 750 | 100 | 5 | body | bge-base + BM25/RRF | 2 | 0.910 | −0.052 | 0.799 | −0.053 | $0.139 | 43s |
| 9 | **semantic** | — | 5 | body | bge-base + BM25/RRF | 1 | 0.940 | +0.030 | 0.800 | +0.001 | $0.108 | 53s |
| **10** | semantic *(bge-small bounds)* | — | 5 | body | **bge-large** + BM25/RRF | 1 | 0.940 | 0.000 | **0.880** | **+0.080** | $0.111 | 56s |
| 11 | semantic *(openai bounds)* | — | 5 | body | bge-large + BM25/RRF | 1 | 0.930 | −0.010 | 0.810 | −0.070 | $0.111 | 53s |

Deltas in rows 2–4 are against row 1; rows 5–6 against row 2. Rerankers see 20
candidates and return 5.

**Rows 1–6b are the original 23-question set. Row 7 is the same configuration as
6b on an expanded 40-question set**, so its numbers are not comparable with the
rows above — the q01–q23 subset of row 7 scores **0.957 / 0.905**, reproducing 6b
and confirming nothing regressed. Row 7 is the baseline for everything that
follows.

---

## What each run showed

**1 → 2 · chunk 512 → 750, overlap 0 → 100.** Precision +0.075. Retrieval changed
on 22/23 questions despite only 9 chunks differing — the documents long enough to
split are the ones the questions ask about.

**2 → 3 · chunk 750 → 1000.** Precision −0.062. At 1000 no document splits (longest
body is 976 tokens), so the biggest documents become single diluted vectors.
*Caveat: rows 1–3 are n=1 and their spread (0.075) sits near the noise floor
(0.06) — treat the chunk-size ranking as weak evidence.*

**2 → 4 · prepend title + date to the embedded text.** Precision −0.113, the
clearest result in the table (n=3 both sides, non-overlapping ranges).
Contextual retrieval repairs context that chunking destroyed; at 256 documents →
263 chunks there is none to repair. **Reverted.**

**2 → 5a · top_k 5 → 3.** Recall −0.170 against a ±0.011 floor. Four questions went
from full recall to zero (q05, q06, q09, q12) — their answer sat at rank 3–5.
Precision gained 0.082. Bad trade: a precision loss wastes tokens, a recall loss
loses the answer.

**2 → 5b · top_k 5 → 8.** Both deltas inside the noise floor, cost +37%. Nothing
left to find above k=5. Also hit OpenAI's 200k TPM limit — measured judge load is
~115k tokens at k=3, ~208k at k=5, ~333k at k=8 — and needed temporary throttling
to complete at all.

**2 → 6a · rerank with `ms-marco-MiniLM-L-6-v2`.** Precision +0.012 (inside noise),
recall −0.040. Fixed q17's buried fact but broke q02 and q10 — net one question
worse. On q10 it dropped `drive-financial-model-2026` (which holds the answer) for
investor emails that merely *discuss* runway: MS MARCO trains on prose passages, so
the model rewards text that reads like an answer over text that contains one.
**Rejected.**

**2 → 6b · rerank with `BAAI/bge-reranker-base`.** Precision **+0.148** at 2.5× the
noise floor, recall unchanged. 278M parameters against MiniLM's 22M, trained on
more varied data, and it has neither the prose bias nor the recall loss — q10 and
q17 both pass. Precision pass rate 16/23 → 22/23. **Adopted.**

The reranker's own scores are deterministic, so all three runs retrieved identical
chunks and only the judge varied. Its precision spread was 0.013 against dense's
0.059 — when the right chunk is clearly first, the judge has less to be uncertain
about.

**7 → 8 · hybrid dense + BM25, fused with RRF.** Recall −0.052, precision −0.053,
both roughly 2× the floor. Per category, against row 7:

```
hybrid_retrieval      recall 1.000 -> 0.880    precision 0.807 -> 0.727
multi_hop                    1.000 -> 1.000              0.876 -> 0.750
semantic_boundary            1.000 -> 1.000              0.969 -> 0.889
reranking_near_dup           1.000 -> 1.000              0.935 -> 0.857
signal_lookup                0.923 -> 0.885              0.929 -> 0.899
conceptual_control           0.833 -> 0.667              0.317 -> 0.350
pii_redaction                1.000 -> 1.000              0.836 -> 0.885
```

`hybrid_retrieval` — the nine questions I wrote specifically to need lexical
matching — regressed on both metrics. The feature lost on its own ground.

Mechanism: the 20 candidates handed to the reranker are now the RRF fusion of each
arm's top 20. RRF counts rank positions and throws the scores away, so BM25's
rank-1 weighs exactly as much as dense's even when it is junk, displacing good
dense candidates out of the shortlist before the cross-encoder ever sees them.
That is why categories with no lexical component at all fell too.

Why BM25 is junk here, measured on q02. The question is "Who made the SSO promise
to Northwind, and who else saw it?" I reimplemented BM25 over the 263 chunks to
see the actual term weights:

```
term         df     IDF      in the target document?
saw           2    4.66      no   <- highest IDF, contributes 0
promise       3    4.32      no   <- contributes 0
else         11    3.13      no
sso          13    2.97      yes (x1)
who          20    2.56      no
made         22    2.46      no
northwind    22    2.46      yes (x1)
it/and/the/to      0.09-0.97 partly
```

The two most discriminating words in the question carry 8.98 of the available
weight between them and score **zero** against the document that holds the
answer — it says `saml` five times where the question says `sso` once, and BM25
has no way to know those are the same thing. Worse, `northwind` appears as a
standalone token only once: the other four occurrences are inside
`linda.marsh@northwindlogistics.com`, which tokenises to `northwindlogistics`, a
different term entirely.

Result: the target document ranks **28th of 263** (chunk 0, score 5.43) and 44th
(chunk 1, 4.55), both far outside `hybrid_prefetch = 20`. BM25 never nominated it
for fusion. What it nominated instead was `gmail-prospect-harrowgate` at rank 6,
which scores 9.29 because it contains the literal word "promise" — about an
entirely different prospect.

(Those numbers come from my own tokeniser, `[a-z0-9]+`. Qdrant's `Qdrant/bm25`
stems and drops stopwords, so the absolute scores differ. The conclusion holds:
given the surnames BM25 finds the document at rank 2, given the real question it
does not.)

So BM25 pays when the *question* carries the rare token. Here the rare tokens sit
in the documents and the questions are conversational. Fixing that is query-side
work — expansion, HyDE — not a fusion parameter.

**Not reverted yet.** Leaving it on while I test semantic chunking, so row 8 is
the baseline for `hybrid_enabled = True` runs and row 7 for dense. Not comparable
across the two.

### Correction, 23 Nov 2026 — row 8 was not a retrieval regression

Everything above this line is what I believed at the time. It is wrong about the
cause, and the mechanism I proposed is contradicted by direct measurement.

The aggregate score said hybrid made things worse. It cannot say *which stage*
made things worse, and I guessed. `eval/diagnose_arms.py` measures each arm
separately against `acceptable_sources`, on **row 8's exact index** — 263 fixed
chunks, same 40 questions:

```
arm        hit@5        rank1        MRR
dense      85%          50%          0.618
sparse     80%          52%          0.636
fused      92%          55%          0.709     <- best of the three
pipeline   85%          50%          0.629     <- after bge-base
```

**Hybrid raised hit@5 from 85% to 92%. The reranker returned it to 85%.** After
the cross-encoder, hybrid's net contribution to MRR is +0.011 against dense alone
— nothing. The gain was real and it was consumed downstream.

What this overturns, specifically: I wrote that RRF was *"displacing good dense
candidates out of the shortlist before the cross-encoder ever sees them."* It was
not. RRF's own top-5 is the best ordering of the three arms, and a document in
RRF's top 5 is necessarily inside the 20 candidates the reranker receives. Nothing
was displaced before reranking. The reranker was handed a better list and returned
a worse one.

It discards correct answers outright, not merely reorders them — five documents
that RRF had inside the top 5 are pushed out of the result set entirely:

```
q10: rank 1 -> None    q19: rank 1 -> None    q32: rank 1 -> None
q31: rank 2 -> None    q44: rank 2 -> None
```

Across all 40 questions it improves 9 and worsens 11.

**Hypothesis, not yet a result:** the reranker helps a mediocre ordering and hurts
a good one. Dense alone places the answer first 50% of the time, so at row 6b
`bge-base` had a lot to fix and gained +0.148 precision. RRF already reaches 55%,
so the reranker now overwrites a better ordering with its own. That single story
fits rows 6b, 7 and 8 together.

**What this does not establish.** These are document-level hit/rank/MRR against
qrels, not the LLM-judged contextual metrics in the table above. The two answer
different questions and the numbers are not interchangeable. The comparison
*between arms* is sound because all four are scored against the same qrels and the
same index. Whether the judged metrics follow needs one run with `hybrid_enabled =
true, rerank_enabled = false` — not yet done.

Row 8's recorded numbers stand. Its verdict does not.

---

### 8 → 9 · semantic chunking

0.940 / 0.800 against row 8's 0.910 / 0.799. Precision flat. Recall +0.030, sitting
exactly on the noise floor, from a single run — so not a result either way.

The same diagnostic on the semantic index says more than the aggregate did:

```
arm        fixed (263)   semantic (365)
dense      85%           90%
sparse     80%           82%
fused      92%           92%
pipeline   85%           88%
reranker   MRR −0.080    MRR −0.071
```

**Semantic chunking improved the dense arm by 5 points of hit@5 and the full
pipeline by 3.** It was not flat. The judged aggregate could not see it because the
reranker is absorbing changes upstream of itself — the same component that ate
hybrid's gain.

The reranker degrades the fused ordering on *both* indexes, so this is not an
artifact of chunking. It was true at row 8 and invisible there.

Caveat on the chunking itself: the first semantic index had 151 of 508 chunks below
the 60-token floor, because the floor was only enforced at seams and a document's
final remainder escaped untested. Two chunks were the single word "Marcus". Row 9
is measured after that fix — 9 below the floor, all of them whole documents shorter
than the floor.

**Row 9 is superseded and needs re-running.** It was measured on an index whose
boundaries came from `text-embedding-3-small`, and that index no longer exists.
Two ingests of an unchanged corpus produced **365 then 366 chunks**: the endpoint
does not return identical vectors for identical input at realistic batch sizes
(max|delta| 3.3e-03 over 66 windows), which moved the p95 threshold from
0.531032150 to 0.531068338 and flipped one document's boundary. Harmless for
ranking; not harmless for a cut-or-not decision at a threshold.

Boundary detection now runs on a local encoder (`BAAI/bge-small-en-v1.5`, see
`atlas/boundary.py`). Two full passes over the corpus are byte-identical, the
window pass is free, and a semantic ingest takes 7s instead of 2m20s. The current
index is **371 chunks**, median 117 tokens — within 1.4% of what the OpenAI
boundaries gave, so the seams largely agree.

The arm-level numbers below were taken on the 365/366-chunk index. The row-8
correction above is unaffected: that was measured on the fixed 263-chunk index,
which is deterministic.

---

### 9 → 10 · a stronger cross-encoder

Precision **0.800 → 0.880**, nearly 3× the noise floor and the clearest single
improvement in this table. Recall unchanged at 0.940. The only intended change
was `bge-reranker-base` → `bge-reranker-large`.

This is the end of the thread that started with row 8 reading as a regression.
Measured per arm on the same index:

```
                     hit@5   rank1    MRR
fused (RRF only)      92%     62%    0.733
+ bge-base            80%     40%    0.561     -0.172
+ bge-large           92%     60%    0.742     +0.021
```

`bge-base` was not merely reordering badly — it discarded seven correct documents
out of the top 5 entirely (q02, q10, q19, q31, q32, q43, q44), taking a 62%
rank-1 ordering down to 40%, worse than either arm alone. `bge-large` preserves
hit@5 completely.

**So every retrieval change since row 6b was working, and one component was
eating all of it.** Hybrid raised hit@5 from 85% to 92%. Semantic chunking
raised the dense arm from 85% to 90%. Neither was visible in the aggregate
because what followed them destroyed the ordering. Replace it and the
accumulated gains surface at once.

Why it helped at 6b and hurt here: a cross-encoder is correcting the ordering it
is handed. Dense alone places the answer first about 50% of the time, so at 6b
there was a great deal to fix and it gained +0.148 precision. RRF already reaches
62%, so a weak cross-encoder now overwrites a better ordering with its own worse
one. The technique was never wrong; the model was too weak for the job once
fusion had done most of it.

**Caveats.**

- **n = 1**, and it will stay n = 1. Row 7 had two runs, row 6b had three. A
  confirming run was considered and declined on cost; row 10 is accepted as the
  working baseline at a single run, and anything compared against it inherits
  that uncertainty.
- **Two things changed between 9 and 10**, not one: the reranker, and boundary
  detection moving to a local encoder. The arm diagnostic showed the boundary
  swap was retrieval-neutral (fused 92%/62%/0.733 against 92%/62%/0.736 on the
  previous index), so the gain is attributable to the reranker — but this is not
  a clean single-variable comparison.
- **Against row 7, +0.028 is inside the ±0.03 floor.** Best precision recorded on
  the 40-question set is true. Beating row 7 is not yet established. Row 9 → 10
  is.
- `bge-large` is 2.24GB against ~400MB and added ~13s per eval run.

**Still failing:** q43 recall 0.00 — the runway recency problem, unchanged by any
of this. q29 and q42 on precision.

### 10 → 11 · OpenAI boundaries, and a prediction that was wrong

One variable: `boundary_encoder`, `bge-small-en-v1.5` → `text-embedding-3-small`
with a content-hash cache. **Precision 0.880 → 0.810. Recall 0.940 → 0.930.**
Failures 8 → 11.

Reverted afterwards, which restores row 10's configuration exactly — so row 10
is the current system and there is no row 12 to measure.

I changed it because the local encoder had measured worse at document level —
dense hit@5 85% against OpenAI's 90%, MRR 0.615 against 0.656 — and because the
cache gave reproducibility without giving up those boundaries. On the restored
index `diagnose_arms` then showed the best pipeline figures yet, 95% hit@5 and
0.747 MRR, reproduced across two runs.

Every one of those numbers improved. Judged precision fell by 0.07, more than
twice the noise floor.

**Why the screen pointed the wrong way.** `hit@5` asks whether an acceptable
source is *anywhere* in the top 5. Contextual Precision scores *all five* chunks,
weighted by rank, and penalises the irrelevant ones. A configuration can find the
right document more often and simultaneously drag in more plausible near-misses
beside it. OpenAI boundaries do exactly that: better at locating the answer,
worse at keeping the window clean.

```
boundaries            judged precision   dense hit@5   pipeline hit@5
bge-small (local)              0.880          85%           92%
text-embedding-3-small         0.810          90%           95%
```

**What this costs the method, not just the run.** `diagnose_arms` caught the
reranker correctly because that effect was enormous — MRR −0.172. It failed here
because the effect was small and lives in a metric the screen does not measure.
**The document-level screen is reliable for large effects and unreliable for
small ones.** Treat it as a filter for obvious breakage, not as a predictor of
judged scores. Anything inside roughly ±0.05 of document-level MRR needs the
judged suite or it is a guess.

Reverted to `bge-small-en-v1.5`: better on the metric that counts, free,
deterministic without needing the cache. The cache code stays — `boundary_encoder`
is a real switch now, and the cache earns its place the moment OpenAI boundaries
are used again.

---

### An aside: the same defect, twice

Two `diagnose_arms` runs minutes apart on an unchanged index gave fused
92%/62%/0.733 and 92%/60%/0.720, while `dense` and `sparse` were bit-identical in
both. Only the fusion moved.

The dense *prefetch* is 20 deep. OpenAI's query embedding is not stable, which
does not disturb dense's top 5 but reorders its tail — and RRF reads ranks all
the way down. Same root cause as the chunk-boundary flip: a discrete decision
taken over near-ties, fed by a non-deterministic endpoint. Worth remembering that
~±0.013 of fused MRR is measurement noise, which is the same magnitude as
`bge-large`'s +0.021.


---

## Current configuration

```
chunk_strategy semantic · p95 cut · floor 60 · ceiling 750 · top_k 5
boundaries   BAAI/bge-small-en-v1.5, local and deterministic
index        text-embedding-3-small (1536, cosine)
             qdrant, 371 chunks from 256 documents, median 117 tokens
retrieval    hybrid dense + BM25, fused with RRF, 20 candidates per arm
rerank       BAAI/bge-reranker-large, 20 candidates -> 5
AsyncConfig(max_concurrent=5, throttle_value=1) -- required above ~25 questions,
  or the judge load exceeds a 200k TPM ceiling

40-question set: recall 0.940   precision 0.880      (row 10, n=1)
```

`chunk_overlap` was never isolated — under fixed chunking only 7 documents split
at 750, so its expected effect was near zero. It no longer applies at all under
semantic chunking. Untested and now moot.

---

## Limits of these numbers

- **Tuned on all 23 test questions.** No held-out set (23 is too few to split), so
  these figures are optimistic.
- **n=1 on rows 1, 3, 5a, 5b.** Rows 2, 4, 6a and 6b have n=3.
- The ±0.06 precision floor was measured on the dense configuration. I previously
  wrote that the reranker tightened the spread to 0.013; that figure came from
  three runs on 23 questions and did not survive the 40-question set, where it is
  **±0.03 on both metrics**. See the note at the top of this file.
- Chunk size and `top_k` are corpus-dependent; a different corpus needs the sweep
  re-run, not these values copied.

---

## Next

Eight questions fail at row 10, and the split has changed since row 8:

```
recall     q02 0.50   q12 0.00   q43 0.00
precision  q08 0.583  q10 0.50   q19 0.583  q29 0.50  q42 0.589
```

**q02** ("who made the SSO promise") is no longer the 0.00-recall case it was
through rows 1–8. It now scores recall 0.50 and **precision 1.00** — every
retrieved chunk is relevant and `gmail-northwind-renewal` lands at rank 1. The
remaining half is the other acceptable source: the 11 June commitment thread
still never reaches the candidates. So the earlier diagnosis was half right —
there was a ranking component, which the reranker upgrade fixed, and a genuine
dense retrieval miss underneath it, which nothing has fixed.

**q43** remains 0.00 recall: runway, where the golden answer is seven months as
of August 2026 and the context returns eight or nine from July documents. The
corpus holds a figure for every month and retrieval picks the wrong one.

**q10**, the other runway question, no longer fails on recall at all — it is now
a precision failure at 0.50. The recency problem is narrower than it looked.

The five precision failures all sit in the 0.50–0.59 band, which is the shape of
one or two merely-on-topic chunks ranked above a relevant one rather than
anything being missed.

1. **DBSF weighted fusion** instead of RRF — worth trying now that the stage
   after it is no longer destroying the ordering. `eval/diagnose_arms.py` costs
   ~$0.00002 and is worth running first, but read row 11 before trusting it:
   the screen is a filter for obvious breakage, not a predictor of judged
   scores, and it pointed the wrong way on a 0.07 precision move.
2. **Recency.** q43 is the last 0.00-recall question: the corpus holds a runway
   figure for every month and retrieval returns the wrong one. A date filter
   needs a payload index, which the collection does not have. Nothing tested so
   far touches this. *Confirmed again at pipeline level by f14, where the July
   investor update existed in the corpus and retrieval returned March, April and
   June instead — this is the widest-reaching open retrieval defect.*
3. **Generator evaluation** — measured, run g1 below. The abstention check on the
   five `missing_data` questions is still outstanding and is not part of it.
   Pipeline evaluation is measured too, run p1 at the end of this file.
4. **Long-form corpus tier** — 249 of 256 documents fit in one 750-token chunk and
   v0.1 already scored 0.957 recall, so there is very little headroom for any of
   this to show in. Specified separately.
5. **Message-boundary chunking.** Run g1 found the chunker splitting an email
   thread between a message's `From:` header and its body, which strands the
   attribution two chunks away from the words it belongs to. Generic change —
   structural headers become boundaries the chunker may not cross — and it is a
   retrieval change, not a generator one.

---

# Generator evaluation

Component-level evaluation of the generator alone — curated context, no
retrieval. 24 questions in `eval/faithfulness_dataset.json`, a separate set from
the 28 retriever goldens: questions written to stress near-duplicates stop being
hard once the context is perfect, so these are easy to retrieve for and
*tempting to embellish* instead. Six each of four shapes — `why`, `partial`,
`gap`, `near-miss`.

The retriever is out of the loop, which means Qdrant is too: the context is
frozen chunk text inside the JSON, so a run needs no container.

**Faithfulness** — the judge splits the answer into claims and checks each
against the context; supported over total. **Answer relevancy** — splits the
answer into claims and asks of each whether it helps answer the question. It
never sees the context. Judge: `gpt-4.1-mini`, deliberately a different family
from the Claude generator. Threshold 0.70. Answers and scores archived to
`eval/results/generator-*.json`.

The five `missing_data` questions are **not** in this set. A refusal asserts
almost nothing, so faithfulness scores it trivially high and learns nothing.
Abstention needs its own golden file and its own check.

---

## All runs

| # | generator | temp | n | questions | faithfulness | answer relevancy | cost | time |
|---|---|---|---|---|---|---|---|---|
| **g1** | `claude-haiku-4-5` | 0 | 1 | 24 | **0.94** (23/24 pass) | **0.92** (21/24 pass) | $0.088 | 42s |

Cost splits $0.027 generation (14,523 in / 2,513 out on Haiku at $1/$5 per MTok)
and $0.061 judging. The judge is the expensive half because faithfulness
decomposes every answer into claims and verifies them one at a time, so judge
calls scale with answer length, not with the question count.

No noise floor yet — g1 is a single run. Nothing here should be read as a
difference until there is a second configuration to compare it against.

By shape:

```
why         6/6    near-miss   6/6    gap   4/6    partial   4/6
```

---

## What g1 showed

Four questions failed. **Two of the four are the judge being wrong, and the
chunks prove it** — which is the main finding of the run, more than the headline
numbers are.

| id | shape | metric | score | verdict |
|---|---|---|---|---|
| f06 | gap | answer relevancy | 0.17 | judge error |
| f10 | partial | faithfulness | 0.67 | judge error |
| f13 | gap | answer relevancy | 0.67 | judge harsh, defensible |
| f24 | partial | answer relevancy | 0.50 | **real generator error** |

So the honest reading is **one genuine failure in 24**, not four. Faithfulness is
effectively 1.00; answer relevancy has one real miss.

### f06 — the generator passed the hardest question in the set and scored 0.17

The commitments log records an audit-log export and a closed onboarding session
for Northwind, and deliberately does **not** record the SAML promise — that
absence is why the document exists. The model listed exactly those two and
omitted SSO. Faithfulness 1.00.

Structure is what failed, not content. The answer is a lead-in — "committed to
Northwind Logistics:" — followed by bullets. Claim decomposition splits the
bullets off from the lead-in, so each claim reads *"Audit log export, 12-month
retention, customer-initiated"* with no entity in it, and answer relevancy never
sees the context, so there is nothing for the judge to attach them to. Hence its
reason: *"do not address Tensile's commitments to Northwind Logistics"* — the
entity was in the sentence it discarded.

**This is a measured property of answer relevancy, not a defect to fix.** The
obvious response is a prompt line telling the model to restate the subject in
every claim, and that is tuning the generator to the judge's claim extractor.
The answer was already correct and well-formed for a human reader. Recorded so
it is not chased later.

### f10 — the judge misattributed a quote, and the chunker is why

The two frozen chunks are `gmail-fernpath-term-sheet#1` and `#3`. Chunk `#1`
ends on a header block:

```
**From:** Ravi Menon <ravi@tensile.dev>
**To:** Priya Kothari <priya@fernpath.vc>
```

Chunk `#3` is the body of the *next* message — *"Pool: we can go to 10.5%. Below
that I'd be arguing with my own partnership"* — signed **Priya**. Its own
`From:` header lives in chunk `#2`, which is not in the context.

So the nearest visible sender name to the 10.5% concession is Ravi's, two chunks
upstream, and the judge took it. The generator did not: it read the `Priya`
sign-off and the "my own partnership" voice and attributed the concession to
Fernpath, which is correct and is what the dataset's own `tempts` note says the
right answer is. Dataset and generator agree; the judge dissents.

The finding here is a chunking one: **a message's attribution can end up in a
different chunk from its words.** Carried into the retriever's Next list as
item 5.

### f13 — borderline

Asked what Tom Brennan said he has *not* done, the model gave the two
admissions and added that he has led six engineers "but informally". Penalised
for including what he *has* done. That clause is a qualifier on the same
admission rather than a digression, so this reads as a harsh metric call, not a
generator defect. Left in the failure count because the call is defensible.

### f24 — the one real failure: a false refusal from a pronoun

The chunk is signed **Karin**, writing from Northwind's side: *"Two items go on
our remediation register."* "Our" is Northwind's. Both items and the explicit
*"no blocking findings for continued use this term"* are in the chunk. The model
read "our" as Tensile's, concluded the source was about the wrong company, and
refused a question it could have answered in full.

Two things worth keeping:

- It is an **over-refusal**, the opposite of the failure mode this set was built
  to catch. The prompt's instruction to refuse rather than guess is working; the
  reading that triggered it was wrong.
- **Faithfulness scored it 1.00.** A refusal asserts almost nothing, so there is
  nothing to contradict. Only relevancy caught it, and only partially. That is
  the same blind spot that keeps abstention in a separate file — and it shows
  here that the blind spot is not confined to the questions deliberately set
  aside for it.

---

## Current configuration (generator)

```
generator            claude-haiku-4-5
temperature          0
prompt               6 rules — per-claim citations, dated-source precedence,
                     arithmetic allowed / invention not, partial answers,
                     no outside knowledge, lead with the answer
context              curated, 1–2 chunks per question, frozen in the golden set
judge                gpt-4.1-mini, threshold 0.70
```

---

## Limits of these numbers

- **n=1, no noise floor.** The retriever's spread was only visible after
  repeated runs; nothing comparable is known here yet.
- **No prompt baseline.** The prompt was rewritten before this first
  measurement, so there is no number for the version that preceded it and no way
  to say what the rewrite bought.
- **The judge is a measuring instrument with its own error rate, and this run
  measured it at 2 of 24.** Both errors were caught only by reading the source
  chunks by hand. Aggregate scores on this set should not be quoted without that
  caveat, and a future failure should be read against its chunks before being
  attributed to the generator.
- **Curated context is not retrieved context.** These numbers say what the
  generator does with correct sources. They say nothing about what it does with
  the top-5 the retriever actually returns.
- **Shape counts are 6 each**, which is too few for a per-shape number to mean
  anything; the breakdown above is a description of where the failures fell, not
  a measurement of shape difficulty.
- **Abstention is unmeasured.** The five `missing_data` questions have no check
  yet, and f24 shows false refusals are a live failure mode.

---

# Pipeline evaluation

The retriever and the generator together, scored end to end. Same 24 questions
as the generator eval above and the same judge, with one substitution:

```
generator eval   retrieval_context <- ideal_context, curated in the golden file
pipeline eval    retrieval_context <- answer.hits, whatever Qdrant returned
```

That single change is the experiment. Everything else — questions, judge,
threshold, context formatting — is held fixed so the difference between the two
runs is attributable to retrieval.

**The RAG triad.** Faithfulness and answer relevancy carry over from the
generator eval. **Contextual Relevancy** is new and only exists at this level:
the judge splits the *retrieved context* into statements and asks of each
whether it is relevant to the question, scoring relevant / total. At component
level the context was hand-picked, so scoring its relevance would have been
scoring whoever picked it.

All three are reference-free — none reads `expected_answer`. Judge
`gpt-4.1-mini`, threshold 0.70. Answers and retrieved chunk refs archived to
`eval/results/pipeline-*.json`.

---

## All runs

| # | context | n | questions | contextual relevancy | faithfulness | answer relevancy | cost | time |
|---|---|---|---|---|---|---|---|---|
| g1 | curated | 1 | 24 | — | 0.94 (23/24) | 0.92 (21/24) | $0.088 | 42s |
| **p1** | **retrieved** | 1 | 24 | **0.43** (2/24) | **0.96** (23/24) | **0.92** (20/24) | $0.304 | 78s |

p1 cost splits $0.063 generation (45,720 in / 3,401 out) and $0.241 judging.
Input tokens are 3× g1's because the window is five retrieved chunks rather than
one or two curated ones, and contextual relevancy decomposes all five. The run
was estimated at $0.15–0.20 beforehand; the estimate was low by half.

Retrieval config is row 10: semantic chunking, hybrid dense+BM25 with RRF,
`bge-reranker-large` 20 → 5, `top_k` 5.

**Caveat on the g1 comparison.** g1 ran before the context-numbering fix (every
chunk was labelled `[1]`) and before the source separator changed from `--` to
`---`. The comparison is therefore not single-variable in the strict sense.

---

## What p1 showed

**The generator does not degrade on real context.** Faithfulness 0.94 → 0.96
and answer relevancy 0.92 → 0.92. The expected result was a drop: curated
context is perfect context, and retrieval is not. There is no drop. On this set
the retriever costs the generator nothing measurable, and the prompt written
against curated context transfers to retrieved context unchanged.

What that does **not** establish: these 24 questions were written to be easy to
retrieve for, deliberately, so the result is about prompt robustness rather than
about retrieval being adequate in general. The hard retrieval cases live in
`golden_dataset.json` and are scored by the retriever eval.

### Contextual relevancy 0.43 — chunk granularity, not ranking

22 of 24 fell below threshold. The two that passed were f06 and f24.

This does not contradict row 10's contextual precision of 0.880. The two
metrics have different denominators:

```
contextual precision   is this CHUNK relevant to the ideal answer, by rank
contextual relevancy   is this STATEMENT relevant to the question, all chunks
```

A correct chunk at rank 1, surrounded by its own ordinary prose, scores 1.0 on
the first and well under 0.5 on the second. Precision says the ranking is good.
Relevancy says each retrieved chunk carries more sentences than the question
needs — which is a property of what was indexed, not of what was ranked. The
retriever cannot return half a chunk.

The judge's reasons bear this out: the statements it calls irrelevant are real
body text, not artifacts. *"Provider shall process Customer Data solely to
provide the Service"*, *"encryption at rest and in transit"*, *"Audit log export
is scoped for Q3."*

**The noise is not uniform.** Median chunk size is 117 tokens, so most chunks
are small. The worst-scoring questions are the ones whose sources are long
structured documents hitting the 750-token ceiling — f22 (0.18), f13 (0.19),
f14 (0.19), f18 (0.22), f17 (0.28), f09 (0.29): the MSA, the security
questionnaire, the role scorecards. If this is ever worth attacking it is a
ceiling question, not a global chunk-size question.

**On the 8.33% pass rate.** A 0.70 threshold requires 70% of every sentence in
all five chunks to be relevant to the question, which whole-chunk retrieval over
real documents will essentially never reach. The average is the number to carry
from this metric; the pass rate is a property of the threshold.

### f14 — the one faithfulness failure is a retrieval miss

Scored 0.50. The answer opened *"The sources do not contain a July investor
update"*, cited June's 9-month runway, and noted that the 3 August leadership
sync carries July ARR of $1.04M without runway.

Checked against the archive and the corpus: **every one of those statements is
true.** The retrieved chunks were

```
gmail-all-hands-august#1            gmail-investor-update-2026-03#0
gmail-investor-update-2026-06#1     notion-leadership-notes-2026-08-03#0
gmail-investor-update-2026-04#1
```

March, April and June — no July. `gmail-investor-update-2026-07` **exists in the
corpus** and reports runway 8 months; retrieval did not return it. June's figure
really is 9 months.

So this is the recency failure from the retriever eval, appearing at pipeline
level on a question the generator set treats as easy. The generator reported its
window honestly and was marked down for it: the judge's stated reason — that the
output "incorrectly implies there is no July 2026 ARR update" — is wrong, since
the answer explicitly cites the July ARR figure from the leadership notes.

Adjusted reading: **faithfulness is effectively 1.00 on this run**, and the
finding belongs to retrieval. It is the same defect as q43 and has the same
blocker — a date filter needs a payload index the collection does not have.

### Answer relevancy — four below threshold, all the same shape

f05 (0.67), f10 (0.62), f13 (0.67), f20 (0.67). In each case the judge found the
answer correct but penalised supporting detail as off-topic: f05's note that the
tracing module is included rather than charged, f10's dilution arithmetic, f20's
build-duration specifics. f13 scored 0.67 on the same question at g1, so that
one is reproducible across context sources.

This is the claim-decomposition behaviour recorded at g1 — the metric rewards an
answer that stops at the literal question. Not fixed, deliberately: a prompt
instruction to omit context would be tuning the generator to the judge's claim
extractor.

---

## Current configuration (pipeline)

```
retrieval   row 10 — semantic chunking, hybrid dense+BM25 + RRF,
            bge-reranker-large 20 -> 5, top_k 5, collection atlas_mine_v01
generator   claude-haiku-4-5, temperature 0, the 6-rule prompt
context     retrieved, formatted with source/title/date headers, one entry per hit
judge       gpt-4.1-mini, threshold 0.70

24 questions: contextual relevancy 0.43  faithfulness 0.96  answer relevancy 0.92
```

---

## Limits of these numbers

- **n=1, no noise floor.** As with g1, nothing here is a difference until a
  second configuration exists to compare against.
- **The question set is the easy one by design.** These 24 were written to stop
  retrieval difficulty from confounding generator measurement. The absolute
  scores are therefore optimistic against the corpus's real difficulty — f14
  being the exception that got through.
- **Contextual relevancy is biased down by the source headers.** Each context
  entry begins `[n] source=… | title=… | date=…`, which the judge may count as
  statements. The headers are kept because the generator needs the date and
  because g1 was scored the same way; the bias is unmeasured. Read this metric
  relatively between runs, not as an absolute.
- **The judge erred again, on f14.** Second run in a row where hand-checking
  overturned a failure. Treat any single failure here as unadjudicated until its
  chunks have been read.
- **The archive stores chunk refs, not chunk text.** f14 was only resolvable
  because the corpus could be grepped directly. A question whose chunks had been
  re-indexed since the run would not be resolvable this way.
