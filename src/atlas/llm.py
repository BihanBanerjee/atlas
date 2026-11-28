"""
The single call site for every Claude request in the system.

Nothing else in the codebase imports the anthropic SDK, and that's deliberate.
Right now this file is thin enough to look like pointless indirection -- it's one
API call wrapped in a function. The bet is that anything I later want to do to
every model call (count what it costs, retry it when it fails, log it, or swap
the provider entirely) has exactly one place to go. Adding that later across six
modules that each call the SDK directly is a much worse afternoon than adding it
here.

Model note: claude-haiku-4-5 predates adaptive thinking and the `effort`
parameter. Passing `effort` to it returns a 400. Plain messages.create is what
this model wants.
"""


from __future__ import annotations

from dataclasses import dataclass

from anthropic import Anthropic

from atlas.config import settings

_client = Anthropic(api_key=settings.anthropic_api_key)


@dataclass
class LLMResponse:
    text: str
    input_tokens: int
    output_tokens: int


    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


def complete(system: str, user: str, max_tokens: int = 2048) -> LLMResponse:
    """
    One turn, no history, no tools. That is all this version needs.

    Token counts come back on the response, so returning them costs nothing --
    and it means the eval runner can report tokens per query without a second
    call to count them.
    """

    message = _client.messages.create(
        model=settings.generation_model,
        max_tokens=max_tokens,
        # Anthropic defaults to 1.0. Zero is here for measurement, not for
        # grounding: the judge scores text, so a generator that rewords itself
        # between runs puts noise underneath every faithfulness number. Two
        # identical runs of the same question produced different prose before
        # this was set.
        #
        # It does not prevent hallucination. Zero makes the model take the most
        # likely next token every time, so an unsupported claim becomes a
        # *repeatable* unsupported claim. Grounding comes from the citation
        # rules in the prompt and from what retrieval puts in the window, not
        # from this parameter.
        #
        # Verified rather than assumed: the SDK's MIGRATION.md says "current
        # models do not use these sampling parameters" and removes temperature
        # from the signature at 2.x. On 0.124.0 with claude-haiku-4-5 it is
        # still in the signature and it is still honoured -- two runs of the
        # same question returned different prose before this line and
        # byte-identical prose after. If the SDK is ever upgraded past 2.x this
        # becomes a TypeError, which is why the dependency is capped.
        temperature=0,
        system=system,
        messages=[{"role": "user", "content": user}]
    )

    # content is a list of blocks; a plain text answer is one text block, but
    # index [0] blindly is how you get a crash the first time that assumption breaks.
    text = "".join(block.text for block in message.content if block.type == "text")


    return LLMResponse(
        text=text,
        input_tokens=message.usage.input_tokens,
        output_tokens=message.usage.output_tokens
    )

