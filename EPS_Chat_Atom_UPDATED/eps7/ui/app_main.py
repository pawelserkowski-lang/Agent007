
from __future__ import annotations

import os
from pathlib import Path
from typing import List

import customtkinter as ctk
from tkinter import filedialog  # type: ignore[import]
from PIL import Image, ImageTk  # type: ignore[import]

from ..tokens import TokenTracker
from ..model_manager.schemas import ModelInfo
from ..model_manager.manager import get_models
from ..chat_engine import ChatEngine
from .token_bar import TokenBar
from .model_selector import ModelSelector
from .chat_tab import ChatTab
from .image_tab import ImageTab
from .project_tab import ProjectTab
from .log_tab import LogTab
from .zip_hud import ZipHUD
from .compare_tab import CompareTab
from .chain_tab import ChainTab
from .help_tab import HelpTab


class EPSChatAtomApp(ctk.CTk):
    """EPS Chat Atom 7.x – okno główne:

    - lewy panel: MODELE + przycisk ZIP,
    - górny pasek: TokenBar,
    - główny obszar: karty:
        - Chat (standardowy czat + autokorekta/tłumaczenie),
        - Porównanie (równoległe odpowiedzi wielu modeli + cross-context),
        - Łańcuch (pipeline modeli: A -> B -> C),
        - Obrazy (galeria),
        - Projekty (scenariusze eksperymentów Porównania),
        - Log (log systemowy),
        - Pomoc (skrótowe objaśnienia funkcji).
    """

    def __init__(self) -> None:
        super().__init__()
        self.title("EPS Chat Atom 7.x")
        self.geometry("1400x840")

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        self._icon_ref: ImageTk.PhotoImage | None = None
        self._load_window_icon()

        self.tracker = TokenTracker()
        self.chat_engine = ChatEngine(tracker=self.tracker)
        self.selected_models: List[ModelInfo] = []

        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)

        # Pasek tokenów
        self.token_bar = TokenBar(self, tracker=self.tracker)
        self.token_bar.grid(row=0, column=0, columnspan=2, sticky="ew")
        self.token_bar.auto_refresh()

        # Lewy panel – przyciski narzędzi + MODELE
        self.sidebar = ctk.CTkFrame(self, fg_color="#e5f2ff")
        self.sidebar.grid(row=1, column=0, sticky="ns")
        self.sidebar.grid_rowconfigure(1, weight=1)

        top_buttons = ctk.CTkFrame(self.sidebar, fg_color="#e5f2ff")
        top_buttons.grid(row=0, column=0, sticky="ew", padx=6, pady=(6, 0))
        top_buttons.grid_columnconfigure(0, weight=1)

        zip_btn = ctk.CTkButton(
            top_buttons,
            text="📦 Otwórz ZIP…",
            command=self._choose_zip,
            fg_color="#3b82f6",
            hover_color="#2563eb",
        )
        zip_btn.grid(row=0, column=0, sticky="ew", pady=4)

        self.model_selector = ModelSelector(
            self.sidebar,
            on_selection_changed=self._on_models_changed,
            width=260,
        )
        self.model_selector.grid(row=1, column=0, sticky="ns")

        # Główne taby
        self.tabview = ctk.CTkTabview(self, fg_color="#e5f2ff", segmented_button_fg_color="#e5f2ff")
        self.tabview.grid(row=1, column=1, sticky="nsew", padx=8, pady=8)

        chat_container = self.tabview.add("Chat")
        compare_container = self.tabview.add("Porównanie")
        chain_container = self.tabview.add("Łańcuch")
        images_container = self.tabview.add("Obrazy")
        projects_container = self.tabview.add("Projekty")
        log_container = self.tabview.add("Log")
        help_container = self.tabview.add("Pomoc")

        # Chat – standardowy tryb rozmowy + narzędzia wejściowe
        self.chat_tab = ChatTab(
            chat_container,
            get_selected_models=self._get_selected_models,
            on_send=self._handle_chat_send,
            chat_engine=self.chat_engine,
            log_fn=self._log,
        )
        self.chat_tab.pack(fill="both", expand=True)

        # Porównanie – równoległe odpowiedzi
        self.compare_tab = CompareTab(
            compare_container,
            get_selected_models=self._get_selected_models,
            chat_engine=self.chat_engine,
            log_fn=self._log,
        )
        self.compare_tab.pack(fill="both", expand=True)

        # Łańcuch – pipeline modeli
        self.chain_tab = ChainTab(
            chain_container,
            get_selected_models=self._get_selected_models,
            chat_engine=self.chat_engine,
            log_fn=self._log,
        )
        self.chain_tab.pack(fill="both", expand=True)

        # Galeria obrazów
        self.images_tab = ImageTab(images_container)
        self.images_tab.pack(fill="both", expand=True)

        # Projekty – scenariusze Porównania
        self.projects_tab = ProjectTab(
            projects_container,
            compare_tab=self.compare_tab,
            log_fn=self._log,
        )
        self.projects_tab.grid(row=0, column=0, sticky="nsew")

        # Log
        self.log_tab = LogTab(log_container)
        self.log_tab.pack(fill="both", expand=True)

        # Pomoc
        self.help_tab = HelpTab(help_container)
        self.help_tab.pack(fill="both", expand=True)

        # HUD ZIP
        self.zip_hud = ZipHUD(self)

        # Wstępne pobranie listy modeli (do cache)
        self._warmup_models()

    # ICON

    def _load_window_icon(self) -> None:
        try:
            assets = Path(__file__).resolve().parent.parent / "assets"
            icon_path = assets / "ikona.webp"
            if icon_path.exists():
                img = Image.open(icon_path)
                img.thumbnail((64, 64))
                self._icon_ref = ImageTk.PhotoImage(img)
                self.iconphoto(False, self._icon_ref)
        except Exception:
            pass

    # MODEL MANAGEMENT

    def _warmup_models(self) -> None:
        try:
            models = get_models(force_refresh=False)
            self._log(f"Załadowano {len(models)} modeli z cache/API.")
        except Exception as exc:  # noqa: BLE001
            self._log(f"[BŁĄD] Nie udało się pobrać modeli: {exc}")

    def _get_selected_models(self) -> List[ModelInfo]:
        return list(self.selected_models)

    def _on_models_changed(self, models: List[ModelInfo]) -> None:
        self.selected_models = models
        names = ", ".join(f"{m.provider_id}:{m.model_id}" for m in models) or "— brak —"
        self.chat_tab.add_system_message(f"Wybrane modele: {names}")
        self.chat_tab.update_models_hint()
        self._log(f"[MODELE] Aktualny wybór: {names}")

    # CHAT (standardowy tryb)

    def _handle_chat_send(self, text: str, models: List[ModelInfo]) -> None:
        if not models:
            self.chat_tab.add_system_message("Brak wybranych modeli – wybierz w panelu MODELE.")
            return
        for m in models:
            label = f"{m.provider_id}:{m.model_id}"

            def on_finished(result, label=label) -> None:
                self.after(0, lambda r=result, l=label: self._handle_chat_result(r, l))

            self.chat_engine.chat_async(m, text, on_finished=on_finished, stream=False)
        self._log(f"[CHAT] Wysłano prompt do {len(models)} modeli.")

    def _handle_chat_result(self, result, label: str) -> None:
        if result.error:
            self.chat_tab.add_model_message(label, f"[BŁĄD] {result.text}")
        else:
            self.chat_tab.add_model_message(label, result.text)

    # ZIP HUD

    def _choose_zip(self) -> None:
        path = filedialog.askopenfilename(
            title="Wybierz plik ZIP",
            filetypes=[("Archiwa ZIP", "*.zip"), ("Wszystkie pliki", "*.*")],
        )
        if not path:
            return
        target_dir = os.path.join(str(Path.home()), "EPS_ZIP_CACHE")
        self._log(f"[ZIP] Rozpakowywanie {path} do {target_dir}")
        self.zip_hud.extract_zip(path, target_dir, on_done=self._on_zip_done)

    def _on_zip_done(self, zip_path: str, target_dir: str) -> None:
        # Log completion
        self._log(f"[ZIP] Zakończono: {zip_path} → {target_dir}")
        # After extraction, attempt to load any images from the archive into the gallery.
        try:
            self._load_zip_images(target_dir)
        except Exception as exc:
            # Don't interrupt the flow; just log any issues with image loading.
            self._log(f"[ZIP] Błąd ładowania obrazów z archiwum: {exc}")

    # LOG

    def _log(self, msg: str) -> None:
        if hasattr(self, "log_tab") and self.log_tab is not None:
            self.log_tab.log(msg)
        else:
            print(msg)

    # ZIP image loading
    def _load_zip_images(self, target_dir: str) -> None:
        """
        Scan the extracted ZIP directory for image files and add them to the
        gallery (ImageTab).  Accepted extensions include PNG, JPG, JPEG, WEBP
        and GIF.  Each image is labeled with its relative path inside the
        archive.  Logs each added image.
        """
        import os  # imported here to avoid circular import at module level

        if not hasattr(self, "images_tab"):
            return

        for root, _, files in os.walk(target_dir):
            for fname in files:
                ext = fname.lower().split(".")[-1]
                if ext in {"png", "jpg", "jpeg", "webp", "gif"}:
                    path = os.path.join(root, fname)
                    # Relative label (e.g. "images/logo.png")
                    try:
                        rel = os.path.relpath(path, start=target_dir)
                    except Exception:
                        rel = fname
                    # Add the image to the gallery
                    self.images_tab.add_image(path, label=rel)
                    self._log(f"[ZIP] Dodano obraz: {rel}")


if __name__ == "__main__":
    app = EPSChatAtomApp()
    app.mainloop()
