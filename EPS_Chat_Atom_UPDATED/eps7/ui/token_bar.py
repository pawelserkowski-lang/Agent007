
from __future__ import annotations
import customtkinter as ctk
from ..tokens import TokenTracker

class TokenBar(ctk.CTkFrame):
    """Small bar displaying total token usage and cost for current session."""

    def __init__(self, parent, tracker: TokenTracker, **kwargs) -> None:
        super().__init__(parent, fg_color="#e5f2ff", **kwargs)
        self.tracker = tracker

        self.label = ctk.CTkLabel(
            self,
            text="Tokens: 0 in / 0 out | Cost: 0.0000",
            font=("Consolas", 11),
            text_color="#66ddff",
        )
        self.label.pack(side="left", padx=8, pady=4)

        self.refresh_button = ctk.CTkButton(
            self,
            text="⟳",
            width=26,
            height=20,
            command=self.refresh,
            fg_color="#02101f",
            hover_color="#04324a",
        )
        self.refresh_button.pack(side="right", padx=4, pady=4)

        self.refresh()

    def refresh(self) -> None:
        total = self.tracker.totals()
        self.label.configure(
            text=f"Tokens: {total.input_tokens} in / {total.output_tokens} out | Cost: {total.cost:.4f}"
        )

    def auto_refresh(self, interval_ms: int = 1500) -> None:
        self.refresh()
        self.after(interval_ms, lambda: self.auto_refresh(interval_ms))
