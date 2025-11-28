
from __future__ import annotations
import customtkinter as ctk

class LogTab(ctk.CTkFrame):
    """Karta logów systemowych (debug, ZIP, modele, itp.)."""

    def __init__(self, parent, **kwargs) -> None:
        super().__init__(parent, fg_color="#e5f2ff", **kwargs)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.text = ctk.CTkTextbox(self, wrap="word")
        self.text.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)

    def log(self, msg: str) -> None:
        self.text.insert("end", msg + "\n")
        self.text.see("end")
