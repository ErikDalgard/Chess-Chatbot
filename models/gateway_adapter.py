import os
from openai import OpenAI


class GatewayModel:
    def __init__(self, default_model):
        self.default_model = default_model
        self.client = OpenAI(
        api_key=os.getenv('AI_GATEWAY_API_KEY'),
        base_url='https://ai-gateway.vercel.sh/v1')