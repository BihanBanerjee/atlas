"""
Retrieved chunks + question -> a cited answer.

Two of the rules do most of the work: every factual claim carries a chunk id,
and a claim that cannot be cited must not be made. The second one is what the
missing_data questions in the golden set are for -- the corpus deliberately
cannot answer them, and a plausible-sounding invented reply is the failure I'm
looking for. Grounding isn't decoration; it's the thing being measured.

Worth noting what this does NOT do: there's no relevance threshold. Whatever
retrieval hands back goes into the prompt, however weak the score. If the top
chunk is junk, the model gets junk and is asked to answer anyway -- and because
the prompt tells it to cite, it may well cite the junk. I'm leaving that in
rather than papering over it with a cutoff, because I want to see whether it
actually happens before I decide what to do about it. Still unmeasured.

I'm keeping the prompt scoped to the version. Right now the pipeline is
retrieve -> rerank -> one grounded call, so the prompt covers citation, source
conflict, derivation and partial answers, and nothing else. Injection
resistance, scope control and PII redaction are their own layers and I'd rather
add them as layers than bury them here -- and a PII rule would fail q15 and q16
outright, because those golden answers want the salary figures.

Rules 2 and 3 are new, and both exist because of what retrieval now does.
Hybrid search and reranking pull the *most similar* chunks they can find, and
this corpus is mostly near-duplicates: six monthly investor updates, an ARR
figure for every month, two pitch decks eleven days apart. The tighter the
window gets, the more the candidates differ only by date -- so telling them
apart is the generator's problem now. The date was already sitting in every
source header and I had never told the model it meant anything.

Rule 3 is there because the old wording ("never infer a fact that is not
stated") forbade answers the golden set asks for: "$25,000 over the approved
budget" is arithmetic on two stated figures, not something invented.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from atlas.llm import complete
from atlas.retrieve import retrieve
from atlas.store import Hit


SYSTEM_PROMPT = """You answer questions using only the numbered sources provided.

Rules:
1. Every factual claim must cite its source as [1], [2], etc. Put the citation
   next to the claim it supports, not in a group at the end of the answer.
2. Sources are dated. When two sources disagree, prefer the most recent and say
   which date your answer reflects. If the question asks about a particular
   time, use the source covering that time rather than the newest one.
3. You may combine sources, and you may do arithmetic on figures they state.
   You may not introduce a fact that no source states.
4. If the sources do not contain the answer, say so plainly and do not guess.
   It is correct and expected to reply that the information is not available.
   If you can support part of the question, answer that part and say which
   part you cannot support.
5. Do not use knowledge from outside the provided sources.
6. Lead with the answer. Be concise."""

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