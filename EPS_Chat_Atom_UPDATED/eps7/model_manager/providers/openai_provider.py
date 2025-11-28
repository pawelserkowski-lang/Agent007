
from __future__ import annotations
from typing import Iterable, List
import requests
from ..schemas import ModelInfo
from ..base_provider import BaseProvider

class OpenAIProvider(BaseProvider):
    id = "openai"
    name = "OpenAI"

    def list_models(self) -> Iterable[ModelInfo]:
        if not self.config.api_key:
            return []
        # Build the models endpoint from the configured base URL.  OpenAI
        # recommends using https://api.openai.com/v1 as the default base; this
        # allows users to override via `OPENAI_BASE_URL` if routing through a
        # proxy.  Remove any trailing slash before appending `/models`.
        base_url = self.config.base_url or "https://api.openai.com/v1"
        base_url = base_url.rstrip("/")
        url = f"{base_url}/models"

        # Authenticate using a bearer token.  Include `Content-Type` even on GET
        # for consistency with other providers.
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }

        resp = requests.get(url, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        models: List[ModelInfo] = []

        raw_models = data.get("data") or data.get("models") or data.get("foundationModels") or []
        for item in raw_models:
            model_id = item.get("id") or item.get("modelId") or item.get("name")
            display_name = item.get("display_name") or item.get("displayName") or model_id
            capabilities: list[str] = []
            meta = item.get("metadata") or {}
            if isinstance(meta, dict):
                caps = meta.get("capabilities") or meta.get("capability") or []
                if isinstance(caps, str):
                    capabilities = [caps]
                elif isinstance(caps, list):
                    capabilities = caps

            models.append(
                ModelInfo(
                    provider_id=self.id,
                    model_id=model_id,
                    display_name=display_name,
                    capabilities=capabilities,
                    is_multimodal=any(c in capabilities for c in ("vision", "audio", "files")),
                    context_window=meta.get("context_length") if isinstance(meta, dict) else None,
                    license=meta.get("license") if isinstance(meta, dict) else None,
                    raw=item,
                )
            )
        return models
