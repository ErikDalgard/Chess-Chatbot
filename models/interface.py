from collections.abc import Iterator
from typing import Protocol, TypeVar
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)
class Model(Protocol):
    def __init__(self, api_key, model_name):
        ...
    def stream(self, instructions, input_text, session_id) -> Iterator[str]:
        ...
    def parse_image(self, image_path: str, output_type: type[T],*,
                    prompt: str | None = None, instructions: str | None = None,) -> T:
        ...

