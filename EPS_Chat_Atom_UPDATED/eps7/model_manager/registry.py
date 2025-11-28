
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Iterable, List
from ..config import load_default_providers
from .schemas import ModelInfo
from .base_provider import BaseProvider

from .providers.openai_provider import OpenAIProvider
from .providers.gemini_provider import GeminiProvider
from .providers.anthropic_provider import AnthropicProvider
from .providers.mistral_provider import MistralProvider
from .providers.cohere_provider import CohereProvider
from .providers.groq_provider import GroqProvider
from .providers.xai_provider import XAIProvider
from .providers.together_provider import TogetherProvider
from .providers.deepseek_provider import DeepSeekProvider
from .providers.bedrock_provider import BedrockProvider

PROVIDER_CLASSES = {
    "openai": OpenAIProvider,
    "gemini": GeminiProvider,
    "anthropic": AnthropicProvider,
    "mistral": MistralProvider,
    "cohere": CohereProvider,
    "groq": GroqProvider,
    "xai": XAIProvider,
    "together": TogetherProvider,
    "deepseek": DeepSeekProvider,
    "bedrock": BedrockProvider,
}

@dataclass
class ProviderEntry:
    id: str
    instance: BaseProvider

def build_providers() -> Dict[str, ProviderEntry]:
    providers_cfg = load_default_providers()
    providers: Dict[str, ProviderEntry] = {}
    for pid, cls in PROVIDER_CLASSES.items():
        cfg = providers_cfg.get(pid)
        if not cfg or not cfg.api_key:
            continue
        providers[pid] = ProviderEntry(id=pid, instance=cls(cfg))
    return providers

def fetch_all_models() -> List[ModelInfo]:
    models: List[ModelInfo] = []
    for pid, entry in build_providers().items():
        try:
            for m in entry.instance.list_models():
                models.append(m)
        except Exception as exc:
            print(f"[WARN] Failed to fetch models for provider {pid}: {exc}")
    return models
