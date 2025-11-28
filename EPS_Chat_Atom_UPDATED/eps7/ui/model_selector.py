
from __future__ import annotations
import customtkinter as ctk
from typing import Callable, Dict, List
from ..model_manager.manager import get_models, group_by_provider
from ..model_manager.schemas import ModelInfo

_PROVIDER_COLORS = {
    "openai": "#22c55e",
    "gemini": "#0ea5e9",
    "anthropic": "#f97316",
    "mistral": "#eab308",
    "cohere": "#a855f7",
    "groq": "#f43f5e",
    "xai": "#e11d48",
    "together": "#10b981",
    "deepseek": "#38bdf8",
    "bedrock": "#8b5cf6",
}

_CAPABILITY_ICONS = {
    "text": "🧠",
    "chat": "💬",
    "code": "⌨️",
    "vision": "👁️",
    "audio": "🎙️",
    "files": "📂",
    "realtime": "⚡",
    "embeddings": "🧩",
}

class ModelSelector(ctk.CTkFrame):
    """Sidebar widget that lists all models grouped by provider and allows multi-selection.

    on_selection_changed(selected: list[ModelInfo]) is called whenever user changes selection.
    """

    def __init__(
        self,
        parent,
        on_selection_changed: Callable[[List[ModelInfo]], None] | None = None,
        **kwargs,
    ) -> None:
        super().__init__(parent, fg_color="#e5f2ff", **kwargs)
        self.on_selection_changed = on_selection_changed
        self.models: Dict[str, ModelInfo] = {}
        self._checks: Dict[str, ctk.CTkCheckBox] = {}

        header = ctk.CTkLabel(self, text="MODELE", font=("Segoe UI", 14, "bold"))
        header.pack(pady=(8, 4))

        self.filter_frame = ctk.CTkFrame(self, fg_color="#e5f2ff")
        self.filter_frame.pack(fill="x", padx=6)

        self.filter_capability_var = ctk.StringVar(value="all")
        for cap_id, cap_label in [
            ("all", "Wszystkie"),
            ("text", "Tekst"),
            ("vision", "Obraz"),
            ("audio", "Audio"),
            ("files", "Pliki"),
        ]:
            btn = ctk.CTkRadioButton(
                self.filter_frame,
                text=cap_label,
                value=cap_id,
                variable=self.filter_capability_var,
                command=self._rebuild_model_list,
                fg_color="#3b82f6",
                hover_color="#1e293b",
                border_color="#93c5fd",
                text_color="#0f172a",
                font=("Segoe UI", 11),
            )
            btn.pack(side="left", padx=2, pady=4)

        self.scroll = ctk.CTkScrollableFrame(self, fg_color="#e5f2ff", width=260)
        self.scroll.pack(fill="both", expand=True, padx=6, pady=(4, 8))

        refresh_btn = ctk.CTkButton(
            self,
            text="Odśwież listę modeli",
            command=self.refresh_models,
            fg_color="#3b82f6",
            hover_color="#2563eb",
            corner_radius=10,
        )
        refresh_btn.pack(fill="x", padx=8, pady=(0, 8))

        self.refresh_models(initial=True)

    def refresh_models(self, initial: bool = False) -> None:
        self.models.clear()
        self._checks.clear()
        for child in self.scroll.winfo_children():
            child.destroy()

        models = get_models(force_refresh=not initial)
        grouped = group_by_provider(models)

        for provider_id, items in grouped.items():
            section_color = _PROVIDER_COLORS.get(provider_id, "#4b5563")
            title = ctk.CTkLabel(
                self.scroll,
                text=f"{items[0].provider_id.upper()}  ({len(items)})",
                font=("Segoe UI", 12, "bold"),
                text_color=section_color,
            )
            title.pack(anchor="w", pady=(8, 2), padx=4)

            for m in sorted(items, key=lambda x: x.display_name):
                model_key = f"{m.provider_id}:{m.model_id}"
                self.models[model_key] = m

                cap_icons = "".join(_CAPABILITY_ICONS.get(c, "") for c in m.capabilities)
                label = f"{cap_icons} {m.display_name}" if cap_icons else m.display_name

                var = ctk.BooleanVar(value=False)
                chk = ctk.CTkCheckBox(
                    self.scroll,
                    text=label,
                    variable=var,
                    command=self._on_check_changed,
                    fg_color=section_color,
                    hover_color="#22d3ee",
                    border_color="#93c5fd",
                    text_color="#0f172a",
                    font=("Segoe UI", 11),
                )
                chk._model_key = model_key  # type: ignore[attr-defined]
                chk._var = var  # type: ignore[attr-defined]
                chk.pack(anchor="w", padx=12, pady=2)
                self._checks[model_key] = chk

        self._rebuild_model_list()

    def _on_check_changed(self) -> None:
        if not self.on_selection_changed:
            return
        selected: list[ModelInfo] = []
        for model_key, chk in self._checks.items():
            if getattr(chk, "_var").get():  # type: ignore[attr-defined]
                m = self.models.get(model_key)
                if m:
                    selected.append(m)
        self.on_selection_changed(selected)

    def _rebuild_model_list(self) -> None:
        cap_filter = self.filter_capability_var.get()
        for model_key, chk in self._checks.items():
            m = self.models.get(model_key)
            if not m:
                continue
            if cap_filter == "all" or cap_filter in m.capabilities:
                chk.pack(anchor="w", padx=12, pady=2)
            else:
                chk.pack_forget()
