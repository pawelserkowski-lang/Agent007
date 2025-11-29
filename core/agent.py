import threading
import logging
import os
import re
import importlib
from typing import Dict, Iterable, List, Optional

from kivy.clock import Clock


class Agent:
    _DEFAULT_PRIORITY_FAMILIES: tuple[str, ...] = (
        "gemini-1.5-pro",
        "gemini-1.5-flash",
        "gemini-pro",
    )

    def __init__(self, db_manager, app_instance, genai_client=None, image_loader=None):
        self.db = db_manager
        self.app = app_instance
        self.base_prompt = """
        ROLE: Gemini Code Assist (CLI Backend).
        TASK: High-performance code generation & Visual Analysis.
        RULES:
        1. Markdown for code.
        2. Analyze provided files/images thoroughly.
        3. Production-ready output.
        """
        self.cached_model: Optional[str] = None
        self._genai = genai_client
        self._pil_image = image_loader
        self._dependencies_ready = genai_client is not None and image_loader is not None

        self._family_suffix_pattern = re.compile(r"-(latest|\d+)$")
        self._version_pattern = re.compile(r"(\d+)$")
        self._html_block_pattern = re.compile(r"```html(.*?)```", re.DOTALL)

    def _ensure_dependencies(self) -> bool:
        """Load optional dependencies only once and keep imports test-friendly."""
        if self._dependencies_ready:
            return True

        if not importlib.util.find_spec("google.generativeai"):
            logging.critical("Brak bibliotek: google-generativeai!")
            return False
        if not importlib.util.find_spec("PIL"):
            logging.critical("Brak biblioteki Pillow!")
            return False

        import google.generativeai as genai  # pylint: disable=import-error
        from PIL import Image as PIL_Image  # pylint: disable=import-error

        self._genai = genai
        self._pil_image = PIL_Image
        self._dependencies_ready = True
        return True

    def discover_best_model(self, api_key: str) -> Optional[str]:
        """Pobiera listę i wybiera najnowszy dostępny model."""
        if not self._ensure_dependencies() or not api_key:
            logging.warning("Brak klucza API podczas wyszukiwania modelu")
            return None

        try:
            self._genai.configure(api_key=api_key)
            raw_models = self._available_generate_models(self._genai.list_models())
        except Exception as exc:  # pragma: no cover - defensive logging
            logging.error("Model Discovery Error: %s", exc)
            return None

        if not raw_models:
            logging.error("Brak modeli generateContent zwróconych przez API")
            return None

        self._cache_available_models(raw_models)
        family_latest = self._select_latest_by_family(raw_models)
        selected = self._choose_model(family_latest)
        self.cached_model = selected
        return selected

    def _family_name(self, model_name: str) -> str:
        return self._family_suffix_pattern.sub("", model_name)

    def _version_marker(self, model_name: str) -> tuple[int, int]:
        if model_name.endswith("latest"):
            return (1, 0)
        match = self._version_pattern.search(model_name)
        version = int(match.group(1)) if match else 0
        return (0, version)

    def _is_newer(self, candidate: str, current: str) -> bool:
        """Porównuje dwa warianty w ramach tej samej rodziny."""
        candidate_marker = self._version_marker(candidate)
        current_marker = self._version_marker(current)
        return candidate_marker > current_marker

    def _select_latest_by_family(self, models: Iterable[str]) -> Dict[str, str]:
        """Keep only the newest entry per family for faster lookup."""
        family_latest: Dict[str, str] = {}
        for model_name in models:
            family = self._family_name(model_name)
            current = family_latest.get(family)
            if not current or self._is_newer(model_name, current):
                family_latest[family] = model_name
        return family_latest

    def _choose_model(self, family_latest: Dict[str, str]) -> Optional[str]:
        if not family_latest:
            return None

        for family in self._priority_families():
            if family in family_latest:
                logging.info("[DISCOVERY] Wybrano priorytetowy model: %s", family_latest[family])
                return family_latest[family]

        fallback_family = min(family_latest)
        fallback = family_latest[fallback_family]
        logging.info("[DISCOVERY] Wybrano model zapasowy (%s): %s", fallback_family, fallback)
        return fallback

    def _priority_families(self) -> List[str]:
        """Return the configured model priority list with safe defaults."""
        custom_priority = getattr(self.app, "model_priority_families", None)
        if custom_priority:
            normalized = self._normalize_priority(custom_priority)
            if normalized:
                return normalized
        return list(self._DEFAULT_PRIORITY_FAMILIES)

    @classmethod
    def _normalize_priority(cls, families: Iterable[str]) -> List[str]:
        """Strip whitespace, drop blanks, and deduplicate while preserving order."""
        seen = set()
        normalized: List[str] = []
        for name in families:
            cleaned = name.strip()
            if not cleaned or cleaned in seen:
                continue
            seen.add(cleaned)
            normalized.append(cleaned)
        return normalized or list(cls._DEFAULT_PRIORITY_FAMILIES)

    def _available_generate_models(self, raw_models: Iterable) -> List[str]:
        available = []
        for model in raw_models:
            methods = getattr(model, "supported_generation_methods", ())
            if "generateContent" not in methods:
                continue
            available.append(model.name.removeprefix("models/"))
        return available

    def _cache_available_models(self, raw_models: List[str]) -> None:
        try:
            self.app.available_models = sorted(raw_models)
        except Exception:  # pragma: no cover - UI safety
            pass
        logging.info("[DISCOVERY] Dostępne modele (%d): %s", len(raw_models), ", ".join(raw_models))

    def _build_system_prompt(self):
        instructions = [self.base_prompt]
        toggles = (
            (self.app.param_polish, "LANG: Polish."),
            (self.app.param_comments, "Add docstrings."),
            (self.app.param_expert, "MODE: Expert."),
            (self.app.param_concise, "MODE: Concise."),
            (self.app.param_stackoverflow, "STYLE: StackOverflow."),
        )
        instructions.extend(text for enabled, text in toggles if enabled)

        custom_text = self.app.param_custom_text.strip()
        if custom_text:
            instructions.append(f"\nUSER_OVERRIDES:\n{custom_text}\n")
        return "\n".join(instructions)

    def _check_and_save_html(self, text):
        if not self.app.param_auto_save_files:
            return None

        match = self._html_block_pattern.search(text)
        if not match:
            return None

        html_content = match.group(1).strip()
        preview_dir = "preview"
        os.makedirs(preview_dir, exist_ok=True)
        file_path = os.path.join(preview_dir, "index.html")
        try:
            with open(file_path, "w", encoding="utf-8") as file_handle:
                file_handle.write(html_content)
            logging.info("HTML saved.")
            return file_path
        except Exception as exc:  # pragma: no cover - filesystem edge
            logging.error("Save Error: %s", exc)
            return None

    def send_message(self, session_id, message, file_contents, images, callback_success, callback_error):
        if not self.app.api_key:
            callback_error("Brak klucza API!")
            return

        def _thread_target():
            if not self._ensure_dependencies():
                Clock.schedule_once(lambda dt: callback_error("Brak bibliotek"), 0)
                return

            target_model = self.cached_model if self.cached_model else "gemini-1.5-pro"
            model_identifier = target_model if target_model.startswith("models/") else f"models/{target_model}"
            logging.info(
                "[ENGINE] Target=%s search=%s temp=%.2f tokens=%d files=%d images=%d",
                model_identifier,
                self.app.use_google_search,
                self.app.param_temperature,
                int(self.app.param_max_tokens),
                len(file_contents) if file_contents else 0,
                len(images) if images else 0,
            )

            tools = [{"google_search_retrieval": {}}] if self.app.use_google_search else []
            safety_settings = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            ]
            gen_config = {
                "temperature": self.app.param_temperature,
                "max_output_tokens": int(self.app.param_max_tokens),
                "top_p": 0.95,
                "top_k": 40,
            }

            full_text_content = self._build_user_payload(message, file_contents)
            image_paths = images or []
            db_content = full_text_content
            if image_paths:
                db_content += f"\n\n[ATTACHED {len(image_paths)} IMAGES]"
            self.db.add_message(session_id, "user", db_content)

            try:
                self._genai.configure(api_key=self.app.api_key)
                model = self._genai.GenerativeModel(
                    model_name=model_identifier,
                    system_instruction=self._build_system_prompt(),
                    generation_config=gen_config,
                    safety_settings=safety_settings,
                    tools=tools,
                )

                content_parts = self._build_content_parts(full_text_content, image_paths)
                chat_history = self._build_history(session_id)

                chat = model.start_chat(history=chat_history)
                response = chat.send_message(content_parts)
                bot_reply = response.text

                preview_file = self._check_and_save_html(bot_reply)
                if preview_file:
                    Clock.schedule_once(lambda dt: self.app.open_web_preview(preview_file), 0)

                self.db.add_message(session_id, "assistant", bot_reply)
                Clock.schedule_once(lambda dt: callback_success(bot_reply), 0)

            except Exception as exc:  # pragma: no cover - runtime network issues
                err_msg = str(exc)
                logging.error("Gemini Error: %s", err_msg)
                Clock.schedule_once(lambda dt: callback_error(f"Błąd API: {err_msg}"), 0)

        threading.Thread(target=_thread_target, daemon=True).start()

    def _build_user_payload(self, message: str, file_contents) -> str:
        parts = [message]
        if file_contents:
            parts.append("\n\n[CONTEXT FILES]:\n")
            for fname, fcontent in file_contents.items():
                parts.append(f"--- FILE: {fname} ---\n{fcontent}\n")
        return "".join(parts)

    def _build_content_parts(self, full_text_content: str, images: List[str]):
        content_parts = [full_text_content]
        for img_path in images:
            try:
                content_parts.append(self._pil_image.open(img_path))
            except Exception:
                logging.warning("Nie udało się otworzyć obrazu: %s", img_path)
        return content_parts

    def _build_history(self, session_id):
        history_data = self.db.get_context_messages(session_id, 10)
        return [
            {"role": "user" if msg["role"] == "user" else "model", "parts": [msg["content"]]}
            for msg in history_data[:-1]
        ]
