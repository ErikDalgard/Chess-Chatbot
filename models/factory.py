import os
from models.interface import Model
from models.gateway_adapter import GatewayModel
from models.gemini_adapter import GeminiModel
from dotenv import load_dotenv
load_dotenv() 

def create_model() -> Model:
    """Create the configured LLM adapter.

    Defaults to the Vercel AI Gateway with ``openai/gpt-5-mini``, which supports
    streaming, vision, and tool calling (required for puzzle mode).
    """
    provider = os.getenv("LLM_PROVIDER", "gateway").lower()
    model_name = os.getenv("LLM_MODEL", "openai/gpt-5-mini")

    if provider == "gateway":
        api_key = os.environ["GATEWAY_API_KEY"]
        return GatewayModel(
            api_key=api_key,
            model_name=model_name,
        )

    if provider == "gemini":
        api_key = os.environ["GEMINI_API_KEY"]
        return GeminiModel(
            api_key=api_key,
            model_name=model_name,
        )

    raise ValueError(f"Unsupported LLM provider: {provider}")
