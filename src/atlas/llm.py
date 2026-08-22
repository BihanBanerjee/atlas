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
        model=settings.synthesis_model,
        max_tokens=max_tokens,
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

