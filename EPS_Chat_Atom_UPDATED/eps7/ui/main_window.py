
from __future__ import annotations
import customtkinter as ctk
from typing import List
from ..tokens import TokenTracker
from ..model_manager.schemas import ModelInfo
from .token_bar import TokenBar
from .model_selector import ModelSelector

class EPSMainWindow(ctk.CTk):
    """Minimal EPS 7.0 window showing:
    - sidebar z wyborem modeli (multi-model)
    - pasek tokenów
    - prosty obszar czatu (placeholder)
    To jest referencyjna integracja; możesz przenieść elementy do swojej aplikacji.
    """

    def __init__(self) -> None:
        super().__init__()
        self.title("EPS 7.0 – Multi‑Model Console")
        self.geometry("1200x720")

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        self.tracker = TokenTracker()
        self.selected_models: List[ModelInfo] = []

        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)

        self.token_bar = TokenBar(self, tracker=self.tracker)
        self.token_bar.grid(row=0, column=0, columnspan=2, sticky="ew")

        self.sidebar = ModelSelector(self, on_selection_changed=self.on_models_changed, width=280)
        self.sidebar.grid(row=1, column=0, sticky="ns")

        self.chat_frame = ctk.CTkFrame(self, fg_color="#e5f2ff")
        self.chat_frame.grid(row=1, column=1, sticky="nsew")
        self.chat_frame.grid_rowconfigure(0, weight=1)
        self.chat_frame.grid_columnconfigure(0, weight=1)

        self.chat_log = ctk.CTkTextbox(self.chat_frame, wrap="word")
        self.chat_log.grid(row=0, column=0, sticky="nsew", padx=12, pady=(12, 4))

        self.entry = ctk.CTkEntry(
            self.chat_frame,
            placeholder_text="Wpisz wiadomość (tu później podepniesz wywołania do modeli)...",
        )
        self.entry.grid(row=1, column=0, sticky="ew", padx=12, pady=(4, 12))
        self.entry.bind("<Return>", self._on_enter)

        self.token_bar.auto_refresh()

    def on_models_changed(self, models: list[ModelInfo]) -> None:
        self.selected_models = models
        names = ", ".join(f"{m.provider_id}:{m.model_id}" for m in models) or "— brak —"
        self.chat_log.insert("end", f"[SYSTEM] Wybrane modele: {names}\n")
        self.chat_log.see("end")

    def _on_enter(self, event=None) -> None:
        text = self.entry.get().strip()
        if not text:
            return
        self.chat_log.insert("end", f"[TY] {text}\n")
        self.chat_log.see("end")
        self.entry.delete(0, "end")
        if not self.selected_models:
            self.chat_log.insert("end", "[SYSTEM] Brak wybranych modeli – wybierz w panelu po lewej.\n")
            self.chat_log.see("end")
            return
        for m in self.selected_models:
            self.chat_log.insert(
                "end",
                f"[{m.provider_id}:{m.model_id}] (tu podłączysz wywołanie API i aktualizację tokenów)\n",
            )
        self.chat_log.see("end")

if __name__ == "__main__":
    app = EPSMainWindow()
    app.mainloop()
