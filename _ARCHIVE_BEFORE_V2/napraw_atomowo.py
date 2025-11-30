import os

# 1. NOWA TREŚĆ DLA core/model_manager.py
# Ten kod po prostu zwraca nazwę Twojego modelu, ignorując API Google przy wyborze.
NEW_MODEL_MANAGER = """
import google.generativeai as genai
import os

def get_best_model(api_key=None):
    # WYMUSZENIE MODELU NA SZTYWNO
    print("[ModelManager] WYMUSZONO MODEL: gemini-3-pro-preview")
    return "models/gemini-3-pro-preview"
"""

# 2. NOWA TREŚĆ DLA core/agent.py
# To jest Twój oryginalny kod, ale z usuniętą linią powodującą błąd (tools=...)
# i wymuszonym modelem.
NEW_AGENT_CODE = """
import threading
import logging
import os
import re
import importlib
from typing import Dict, Iterable, List, Optional

from kivy.clock import Clock


class Agent:
    _DEFAULT_PRIORITY_FAMILIES: tuple[str, ...] = (
        "gemini-3-pro-preview",
        "gemini-1.5-pro",
    )

    def __init__(self, db_manager, app_instance, genai_client=None, image_loader=None):
        self.db = db_manager
        self.app = app_instance
        self.base_prompt = \"\"\"
        ROLE: Gemini Code Assist (CLI Backend).
        TASK: High-performance code generation & Visual Analysis.
        RULES:
        1. Markdown for code.
        2. Analyze provided files/images thoroughly.
        3. Production-ready output.
        \"\"\"
        self.cached_model: Optional[str] = "gemini-3-pro-preview"
        self._genai = genai_client
        self._pil_image = image_loader
        self._dependencies_ready = genai_client is not None and image_loader is not None

        self._family_suffix_pattern = re.compile(r"-(latest|\d+)$")
        self._version_pattern = re.compile(r"(\d+)$")
        self._html_block_pattern = re.compile(r"```html(.*?)```", re.DOTALL)

    def _ensure_dependencies(self) -> bool:
        if self._dependencies_ready:
            return True

        if not importlib.util.find_spec("google.generativeai"):
            logging.critical("Brak bibliotek: google-generativeai!")
            return False
        if not importlib.util.find_spec("PIL"):
            logging.critical("Brak biblioteki Pillow!")
            return False

        import google.generativeai as genai
        from PIL import Image as PIL_Image

        self._genai = genai
        self._pil_image = PIL_Image
        self._dependencies_ready = True
        return True

    def discover_best_model(self, api_key: str) -> Optional[str]:
        # Zwracamy od razu nasz model, pomijamy logikę
        return "gemini-3-pro-preview"

    def _family_name(self, model_name: str) -> str:
        return self._family_suffix_pattern.sub("", model_name)

    def _version_marker(self, model_name: str) -> tuple[int, int]:
        return (0, 0)

    def _is_newer(self, candidate: str, current: str) -> bool:
        return False

    def _select_latest_by_family(self, models: Iterable[str]) -> Dict[str, str]:
        return {}

    def _choose_model(self, family_latest: Dict[str, str]) -> Optional[str]:
        return "gemini-3-pro-preview"

    def _priority_families(self) -> List[str]:
        return ["gemini-3-pro-preview"]

    @classmethod
    def _normalize_priority(cls, families: Iterable[str]) -> List[str]:
        return ["gemini-3-pro-preview"]

    def _available_generate_models(self, raw_models: Iterable) -> List[str]:
        return ["gemini-3-pro-preview"]

    def _cache_available_models(self, raw_models: List[str]) -> None:
        pass

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
            instructions.append(f"\\nUSER_OVERRIDES:\\n{custom_text}\\n")
        return "\\n".join(instructions)

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
        except Exception as exc:
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

            # WYMUSZENIE MODELU
            target_model = "gemini-3-pro-preview"
            
            logging.info(
                "[ENGINE] Target=%s search=DISABLED temp=%.2f tokens=%d",