"""
Turning text into vectors.

This is the retrieval side of things -- text goes in, a list of floats comes
out, and similar text lands near other similar text in that space. Qdrant does
the searching; this file just produces the numbers it searches over.

Worth noting: Anthropic doesn't sell an embeddings endpoint. There's no
client.embeddings.create() in their SDK. So even though Claude handles the
answering, the vector side has to come from somewhere else -- OpenAI here.
Two providers for one pipeline, doing two unrelated jobs.

Keeping every embedding call in this one file. Right now that buys nothing,
but the query path and the indexing path both need embeddings, and if they
ever drift onto different models the similarity scores stop meaning anything.
Easier to keep them honest from one place.
"""

from __future__ import annotations

from openai import OpenAI

from atlas.config import settings

_client = OpenAI(api_key=settings.openai_api_key)

# The API accepts far more per request, but small batches keep memory flat and 
# make a failure cheap to retry. 48 documents is not a throughput problem.

_BATCH_SIZE = 100


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a list of texts, preserving input order."""

    if not texts:
        return []

    vectors: list[list[float]] = []

    for start in range(0, len(texts), _BATCH_SIZE):
        batch = texts[start : start + _BATCH_SIZE]
        response = _client.embeddings.create(
            model=settings.embedding_model,
            input=batch,
        )
        # The API guarantees response order matches input order, but it also
        # returns an explicit index -- sort on it rather than trusting position.
        ordered = sorted(response.data, key=lambda item: item.index)
        vectors.extend(item.embedding for item in ordered)

    return vectors

def embed_query(text: str) -> list[float]:
    """
    Embed a single query.

    Must use the same model as embed_texts. A query vector from one model
    compared against document vectors from another produces similarity scores
    that look plausible and mean nothing -- there is no error, just silently
    bad retrieval. Both paths read settings.embedding_model for this reason.
    """
    return embed_texts([text])[0]