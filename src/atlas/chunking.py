"""
Fixed-width token windows, with optional overlap.

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

WHY tiktoken AND NOT Anthropic's token counter
----------------------------------------------
We chunk for the *embedding* model (OpenAI text-embedding-3-small), so we count
with OpenAI's tokenizer. That is the correct tool here. It is the wrong tool for
estimating Claude prompt sizes -- use Anthropic's count_tokens endpoint for that.
"""

from __future__ import annotations

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