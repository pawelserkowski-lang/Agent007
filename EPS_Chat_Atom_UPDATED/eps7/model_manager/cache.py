
from __future__ import annotations
import json
import time
from pathlib import Path
from typing import Iterable
from .schemas import ModelInfo

CACHE_FILE = Path(__file__).resolve().parent / "model_cache.json"
CACHE_TTL_SECONDS = 3600

def _now_ts() -> int:
    return int(time.time())

def load_cache() -> dict | None:
    if not CACHE_FILE.exists():
        return None
    try:
        data = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    if _now_ts() - data.get("timestamp", 0) > CACHE_TTL_SECONDS:
        return None
    return data

def save_cache(models: Iterable[ModelInfo]) -> None:
    data = {
        "timestamp": _now_ts(),
        "models": [
            {
                "provider_id": m.provider_id,
                "model_id": m.model_id,
                "display_name": m.display_name,
                "capabilities": m.capabilities,
                "is_multimodal": m.is_multimodal,
                "context_window": m.context_window,
                "license": m.license,
            }
            for m in models
        ],
    }
    CACHE_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
