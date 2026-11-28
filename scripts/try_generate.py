"""
Run the generator once, by hand, and look at what comes back.

Not a test and not an eval -- there is no scoring here. This is the check you
want before paying for forty judged answers: does the Anthropic client
authenticate, does claude-haiku-4-5 accept the request shape, and does the
model actually produce [1]/[2] citations the way the system prompt asks? A 400
or a citation format the eval cannot parse is much cheaper to find on one
question than on question 1 of a full run.

It prints the retrieved sources before the answer on purpose. When an answer
looks wrong the first question is always "what was it given", and having both
on screen together saves a second run.

Usage:
    uv run python scripts/try_generate.py
    uv run python scripts/try_generate.py "your own question here"

Costs one generation call -- a few hundred tokens on Haiku.
"""

from __future__ import annotations

import re
import sys

from atlas.config import settings
from atlas.generate import answer_question


# The ARR question, deliberately. The corpus carries an ARR figure for every
# month from February to August, so retrieval returns a cluster of near
# identical chunks that differ only by date -- and in the row 10 run the June
# chunk came back ABOVE the July one. That makes this the question that
# exercises the dated-source rule in the prompt: sources are dated, and when
# they disagree the one covering the asked-about period wins.
#
# The right answer is $1,040,000, from July MRR of $86,700. If the model
# answers $940,000 it has taken the top chunk instead of the right one.
DEFAULT_QUESTION = "What was Tensile's ARR in July 2026?"

def main() -> None:
    question = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_QUESTION

    print(f"collection  {settings.qdrant_collection}")
    print(f"generator   {settings.generation_model}")
    print(f"retrieval   top_k={settings.top_k} · hybrid={settings.hybrid_enabled} · "
          f"rerank={settings.reranker_model if settings.rerank_enabled else 'off'}")
    print()
    print(f"QUESTION\n  {question}\n")

    answer = answer_question(question)

    print("RETRIEVED")
    for index, hit in enumerate(answer.hits, start=1):
        score = f"{hit.rerank_score:.3f}" if hit.rerank_score is not None else f"{hit.score:.3f}"
        print(f"  [{index}] {score}  {hit.doc_id} (chunk {hit.chunk_index})  {hit.date}")
        print(f"       {hit.text[:88].replace(chr(10), ' ')}...")
    print()

    print("ANSWER")
    for line in answer.text.splitlines():
        print(f"  {line}")
    print()

    # Only the bracket form counts. Scanning for bare digits picks up the 1, 4
    # and 0 in "$1,040,000" and the 2, 0, 2, 6 in "2026" -- which is how the
    # first version of this reported six citations in an answer that had two.
    cited = sorted({int(n) for n in re.findall(r"\[(\d+)\]", answer.text)})
    stray = [n for n in cited if n > len(answer.hits)]

    print(f"tokens      in {answer.input_tokens} · out {answer.output_tokens} · "
          f"total {answer.input_tokens + answer.output_tokens}")
    if not cited:
        print("citations   NONE FOUND -- the eval will not be able to parse this")
    else:
        print(f"citations   {' '.join(f'[{n}]' for n in cited)}"
              f"  ({len(cited)} of {len(answer.hits)} sources used)")
    if stray:
        # A citation numbered above the sources provided is an invented
        # reference, which is worse than none: it reads as grounded and isn't.
        print(f"            WARNING: {stray} exceed the {len(answer.hits)} sources provided")


if __name__ == "__main__":
    main()