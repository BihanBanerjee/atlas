"""
Two splitters: fixed-width token windows, and semantic (topic-boundary) chunks.

`settings.chunk_strategy` picks one. Both stay live because a chunking change is
only readable against the other -- the index has to be rebuilt either way, and a
result is meaningless without the baseline it is being compared to.

FIXED: fixed-width token windows, with optional overlap.

The splitter has no regard for sentences, headings, or table boundaries. It
counts tokens and cuts, so on a long document it will routinely:

  - cut an email thread mid-sentence
  - separate a markdown table from the header row that gives it meaning
  - split "ARR: $940,000" away from the "June 2026" line that dates it

WHAT OVERLAP DOES AND DOES NOT FIX
----------------------------------
With `chunk_overlap = n`, each window repeats the last n tokens of the previous
one, so a fact straddling a boundary appears whole in the second chunk even
though the first cut it in half. That is the only problem overlap solves.

It does not make the splitter structure-aware, and it is not free: overlapping
text is embedded and stored more than once, so the index grows and near-duplicate
chunks compete for the same top-k slots. On a corpus where most documents are
shorter than one window, overlap changes nothing at all -- it only ever applies
to documents long enough to split.

SEMANTIC: cut where the meaning changes
---------------------------------------
Embed each sentence in the context of its neighbours, measure cosine distance
between consecutive sentences, and cut where that distance spikes. A spike means
the text moved to a new subject, which is a better place to cut than "750 tokens
have elapsed".

The cost is a second embedding pass at ingest -- every sentence, not every chunk
-- and a dependency from this module onto `embeddings`, which the fixed splitter
does not have.

WHAT THIS CORPUS SUGGESTS BEFORE ANY MEASUREMENT
------------------------------------------------
Semantic chunking is built for long documents. Measured here: 256 bodies, median
124 tokens, p90 410, and only 7 over the 750-token window. 249 of 256 documents
are already stored whole, so there is no bad cut to repair -- splitting can only
make the units smaller. At a fixed top_k that means less text reaching the prompt,
which row 5a already measured as a recall collapse (top_k 5->3 cost -0.170).

So the expectation is recall down, precision possibly up as an artifact of
granularity rather than better retrieval. Written down before running it, because
a prediction made afterwards is worthless. See eval/RESULTS.md for what happened.

WHY tiktoken AND NOT Anthropic's token counter
----------------------------------------------
We chunk for the *embedding* model (OpenAI text-embedding-3-small), so we count
with OpenAI's tokenizer. That is the correct tool here. It is the wrong tool for
estimating Claude prompt sizes -- use Anthropic's count_tokens endpoint for that.
"""

from __future__ import annotations

import re

import numpy as np
import tiktoken

from atlas.config import settings

# Loading an encoding is not free, so doing it at once at import than per call.
_encoder = tiktoken.get_encoding(settings.tokenizer_encoding)


def count_tokens(text: str) -> int:
    return len(_encoder.encode(text))


def chunk_text(
    text: str,
    chunk_tokens: int | None = None,
    chunk_overlap: int | None = None,
) -> list[str]:
    """
    Split text into token windows of `chunk_tokens`, each repeating the previous
    window's last `chunk_overlap` tokens.

    The window is the slice size; the *step* is what advances. With no overlap the
    two are equal and the windows tile the text exactly. With overlap the step is
    smaller, so the windows slide rather than tile.
    """
    size = chunk_tokens if chunk_tokens is not None else settings.chunk_tokens
    overlap = chunk_overlap if chunk_overlap is not None else settings.chunk_overlap

    step = size - overlap
    if step <= 0:
        # An overlap at or above the window size means the step is zero or
        # negative: the loop would never advance past the first window.
        raise ValueError(
            f"chunk_overlap ({overlap}) must be smaller than chunk_tokens ({size})"
        )

    tokens = _encoder.encode(text)
    if not tokens:
        return []

    chunks = []
    for start in range(0, len(tokens), step):
        window = tokens[start : start + size]
        chunks.append(_encoder.decode(window))

        # Stop as soon as a window reaches the end. Without this, a step smaller
        # than the window keeps producing trailing chunks whose content is almost
        # entirely contained in the one before -- near-duplicates that cost an
        # embedding call each and then compete for retrieval slots.
        if start + size >= len(tokens):
            break

    return chunks


# A sentence ends at .!? followed by whitespace, or at a blank line. Deliberately
# crude: the corpus is markdown email and notes, where a real sentence tokenizer
# (nltk, spacy) would be a heavy dependency to resolve "Inc." and "e.g.". The
# failure mode of getting a boundary wrong here is a slightly misplaced cut, not
# a wrong answer -- the sentences are re-joined into chunks either way.
_SENTENCE_BREAK = re.compile(r"(?<=[.!?])\s+|\n{2,}")


def split_sentences(text: str) -> list[str]:
    """Split text into sentence-ish units, dropping empties."""
    return [part.strip() for part in _SENTENCE_BREAK.split(text) if part.strip()]


def _window(sentences: list[str], index: int) -> str:
    """
    Sentence `index` joined with its immediate neighbours.

    Embedding a sentence alone makes short ones ("Thanks, Marcus.") land in
    whatever corner of the space short pleasantries occupy, and every comparison
    against them reads as a topic change. Judging each sentence in the context it
    appears in measures whether the *passage* moved, which is the thing we want.
    """
    start = max(0, index - 1)
    return " ".join(sentences[start: index + 2])


def semantic_chunk_text(text: str) -> list[str]:
    """
    Split text where adjacent sentences stop being about the same thing.

    Returns chunks of at least `semantic_min_tokens` (except a final short
    remainder, and except a document that is shorter than the floor to begin
    with) and at most `semantic_max_tokens`.
    """
    sentences = split_sentences(text)
    if len(sentences) < 2:
        # Nothing to compare. A one-sentence document is its own chunk.
        return [text.strip()] if text.strip() else []

    # Imported here, not at module scope: the fixed splitter must not pay for an
    # OpenAI client it never uses, and importing at call time keeps `chunking`
    # cheap to import for anything that only wants count_tokens().
    from atlas.embeddings import embed_texts

    vectors = np.array(embed_texts([_window(sentences, i) for i in range(len(sentences))]))

    # Cosine distance between each consecutive pair. text-embedding-3-small
    # returns unit-norm vectors, but normalising explicitly costs nothing and
    # means this does not silently break on a model that does not.
    norms = vectors / np.linalg.norm(vectors, axis=1, keepdims=True)
    similarities = np.sum(norms[:-1] * norms[1:], axis=1)
    distances = 1.0 - similarities

    # The threshold is a percentile of *this document's* distances, so it adapts
    # to how varied the document already is. np.percentile on a single-element
    # array returns that element, which yields no cut -- correct for a two-
    # sentence document.
    threshold = np.percentile(distances, settings.semantic_percentile)

    # distances[i] is the seam between sentence i and i+1, so a cut there means
    # sentence i+1 starts a new chunk.
    seams = {i + 1 for i, distance in enumerate(distances) if distance > threshold}

    chunks: list[str] = []
    current: list[str] = []

    for index, sentence in enumerate(sentences):
        candidate = current + [sentence]
        candidate_tokens = count_tokens(" ".join(candidate))

        # The ceiling wins over everything: an over-long chunk is a correctness
        # problem (it can exceed the embedding model's input limit), while an
        # ill-placed cut is only a quality one.
        if current and candidate_tokens > settings.semantic_max_tokens:
            chunks.append(" ".join(current))
            current = [sentence]
            continue

        # A seam only cuts if what we have already is worth keeping. Below the
        # floor we carry on through the seam rather than emit a fragment.
        if (
            index in seams
            and current
            and count_tokens(" ".join(current)) >= settings.semantic_min_tokens
        ):
            chunks.append(" ".join(current))
            current = [sentence]
            continue

        current = candidate


    if current:
        chunks.append(" ".join(current))

    return chunks
