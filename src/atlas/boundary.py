"""
The encoder behind semantic chunking's boundary detection.

Separate from `embeddings.py`, which talks to OpenAI and produces the vectors
that go into Qdrant. These two jobs look alike and are not:

  embeddings.py   one vector per chunk, stored, compared against query vectors
                  for months afterwards. Quality is what matters.
  boundary.py     throwaway vectors, used once, only to ask "did the topic move
                  between these two adjacent windows". Only *relative* distance
                  matters, and nothing is stored.

Why this is local
-----------------
Chunking takes a threshold off these numbers -- `np.percentile(distances, 95)`
-- and then makes a binary cut-or-not decision at it. That is far more sensitive
to small perturbations than ranking is.

The OpenAI endpoint does not return identical vectors for identical input. A
2-item batch does; a realistic 66-window document gave max|delta| = 3.3e-03
between two calls, which moved the computed p95 threshold from 0.531032150 to
0.531068338. Enough to flip a distance sitting on the cutoff: two ingests of an
unchanged corpus produced 365 and then 366 chunks.

A local model with fixed weights, in eval mode under no_grad on the same device,
returns the same vectors every time. The corpus is reproducible; now the index
built from it is too.

Two things follow for free. The window pass was roughly 75% of a semantic
ingest's embedding cost, and it is now nothing. And it was one HTTP round trip
per document -- 256 sequential calls, about 2m20s -- which is now a local batch.

What this does not change
-------------------------
Nothing in `semantic_chunk_text`'s mathematics. Windows, unit normalisation,
cosine distance, the percentile, the fence-post, the assembly loop: all
identical. Only the source of the vectors moved. It does change *where* chunks
split, because a different model produces a different distance distribution and
therefore a different threshold -- so the index must be rebuilt and anything
measured on the old one re-measured.
"""

from __future__ import annotations

import numpy as np

from atlas.config import settings

# Loaded on first use and kept. A few hundred MB and a second or two to load, and
# importing this module must stay cheap -- `chunking` imports it lazily so that
# the fixed splitter never pays for it at all.
_model = None


def _get_model():
    global _model
    if _model is None:
        # Imported here rather than at module scope so that importing `atlas`
        # does not drag torch into a process that is only going to count tokens.
        from sentence_transformers import SentenceTransformer

        _model = SentenceTransformer(settings.boundary_encoder)
    return _model


def embed_windows(windows: list[str]) -> np.ndarray:
    """
    Embed context windows for boundary detection. Shape (len(windows), dim).

    Returned unnormalised. `semantic_chunk_text` divides by the norm itself, and
    keeping that step visible there is the point -- it is where the cosine
    similarity becomes a plain dot product.
    """
    if not windows:
        return np.empty((0, 0))
    return _get_model().encode(windows, convert_to_numpy=True, show_progress_bar=False)
