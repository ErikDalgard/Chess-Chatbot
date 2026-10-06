import os
from google import genai
from collections import defaultdict
from typing import Protocol, TypeVar
from pydantic import BaseModel
import base64
from pathlib import Path
from google.genai import types

T = TypeVar("T", bound=BaseModel)

_MIME_TYPES = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
}

class GeminiModel:
    def __init__(self, api_key, model_name):
        self.model_name = model_name
        self.client = genai.Client(api_key=api_key)
        self.chats = defaultdict(lambda: None)

    def stream(self, instructions, input_text, session_id):
            extra = {}
            if self.chats[session_id]:
                extra["previous_interaction_id"] = self.chats[session_id]
            
            #Streaming the response
            stream = self.client.interactions.create(
                model=self.model_name,
                system_instruction=instructions,
                input=input_text,
                stream=True,
                **extra,
                )
            
            answer = ""
            for event in stream:
                if event.event_type == "interaction.created":
                    self.chats[session_id] = event.interaction.id
                elif event.event_type == "step.delta" and getattr(event.delta, "type", None) == "text":
                    answer += event.delta.text
                    yield answer

    def parse_image(
        self,
        image_path: str,
        output_type: type[T],
        *,
        prompt: str | None = None,
        instructions: str | None = None,
    ) -> T:
        contents: list = []
        if image_path is not None:
            path = Path(image_path)
            mime_type = _MIME_TYPES.get(path.suffix.lower())
            if mime_type is None:
                raise ValueError(f"Unsupported image type: {path.suffix}")
            contents.append(
                types.Part.from_bytes(data=path.read_bytes(), mime_type=mime_type)
            )

        contents.append(prompt or "Read the chess position in this image.")

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=instructions,
                response_mime_type="application/json",
                response_json_schema=output_type.model_json_schema(),
            ),
        )

        return output_type.model_validate_json(response.text)