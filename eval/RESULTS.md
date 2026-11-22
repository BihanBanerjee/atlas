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

---

## Current configuration

```
chunk_tokens 750 · chunk_overlap 100 · top_k 5 · embedded_text body_only
text-embedding-3-small (1536, cosine) · qdrant, 263 chunks from 256 documents
rerank BAAI/bge-reranker-base, 20 candidates -> 5
AsyncConfig(max_concurrent=5, throttle_value=1) -- required above ~25 questions,
  or the judge load exceeds a 200k TPM ceiling

45-question set: recall 0.962   precision 0.852
q01-q23 subset:  recall 0.957   precision 0.905
```

`chunk_overlap` was never isolated — only 7 documents split at 750, so its
expected effect is near zero. Untested.

---

## Limits of these numbers

- **Tuned on all 23 test questions.** No held-out set (23 is too few to split), so
  these figures are optimistic.
- **n=1 on rows 1, 3, 5a, 5b.** Rows 2, 4, 6a and 6b have n=3.
- The ±0.06 precision floor was measured on the dense configuration. With the
  reranker the spread is 0.013 — better retrieval gives the judge less to be
  uncertain about, so future deltas can be read more tightly.
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

1. **Semantic chunking** — next, with hybrid left on (compare against row 8).
2. **DBSF weighted fusion** instead of RRF — after that.
3. **Generator evaluation** — never measured. Faithfulness, answer relevancy, and
   the abstention check on the five `missing_data` questions.
