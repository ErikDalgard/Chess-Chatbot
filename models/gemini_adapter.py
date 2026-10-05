import os
from google import genai

class OpenAIModel:
    def __init__(self, default_model):
        self.default_model = default_model
        API_KEY = os.environ["GEMINI_API_KEY"]
        self.client = genai.Client(api_key=API_KEY)

    def stream(self, model, instructions, input):
        