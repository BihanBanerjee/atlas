"""
Retrieved chunks + question -> a cited answer.

Two rules in the system prompt do all the work here: every factual claim carries
a chunk id, and a claim that cannot be cited must not be made. The second one is
what the missing_data questions in the golden set are for -- the corpus
deliberately cannot answer them, and a plausible-sounding invented reply is the
failure I'm looking for. Grounding isn't decoration; it's the thing being
measured.

Worth noting what this does NOT do: there's no relevance threshold. Whatever
retrieval hands back goes into the prompt, however weak the score. If the top
chunk is junk, the model gets junk and is asked to answer anyway -- and because
the prompt tells it to cite, it may well cite the junk. I'm leaving that in
rather than papering over it with a cutoff, because I want to see whether it
actually happens before I decide what to do about it.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from atlas.llm import complete
from atlas.retrieve import retrieve
from atlas.store import Hit


SYSTEM_PROMPT = """You answer questions using only the numbered sources provided.

Rules:
1. Every factual claim must cite its source as [1], [2], etc.
2. If the sources do not contain the answer, say so plainly and do not guess.
   Never infer a fact that is not stated. It is correct and expected to reply
   that the information is not available.
3. Do not use knowledge from outside the provided sources.
4. Be concise. Answer the question asked, nothing more."""

@dataclass
class Answer:
    text: str
    contexts: list[str] = field(default_factory=list)
    hits: list[Hit] = field(default_factory=list)
    input_tokens: int = 0
    output_tokens: int = 0


def _format_sources(hits: list[Hit]) -> str:
    """Number the chunks so the model has stable ids to cite."""
    blocks = []
    for index, hit in enumerate(hits, start=1):
        header = f"[{index}] source={hit.source} | title={hit.title} | date={hit.date}"
        blocks.append(f"{header}\n{hit.text}")
    return "\n\n--\n\n".join(blocks)


def answer_question(question: str, k:int | None = None) -> Answer:
    """Full v0.1 query path: retrieve and then synthesize."""
    hits = retrieve(question, k=k)

    if not hits:
        return Answer(text="No sources were retrieved, so I cannot answer this.")

    user_prompt = (
        f"Sources: \n\n{_format_sources(hits)}\n\n"
        f"Question: {question}"
    )

    response = complete(system=SYSTEM_PROMPT, user=user_prompt)

    return Answer(
        text=response.text,
        contexts=[hit.text for hit in hits],
        hits=hits,
        input_tokens=response.input_tokens,
        output_tokens=response.output_tokens,
    )