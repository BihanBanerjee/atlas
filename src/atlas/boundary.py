"""
The encoder behind semantic chunking's boundary detection, with a cache.

Separate from `embeddings.py`, which produces the vectors that go into Qdrant.
These two jobs look alike and are not:

  embeddings.py   one vector per chunk, stored, compared against query vectors
                  for months afterwards. Quality is what matters.
  boundary.py     throwaway vectors, used once, only to ask "did the topic move
                  between these two adjacent windows". Only *relative* distance
                  matters, and nothing is stored in the index.

Why there is a cache
--------------------
Chunking takes a threshold off these numbers -- `np.percentile(distances, 95)` --
and then makes a binary cut-or-not decision at it. That is far more sensitive to
small perturbations than ranking is.

The OpenAI endpoint does not return identical vectors for identical input. A
2-item batch does; a realistic 66-window document gave max|delta| = 3.3e-03
between two calls, which moved the computed p95 threshold from 0.531032150 to
0.531068338. Enough to flip a distance sitting on the cutoff: two ingests of an
unchanged corpus produced 365 and then 366 chunks.

A local encoder fixes that by having fixed weights, and `bge-small-en-v1.5` was
tried. It is deterministic and free, but it measured worse: on the dense arm,
hit@5 fell 90% -> 85% and MRR 0.656 -> 0.615 against the same corpus chunked
with OpenAI boundaries. The fused arm was unchanged at 92%, so the pipeline may
wash it out, but there was no quality argument for the swap.

Caching gets the determinism without giving up the boundaries. An embedding is
requested once per distinct (model, text) pair and reused forever after, so a
re-ingest of an unchanged corpus reads every vector back byte-identical and
produces byte-identical chunks.

What this does and does not guarantee
-------------------------------------
Reproducible *given the cache*. A warm cache makes re-ingestion exactly
repeatable, which is what the corpus determinism rule in
`scripts/generate_noise.py` is really asking for. A cold cache on another
machine re-requests the vectors and may land a boundary differently -- weaker
than a local model's guarantee, and the reason the cache file is worth keeping
rather than treating as scratch.

The cache is keyed on (model, text), so changing `boundary_encoder` or editing a
document simply misses and re-embeds. There is no invalidation to get wrong.
"""

from __future__ import annotations

import hashlib
import sqlite3

import numpy as np

from atlas.config import settings

# Sentinel meaning "use the same OpenAI model the index is built with". Anything
# else is treated as a sentence-transformers model name and run locally.
OPENAI = "openai"

_model = None
_conn: sqlite3.Connection | None = None


def _get_model():
    global _model
    if _model is None:
        # Imported here rather than at module scope so that importing `atlas`
        # does not drag torch into a process that is only going to count tokens.
        from sentence_transformers import SentenceTransformer

        _model = SentenceTransformer(settings.boundary_encoder)
    return _model


def _db() -> sqlite3.Connection:
    global _conn
    if _conn is None:
        settings.boundary_cache_path.parent.mkdir(parents=True, exist_ok=True)
        _conn = sqlite3.connect(settings.boundary_cache_path)
        _conn.execute(
            "CREATE TABLE IF NOT EXISTS vectors ("
            "  key TEXT PRIMARY KEY,"
            "  dim INTEGER NOT NULL,"
            "  vec BLOB NOT NULL"
            ")"
        )
        _conn.commit()
    return _conn


def _key(model: str, text: str) -> str:
    # The model goes in the key so that switching encoders misses rather than
    # silently returning vectors from the wrong space.
    digest = hashlib.sha256(f"{model}\x00{text}".encode()).hexdigest()
    return digest


def _embed_uncached(model: str, texts: list[str]) -> list[list[float]]:
    if model == OPENAI:
        # Imported at call time: a cached run must not need an OpenAI client.
        from atlas.embeddings import embed_texts

        return embed_texts(texts)
    return [row.tolist() for row in _get_model().encode(texts, convert_to_numpy=True)]


def embed_windows(windows: list[str]) -> np.ndarray:
    """
    Embed context windows for boundary detection. Shape (len(windows), dim).

    Returned unnormalised. `semantic_chunk_text` divides by the norm itself, and
    keeping that step visible there is the point -- it is where the cosine
    similarity becomes a plain dot product.
    """
    if not windows:
        return np.empty((0, 0))

    model = settings.boundary_encoder

    if not settings.boundary_cache:
        return np.array(_embed_uncached(model, windows), dtype=np.float32)

    db = _db()
    keys = [_key(model, w) for w in windows]

    # One lookup for the whole batch rather than one per window.
    found: dict[str, np.ndarray] = {}
    for start in range(0, len(keys), 500):
        batch = keys[start : start + 500]
        placeholders = ",".join("?" * len(batch))
        for key, dim, blob in db.execute(
            f"SELECT key, dim, vec FROM vectors WHERE key IN ({placeholders})", batch
        ):
            found[key] = np.frombuffer(blob, dtype=np.float32, count=dim)

    missing = [(i, w) for i, (w, k) in enumerate(zip(windows, keys)) if k not in found]
    if missing:
        fresh = _embed_uncached(model, [w for _, w in missing])
        rows = []
        for (i, _), vector in zip(missing, fresh):
            array = np.asarray(vector, dtype=np.float32)
            found[keys[i]] = array
            rows.append((keys[i], len(array), array.tobytes()))
        db.executemany("INSERT OR REPLACE INTO vectors VALUES (?, ?, ?)", rows)
        db.commit()

    return np.vstack([found[k] for k in keys])
