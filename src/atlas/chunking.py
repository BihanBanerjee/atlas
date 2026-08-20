"""
Chunking: fixed-width token windows.

Cuts text every N tokens without looking at what it's cutting through. The
boundary lands wherever the count runs out -- mid-sentence, mid-table, doesn't
matter. Things I've watched it do to the corpus:

  - cut an email thread in the middle of a sentence
  - separate a markdown table from the header row that gives its columns meaning
  - split "ARR: $940,000" from the "June 2026" line that dates it

Whether that actually hurts retrieval is a measurement question, not something
to guess at. Keeping it simple for now so there's a number to compare against
before changing anything.

On the tokenizer choice
-----------------------
Counting with tiktoken because these chunks feed OpenAI's embedding model, and
cl100k_base is the encoding it uses. Same text under a different tokenizer gives
a different count -- so "512 tokens" only means anything if it's 512 by the same
rules the model reads with.

Wrong tool for measuring Claude prompt sizes, though. Anthropic has its own
count_tokens endpoint for that.
"""

from __future__ import annotations

import tiktoken

from atlas.config import settings

# Loading an encoding is not free, so doing it at once at import than per call.
_encoder = tiktoken.get_encoding(settings.tokenizer_encoding)


def count_tokens(text: str) -> int:
    return len(_encoder.encode(text))


def chunk_text(text: str, chunk_tokens: int | None = None) -> list[str]:
    """
        Split text into consecutive fixed-size token windows.

        No overlap -- chunk N ends exactly where chunk N+1 begins. Some chunkers
        repeat a bit of text across the boundary so a split sentence still shows up
        whole somewhere. Not doing that yet; want to see how the plain version
        scores before adding anything.
    """

    size = chunk_tokens or settings.chunk_tokens

    tokens = _encoder.encode(text) # tokens is a list of integers. (Tokenized sub-words kind of thingies are stored in numerical form here not in there pure string structure)
    if not tokens:
        return[]

    chunks = [] # an array of strings
    for start in range(0, len(tokens), size):
        window = tokens[start: start+size] # comprises of 512 tokens.
        chunks.append(_encoder.decode(window))
    return chunks