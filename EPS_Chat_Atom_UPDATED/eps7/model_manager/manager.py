
from __future__ import annotations
from typing import Iterable, List
from .schemas import ModelInfo
from . import cache
from .registry import fetch_all_models

def get_models(force_refresh: bool = False) -> List[ModelInfo]:
    if not force_refresh:
        cached = cache.load_cache()
        if cached:
            return [
                ModelInfo(
                    provider_id=m["provider_id"],
                    model_id=m["model_id"],
                    display_name=m["display_name"],
                    capabilities=m.get("capabilities", []),
                    is_multimodal=m.get("is_multimodal", False),
                    context_window=m.get("context_window"),
                    license=m.get("license"),
                )
                for m in cached.get("models", [])
            ]
    models = fetch_all_models()
    cache.save_cache(models)
    return models

def group_by_provider(models: Iterable[ModelInfo]) -> dict[str, list[ModelInfo]]:
    grouped: dict[str, list[ModelInfo]] = {}
    for m in models:
        grouped.setdefault(m.provider_id, []).append(m)
    return grouped

def filter_by_capability(models: Iterable[ModelInfo], capability: str) -> list[ModelInfo]:
    return [m for m in models if capability in m.capabilities]
