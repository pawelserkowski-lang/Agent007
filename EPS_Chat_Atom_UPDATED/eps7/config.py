
import os
from dataclasses import dataclass

@dataclass
class ProviderConfig:
    name: str
    api_key: str | None
    base_url: str | None = None

def getenv(name: str) -> str | None:
    value = os.getenv(name)
    return value if value else None

def load_default_providers() -> dict[str, ProviderConfig]:
    """
    Load provider configuration from environment variables.

    Supported providers (all must expose a list-models API endpoint):
      - OpenAI
      - Google Gemini
      - Anthropic (Claude)
      - Mistral AI
      - Cohere
      - xAI (Grok)
      - Groq
      - Together AI
      - DeepSeek
      - Amazon Bedrock (optional, as multi-provider hub)
    """
    return {
        "openai": ProviderConfig(
            name="OpenAI",
            api_key=getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        ),
        "gemini": ProviderConfig(
            name="Google Gemini",
            api_key=getenv("GEMINI_API_KEY"),
            base_url=os.getenv("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1"),
        ),
        "anthropic": ProviderConfig(
            name="Anthropic Claude",
            api_key=getenv("ANTHROPIC_API_KEY"),
            base_url=os.getenv("ANTHROPIC_BASE_URL", "https://api.anthropic.com/v1"),
        ),
        "mistral": ProviderConfig(
            name="Mistral AI",
            api_key=getenv("MISTRAL_API_KEY"),
            base_url=os.getenv("MISTRAL_BASE_URL", 'https://api.mistral.ai/v1'),
        ),
        "cohere": ProviderConfig(
            name="Cohere",
            api_key=getenv("COHERE_API_KEY"),
            base_url=os.getenv("COHERE_BASE_URL", "https://api.cohere.com/v1"),
        ),
        "xai": ProviderConfig(
            name="xAI Grok",
            api_key=getenv("XAI_API_KEY"),
            base_url=os.getenv("XAI_BASE_URL", "https://api.x.ai/v1"),
        ),
        "groq": ProviderConfig(
            name="Groq",
            api_key=getenv("GROQ_API_KEY"),
            base_url=os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1"),
        ),
        "together": ProviderConfig(
            name="Together AI",
            api_key=getenv("TOGETHER_API_KEY"),
            base_url=os.getenv("TOGETHER_BASE_URL", "https://api.together.xyz/v1"),
        ),
        "deepseek": ProviderConfig(
            name="DeepSeek",
            api_key=getenv("DEEPSEEK_API_KEY"),
            base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
        ),
        "bedrock": ProviderConfig(
            name="Amazon Bedrock",
            api_key=getenv("BEDROCK_API_KEY"),
            base_url=None,
        ),
    }
