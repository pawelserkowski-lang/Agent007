
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Tuple
import time

@dataclass
class TokenUsage:
    provider_id: str
    model_id: str
    input_tokens: int = 0
    output_tokens: int = 0
    cost: float = 0.0
    last_updated: float = field(default_factory=time.time)

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

class TokenTracker:
    """Simple in-memory tracker of token usage per model."""

    def __init__(self) -> None:
        self._usage: Dict[Tuple[str, str], TokenUsage] = {}

    def register_call(
        self,
        provider_id: str,
        model_id: str,
        input_tokens: int,
        output_tokens: int,
        cost: float | None = None,
    ) -> None:
        key = (provider_id, model_id)
        entry = self._usage.get(key)
        if not entry:
            entry = TokenUsage(provider_id=provider_id, model_id=model_id)
            self._usage[key] = entry

        entry.input_tokens += int(input_tokens)
        entry.output_tokens += int(output_tokens)
        entry.last_updated = time.time()
        if cost is not None:
            entry.cost += float(cost)

    def totals(self) -> TokenUsage:
        total = TokenUsage(provider_id="*", model_id="*")
        for entry in self._usage.values():
            total.input_tokens += entry.input_tokens
            total.output_tokens += entry.output_tokens
            total.cost += entry.cost
        return total

    def per_model(self) -> Dict[Tuple[str, str], TokenUsage]:
        return dict(self._usage)
