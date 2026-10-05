from typing import Protocol
from collections.abc import Iterator

class Model(Protocol):
    def stream(self, model, instructions, input) -> Iterator[str]:
        answer = ""
            for event in stream:
                if event.event_type == "interaction.created":
                    chats[session_id] = event.interaction.id
                elif event.event_type == "step.delta" and getattr(event.delta, "type", None) == "text":
                    answer += event.delta.text
                    yield answer


