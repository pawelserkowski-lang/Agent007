
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Literal

Capability = Literal["text", "chat", "code", "vision", "audio", "files", "realtime", "embeddings"]

@dataclass
class ModelInfo:
    provider_id: str
    model_id: str
    display_name: str
    capabilities: list[Capability] = field(default_factory=list)
    is_multimodal: bool = False
    context_window: int | None = None
    license: str | None = None
    is_default: bool = False
    raw: dict | None = None
