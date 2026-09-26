# Retriever evaluation

Component-level evaluation of the retriever alone — no generator, no synthesis.
23 of 28 golden questions; the 5 `missing_data` questions are excluded because
"this is not in the corpus" cannot be attributed to retrieved chunks.

**Contextual Recall** — fraction of the ideal answer's claims supported by the
retrieved chunks. **Contextual Precision** — each retrieved chunk judged against
the ideal answer, weighted by rank. Judge: `gpt-4.1-mini` (OpenAI, deliberately a
different family from the Claude generator). Raw runs in `eval/results/*.json`.

**Noise floor:** repeating a configuration unchanged moves aggregate precision by
up to **±0.06** and recall by **±0.011**. Differences smaller than that are not
results.

---

## All runs

| # | chunk | overlap | top_k | embedded | n | recall | Δ | precision | Δ | cost | time |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 512 | 0 | 5 | body | 1 | 0.957 | — | 0.680 | — | $0.075 | 9s |
| 2 | **750** | **100** | 5 | body | 3 | 0.953 | −0.004 | **0.755** | **+0.075** | $0.084 | 9s |
| 3 | 1000 | 150 | 5 | body | 1 | 0.950 | −0.003 | 0.693 | −0.062 | $0.090 | 93s |
| 4 | 750 | 100 | 5 | title+date | 3 | 0.934 | −0.019 | 0.642 | −0.113 | $0.081 | 9s |
| 5a | 750 | 100 | **3** | body | 1 | **0.783** | **−0.170** | **0.837** | **+0.082** | $0.060 | 8s |
| 5b | 750 | 100 | **8** | body | 1 | 0.942 | −0.011 | 0.716 | −0.039 | $0.115 | 27s |

Deltas in rows 2–4 are against row 1; rows 5a/5b against row 2. **Row 2 is the
kept configuration.**

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

---

## Current configuration

```
chunk_tokens 750 · chunk_overlap 100 · top_k 5 · embedded_text body_only
text-embedding-3-small (1536, cosine) · qdrant, 263 chunks from 256 documents

recall 0.953   precision 0.755
```

`chunk_overlap` was never isolated — only 7 documents split at 750, so its
expected effect is near zero. Untested.

---

## Limits of these numbers

- **Tuned on all 23 test questions.** No held-out set (23 is too few to split), so
  these figures are optimistic.
- **n=1 on rows 1, 3, 5a, 5b.** Only rows 2 and 4 have repeats.
- Chunk size and `top_k` are corpus-dependent; a different corpus needs the sweep
  re-run, not these values copied.

---

## Next

Tuning is exhausted — every parameter that needs no new capability has been
swept. Every remaining precision failure reads *"the relevant node is at rank 3"*,
which is a ranking problem no parameter addresses.

1. **Hybrid search (BM25 + dense)** — dense embeddings blur exact strings; sparse
   retrieval matches them literally.
2. **Reranking (cross-encoder)** — a bi-encoder never sees query and document
   together; a cross-encoder does.
