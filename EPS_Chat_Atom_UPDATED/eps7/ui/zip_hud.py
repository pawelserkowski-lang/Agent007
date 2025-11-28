
from __future__ import annotations
import customtkinter as ctk
import threading
import zipfile
import os
from typing import Optional, Callable

class ZipHUD(ctk.CTkFrame):
    """HUD postępu rozpakowywania ZIP z paskiem i opisem.

    Wywołanie:
        hud.extract_zip(path, target_dir, on_done=callback)
    """

    def __init__(self, parent, **kwargs) -> None:
        super().__init__(parent, fg_color="#e5f2ff", **kwargs)
        self.label = ctk.CTkLabel(
            self,
            text="ZIP: —",
            font=("Segoe UI", 11),
            text_color="#0f172a",
        )
        self.label.pack(anchor="w", padx=8, pady=(6, 2))

        self.progress = ctk.CTkProgressBar(self)
        self.progress.set(0.0)
        self.progress.pack(fill="x", padx=8, pady=(0, 6))

        self._on_done: Optional[Callable[[str, str], None]] = None
        self._busy = False

    def extract_zip(self, zip_path: str, target_dir: str, on_done: Optional[Callable[[str, str], None]] = None) -> None:
        if self._busy:
            return
        self._busy = True
        self._on_done = on_done
        self.label.configure(text=f"ZIP: {os.path.basename(zip_path)} – przygotowanie…")
        self.progress.set(0.0)
        self.place(relx=1.0, rely=1.0, anchor="se", x=-16, y=-16)

        t = threading.Thread(target=self._worker, args=(zip_path, target_dir), daemon=True)
        t.start()

    def _worker(self, zip_path: str, target_dir: str) -> None:
        try:
            with zipfile.ZipFile(zip_path, "r") as zf:
                members = zf.infolist()
                total = len(members) or 1
                os.makedirs(target_dir, exist_ok=True)
                for idx, member in enumerate(members, start=1):
                    zf.extract(member, path=target_dir)
                    progress = idx / total
                    self.after(
                        0,
                        lambda p=progress, name=member.filename: self._update_progress(p, name),
                    )
        except Exception as exc:  # noqa: BLE001
            self.after(0, lambda e=exc: self._fail(e, zip_path, target_dir))
            return
        self.after(0, lambda: self._complete(zip_path, target_dir))

    def _update_progress(self, value: float, filename: str) -> None:
        self.progress.set(value)
        self.label.configure(
            text=f"Rozpakowywanie… {int(value * 100)}%  •  {filename}",
        )

    def _complete(self, zip_path: str, target_dir: str) -> None:
        self._busy = False
        self.progress.set(1.0)
        self.label.configure(
            text=f"Zakończono: {os.path.basename(zip_path)} → {target_dir}",
        )
        if self._on_done:
            self._on_done(zip_path, target_dir)

    def _fail(self, exc: Exception, zip_path: str, target_dir: str) -> None:
        self._busy = False
        self.progress.set(0.0)
        self.label.configure(
            text=f"BŁĄD przy {os.path.basename(zip_path)}: {exc}",
        )
