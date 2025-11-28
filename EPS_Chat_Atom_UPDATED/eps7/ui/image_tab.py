
from __future__ import annotations
import customtkinter as ctk
from typing import List
from PIL import Image, ImageTk  # type: ignore[import]

class ImageTab(ctk.CTkFrame):
    """Karta galerii obrazów.

    Umożliwia:
    - dodawanie miniaturek obrazów,
    - kliknięcie w miniaturę aby otworzyć powiększenie.
    """

    def __init__(self, parent, **kwargs) -> None:
        super().__init__(parent, fg_color="#e5f2ff", **kwargs)
        self._image_refs: List[ImageTk.PhotoImage] = []

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.scroll = ctk.CTkScrollableFrame(self, fg_color="#e5f2ff")
        self.scroll.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)

    def add_image(self, image_path: str, label: str | None = None) -> None:
        wrapper = ctk.CTkFrame(self.scroll, fg_color="#e5f2ff")
        wrapper.pack(anchor="w", padx=4, pady=4)

        if label:
            cap = ctk.CTkLabel(
                wrapper,
                text=label,
                font=("Segoe UI", 10, "bold"),
                text_color="#38bdf8",
            )
            cap.pack(anchor="w")

        try:
            img = Image.open(image_path)
            img.thumbnail((260, 260))
            tk_img = ImageTk.PhotoImage(img)
            self._image_refs.append(tk_img)
            btn = ctk.CTkButton(
                wrapper,
                image=tk_img,
                text="",
                width=260,
                height=260,
                fg_color="#e5f2ff",
                hover_color="#3b82f6",
                command=lambda p=image_path: self._open_full(p),
            )
            btn.pack(anchor="w")
        except Exception as exc:  # noqa: BLE001
            err = ctk.CTkLabel(
                wrapper,
                text=f"[BŁĄD PODGLĄDU] {exc}",
                text_color="#f97316",
            )
            err.pack(anchor="w")

    def _open_full(self, image_path: str) -> None:
        win = ctk.CTkToplevel(self)
        win.title(image_path)
        frame = ctk.CTkFrame(win, fg_color="#e5f2ff")
        frame.pack(fill="both", expand=True, padx=8, pady=8)
        try:
            img = Image.open(image_path)
            img.thumbnail((900, 900))
            tk_img = ImageTk.PhotoImage(img)
            self._image_refs.append(tk_img)
            lbl = ctk.CTkLabel(frame, image=tk_img, text="")
            lbl.pack()
        except Exception as exc:  # noqa: BLE001
            err = ctk.CTkLabel(
                frame,
                text=f"[BŁĄD PODGLĄDU] {exc}",
                text_color="#f97316",
            )
            err.pack()
