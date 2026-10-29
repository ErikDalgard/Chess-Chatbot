from collections.abc import Iterator
from typing import Protocol, TypeVar
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class Model(Protocol):
    """Shared LLM surface used by chat, board reading, and puzzle tooling.

    All adapters implement streaming and structured image parsing.
    Puzzle mode additionally requires ``stream_tools`` and ``clear_history``
    (implemented by the Vercel AI Gateway adapter).
    """

    def __init__(self, api_key, model_name):
        ...

    def stream(self, instructions, input_text, session_id) -> Iterator[str]:
        ...

    def parse_image(
        self,
        image_path: str,
        output_type: type[T],
        *,
        prompt: str | None = None,
        instructions: str | None = None,
    ) -> T:
        ...

    def parse_text(
        self,
        output_type: type[T],
        *,
        prompt: str,
        instructions: str | None = None,
    ) -> T:
        ...
