import os
from openai import OpenAI
from collections import defaultdict
from typing import Protocol, TypeVar
from pydantic import BaseModel
import base64


T = TypeVar("T", bound=BaseModel)

class GatewayModel:
    def __init__(self, api_key, model_name):
        self.model_name = model_name
        self.chats = defaultdict(lambda: None)

        self.client = OpenAI(
        api_key=api_key,
        base_url='https://ai-gateway.vercel.sh/v1')
        
    def stream(self, instructions, input_text, session_id):

        history = self.chats.setdefault(session_id, [])
        history.append({"role": "user", "content": input_text,})

        #Streaming the response
        stream = self.client.responses.create(
            model=self.model_name,
            instructions=instructions,
            input=history,
            stream=True
            )
  
        answer = ""
        for event in stream:
           if event.type == 'response.output_text.delta':
                answer += event.delta
                yield answer
        history.append({"role": "assistant", "content": answer,})

    # Function to encode the image
    def encode_image(self, image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")

    def parse_image(
        self,
        image_path: str,
        output_type: type[T],
        *,
        prompt: str | None = None,
        instructions: str | None = None,
    ) -> T:
        base64_image = self.encode_image(image_path)
        content = [
            {
                "type": "input_image",
                "image_url": f"data:image/jpeg;base64,{base64_image}",
            },
            {
                "type": "input_text",
                "text": prompt or "Analyze this image.",
            },
        ]

        response = self.client.responses.parse(
            model=self.model_name,
            instructions=instructions,
            input=[
                {
                    "role": "user",
                    "content": content,
                }
            ],
            text_format=output_type,
        )

        if response.output_parsed is None:
            raise ValueError("The model returned no parsed output")

        return response.output_parsed
