
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Callable, Any
import threading
import time

import requests  # type: ignore[import]

from .config import load_default_providers
from .tokens import TokenTracker
from .model_manager.schemas import ModelInfo


@dataclass
class ChatResult:
    model: ModelInfo
    text: str
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    cost: Optional[float] = None
    raw: Optional[dict[str, Any]] = None
    error: Optional[str] = None
    latency_s: Optional[float] = None


class ChatEngine:
    """Silnik rozmów EPS 7.x.

    Obsługa (szkic):
    - providerzy zgodni z OpenAI (`/chat/completions`):
        openai, groq, xai, together, deepseek, mistral
    - providerzy z własnym stylem API:
        gemini  -> Google Generative Language API (`:generateContent`)
        anthropic -> /v1/messages
        cohere  -> /v1/chat

    Dla prostoty:
    - strumieniowanie (stream=True) nie jest jeszcze zaimplementowane,
    - koszt jest pozostawiony jako None (możesz dodać wyliczenia według cennika).
    """

    def __init__(self, tracker: Optional[TokenTracker] = None) -> None:
        self.tracker = tracker

    # PUBLIC API

    def chat(
        self,
        model: ModelInfo,
        prompt: str,
        stream: bool = False,
        temperature: float = 0.2,
    ) -> ChatResult:
        cfg = self._get_provider_cfg(model.provider_id)
        if not cfg or not cfg.api_key:
            return ChatResult(
                model=model,
                text=f"[BŁĄD] Brak API key dla providera {model.provider_id}.",
                error="missing_api_key",
            )

        pid = model.provider_id

        if pid in {"openai", "groq", "xai", "together", "deepseek", "mistral"}:
            return self._chat_openai_compatible(cfg, model, prompt, stream=stream, temperature=temperature)

        if pid == "gemini":
            return self._chat_gemini(cfg, model, prompt, temperature=temperature)

        if pid == "anthropic":
            return self._chat_anthropic(cfg, model, prompt, temperature=temperature)

        if pid == "cohere":
            return self._chat_cohere(cfg, model, prompt, temperature=temperature)

        return ChatResult(
            model=model,
            text=f"[INFO] Provider {pid} nie jest jeszcze obsługiwany przez ChatEngine.",
            error="provider_not_implemented",
        )

    def chat_async(
        self,
        model: ModelInfo,
        prompt: str,
        on_finished: Callable[[ChatResult], None],
        stream: bool = False,
        temperature: float = 0.2,
    ) -> None:
        def worker() -> None:
            result = self.chat(model, prompt, stream=stream, temperature=temperature)
            on_finished(result)

        t = threading.Thread(target=worker, daemon=True)
        t.start()

    # INTERNAL

    def _get_provider_cfg(self, provider_id: str):
        providers = load_default_providers()
        return providers.get(provider_id)

    # --- OpenAI-compatible providers ---

    def _chat_openai_compatible(self, cfg, model: ModelInfo, prompt: str, stream: bool, temperature: float) -> ChatResult:
        base_url = cfg.base_url or "https://api.openai.com/v1"
        url = base_url.rstrip("/") + "/chat/completions"

        headers = {
            "Authorization": f"Bearer {cfg.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": model.model_id,
            "messages": [
                {"role": "user", "content": prompt},
            ],
            "temperature": float(temperature),
        }

        t0 = time.time()
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=60)
            latency = time.time() - t0
            # If the response indicates an error (e.g. 4xx/5xx), raise an exception
            resp.raise_for_status()
            data = resp.json()
        except requests.HTTPError as exc:
            # Provide a more specific message for 403 Forbidden errors.  This
            # typically means the request is recognized but denied, for reasons
            # such as missing permissions, disabled models, or geographic
            # restrictions【811370743087972†screenshot】.
            status = None
            try:
                status = exc.response.status_code  # type: ignore[assignment]
            except Exception:
                pass
            if status == 403:
                err_text = (
                    "[BŁĄD 403] Dostęp zabroniony – sprawdź klucz API, uprawnienia "
                    "do modelu, projekt lub region/IP."
                )
            else:
                err_text = f"[BŁĄD] Wywołanie API nie powiodło się: {exc}"
            return ChatResult(
                model=model,
                text=err_text,
                error="http_error",
            )
        except Exception as exc:  # noqa: BLE001
            return ChatResult(
                model=model,
                text=f"[BŁĄD] Wywołanie API nie powiodło się: {exc}",
                error="http_error",
            )

        text = self._extract_openai_like_text(data)
        input_tokens, output_tokens = self._extract_openai_like_usage(data)
        cost = None

        self._track_usage(model, input_tokens, output_tokens, cost)

        return ChatResult(
            model=model,
            text=text,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost=cost,
            raw=data,
            latency_s=latency,
        )

    def _extract_openai_like_text(self, data: dict[str, Any]) -> str:
        try:
            choice = (data.get("choices") or [{}])[0]
            msg = choice.get("message") or {}
            text = msg.get("content") or "[BRAK TREŚCI]"
        except Exception:  # noqa: BLE001
            text = str(data)
        return text

    def _extract_openai_like_usage(self, data: dict[str, Any]) -> tuple[int, int]:
        usage = data.get("usage") or {}
        input_tokens = usage.get("prompt_tokens") or usage.get("input_tokens") or 0
        output_tokens = usage.get("completion_tokens") or usage.get("output_tokens") or 0
        return int(input_tokens), int(output_tokens)

    # --- Gemini (Google Generative Language API) ---

    def _chat_gemini(self, cfg, model: ModelInfo, prompt: str, temperature: float) -> ChatResult:
        # Używamy oficjalnego REST API: POST /v1/models/{model}:generateContent?key=API_KEY
        base_url = cfg.base_url or "https://generativelanguage.googleapis.com/v1"
        url = base_url.rstrip("/") + f"/models/{model.model_id}:generateContent"

        params = {"key": cfg.api_key}
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt},
                    ]
                }
            ],
            "generationConfig": {
                "temperature": float(temperature),
                "maxOutputTokens": 1024,
            },
        }

        t0 = time.time()
        try:
            resp = requests.post(url, headers=headers, params=params, json=payload, timeout=60)
            latency = time.time() - t0
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:  # noqa: BLE001
            return ChatResult(
                model=model,
                text=f"[BŁĄD GEMINI] {exc}",
                error="http_error",
            )

        text = ""
        try:
            candidates = data.get("candidates") or []
            if candidates:
                cand = candidates[0]
                content = cand.get("content") or {}
                parts = content.get("parts") or []
                texts = []
                for p in parts:
                    if isinstance(p, dict) and "text" in p:
                        texts.append(str(p["text"]))
                text = "".join(texts) if texts else str(cand)
            else:
                text = "[BRAK KANDYDATÓW]"  # noqa: E501
        except Exception:  # noqa: BLE001
            text = str(data)

        usage = data.get("usageMetadata") or {}
        input_tokens = int(usage.get("promptTokenCount", 0))
        output_tokens = int(usage.get("candidatesTokenCount", 0))
        cost = None

        self._track_usage(model, input_tokens, output_tokens, cost)

        return ChatResult(
            model=model,
            text=text,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost=cost,
            raw=data,
            latency_s=latency,
        )

    # --- Anthropic Claude ---

    def _chat_anthropic(self, cfg, model: ModelInfo, prompt: str, temperature: float) -> ChatResult:
        base_url = cfg.base_url or "https://api.anthropic.com/v1"
        url = base_url.rstrip("/") + "/messages"

        headers = {
            "x-api-key": cfg.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }

        payload = {
            "model": model.model_id,
            "messages": [
                {"role": "user", "content": prompt},
            ],
            "max_tokens": 1024,
            "temperature": float(temperature),
        }

        t0 = time.time()
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=60)
            latency = time.time() - t0
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:  # noqa: BLE001
            return ChatResult(
                model=model,
                text=f"[BŁĄD CLAUDE] {exc}",
                error="http_error",
            )

        text = ""
        try:
            parts = data.get("content") or []
            texts: list[str] = []
            for p in parts:
                if isinstance(p, dict) and p.get("type") == "text" and "text" in p:
                    texts.append(str(p["text"]))
            text = "".join(texts) if texts else str(parts)
        except Exception:  # noqa: BLE001
            text = str(data)

        usage = data.get("usage") or {}
        input_tokens = int(usage.get("input_tokens", 0))
        output_tokens = int(usage.get("output_tokens", 0))
        cost = None

        self._track_usage(model, input_tokens, output_tokens, cost)

        return ChatResult(
            model=model,
            text=text,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost=cost,
            raw=data,
            latency_s=latency,
        )

    # --- Cohere ---

    def _chat_cohere(self, cfg, model: ModelInfo, prompt: str, temperature: float) -> ChatResult:
        base_url = cfg.base_url or "https://api.cohere.com/v1"
        url = base_url.rstrip("/") + "/chat"

        headers = {
            "Authorization": f"Bearer {cfg.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": model.model_id,
            "message": prompt,
            "temperature": float(temperature),
        }

        t0 = time.time()
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=60)
            latency = time.time() - t0
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:  # noqa: BLE001
            return ChatResult(
                model=model,
                text=f"[BŁĄD COHERE] {exc}",
                error="http_error",
            )

        text = ""
        try:
            # Starsze API: odpowiedź w polu "text"
            if "text" in data:
                text = str(data["text"])
            # Nowsze schematy mogłyby mieć message/content
            elif "message" in data:
                msg = data.get("message") or {}
                content = msg.get("content") or []
                texts: list[str] = []
                for c in content:
                    if isinstance(c, dict) and "text" in c:
                        texts.append(str(c["text"]))
                text = "".join(texts) if texts else str(msg)
            else:
                text = str(data)
        except Exception:  # noqa: BLE001
            text = str(data)

        meta = data.get("meta") or {}
        tokens = meta.get("tokens") or {}
        input_tokens = int(tokens.get("input_tokens", 0))
        output_tokens = int(tokens.get("output_tokens", 0))
        cost = None

        self._track_usage(model, input_tokens, output_tokens, cost)

        return ChatResult(
            model=model,
            text=text,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost=cost,
            raw=data,
            latency_s=latency,
        )

    # --- Helpers ---

    def _track_usage(self, model: ModelInfo, input_tokens: int, output_tokens: int, cost: Optional[float]) -> None:
        if self.tracker is None:
            return
        try:
            self.tracker.register_call(
                provider_id=model.provider_id,
                model_id=model.model_id,
                input_tokens=int(input_tokens),
                output_tokens=int(output_tokens),
                cost=cost,
            )
        except Exception:
            # nie przerywamy głównego flow przez problemy z trackerem
            pass
