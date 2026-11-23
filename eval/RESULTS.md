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
| **10** | semantic | — | 5 | body | **bge-large** + BM25/RRF | 1 | 0.940 | 0.000 | **0.880** | **+0.080** | $0.111 | 56s |

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

- **n = 1.** Row 7 had two runs, row 6b had three.
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

One question still fails: **q02** ("who made the SSO promise"), recall 0.00 across
every configuration. The judge's reason is that the retrieval context holds only
July–August emails — the 11 June commitment thread never enters the 20 candidates,
so the reranker cannot promote it. That is a dense retrieval miss, not a ranking
one.

Hybrid search was the obvious candidate for it and it did not help — see row 8
for why (the question carries no rare token; the document does).

Two questions now fail on **recency** rather than ranking: q10 and q43 both ask
about runway, the golden answer says seven months as of August 2026, and the
retrieved context says eight and nine from July documents. Retrieval finds the
right neighbourhood and the wrong month. Nothing I have tested so far addresses
this.

1. **Repeat row 10.** n=1 on the headline number. A second run settles whether
   0.880 holds and whether it genuinely clears row 7's 0.852.
2. **DBSF weighted fusion** instead of RRF — worth trying now that the stage
   after it is no longer destroying the ordering.
3. **Recency.** q43 and q10 ask about runway; the corpus holds a figure for every
   month and retrieval returns the wrong one. A date filter needs a payload index,
   which the collection does not have. Nothing tested so far touches this.
4. **Generator evaluation** — never measured. Faithfulness, answer relevancy, and
   the abstention check on the five `missing_data` questions.
5. **Long-form corpus tier** — 249 of 256 documents fit in one 750-token chunk and
   v0.1 already scored 0.957 recall, so there is very little headroom for any of
   this to show in. Specified separately.
