import os
from openai import OpenAI
from collections import defaultdict
from typing import Protocol, TypeVar
from pydantic import BaseModel
import base64
import openai
import json

T = TypeVar("T", bound=BaseModel)

class Tool:
    def __init__(self, function, ArgType: T, name: str, description: str):
        self.ArgType = ArgType
        self.name=name
        self.description = description
        self.function = function

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


    def parse_text(
            self,
            output_type: type[T],
            *,
            prompt: str,
            instructions: str | None = None,
        ) -> T:
        
        content = [
            {
                "type": "input_text",
                "text": prompt
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

    def stream_tools_from_history(self, instructions, session_id, tools, depth, max_depth):
        tool_name_to_func = {}
        formatted_tools = []
        for tool in tools:
            tool_name_to_func[tool.name] = tool.function
            
            
            generated = openai.pydantic_function_tool(
                    tool.ArgType, name=tool.name, description= tool.description)

            formatted_tools.append(
                    {
                        "type": "function",
                        **generated["function"],
                    })

        history = self.chats.setdefault(session_id, [])

        # 2. Prompt the model with tools defined
        stream = self.client.responses.create(
            model=self.model_name,
            instructions=instructions,
            tools=formatted_tools,
            input=history,
            stream=True,
        )
        print(history)
    
        tool_calls = []

            
        answer = ""
        for event in stream:
            if event.type == "response.output_text.delta":
                answer += event.delta
                yield answer
    
            elif event.type == "response.output_item.done":
                if event.item.type == "function_call":
                    tool_calls.append(event.item)

        history.append({"role": "assistant", "content": answer,})
    
        if tool_calls:
            for call in tool_calls:
                history.append({
                "type": "function_call",
                "call_id": call.call_id,
                "name": call.name,
                "arguments": call.arguments,
            })
    
            # Execute each completed tool call
            tool_outputs = []
    
            for call in tool_calls:
                args = json.loads(call.arguments)

                func = tool_name_to_func.get(call.name)
                if func:
                    result = func(**args)
                else:
                    raise ValueError(f"Unknown tool: {call.name}")
    
                tool_outputs.append({
                    "type": "function_call_output",
                    "call_id": call.call_id,
                    "output": json.dumps(result),
                })
            history.extend(tool_outputs)

            if depth < max_depth:
                yield from self.stream_tools_from_history(instructions, session_id, tools, depth + 1, max_depth)


    def stream_tools(self, instructions, input_text, session_id, tools: list[Tool], max_depth):
        history = self.chats.setdefault(session_id, [])
        history.append({"role": "user", "content": input_text,})
        yield from self.stream_tools_from_history(instructions, session_id, tools, 1, max_depth)
       
            