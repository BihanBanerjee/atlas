"""
Query -> vector -> nearest neighbours.

One embedding of the question, one cosine search, take the top 5. Nothing
filters or re-scores what comes back -- whatever is nearest in vector space goes
straight into the prompt.

Two things I'm suspicious of but haven't measured yet:

  Distinctive names get blurred. "Fernpath" tokenises into ['F','ern','path'],
  "Northwind" into ['North','wind']. Embeddings capture meaning, and a made-up
  company name doesn't have much meaning to capture -- so a query naming one
  might not rank the document that actually contains it any higher than a
  document about something vaguely similar.

  Nearest is not the same as most relevant. Cosine similarity scores the query
  and the document separately and then compares two compressed summaries. It
  never looks at the pair together, so "close in vector space" and "actually
  answers the question" can come apart.

Both are guesses right now. Leaving them written down so I can check whether the
eval shows either of them actually happening.
"""


from __future__ import annotations


from atlas.config import settings
from atlas.embeddings import embed_query
from atlas.store import Hit, search as vector_search


def retrieve(question: str, k: int | None = None) -> list[Hit]:
    """Return the top-k chunks for a question, most similar first."""
    query_vector = embed_query(question)
    return vector_search(query_vector, limit=k or settings.top_k)