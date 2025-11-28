
from __future__ import annotations
import customtkinter as ctk
from typing import List, Callable, Optional, Any
from pathlib import Path
from PIL import Image, ImageTk  # type: ignore[import]

from ..model_manager.schemas import ModelInfo


class ChatTab(ctk.CTkFrame):
    """Główna karta czatu.

    Funkcjonalność:
    - wyświetlanie wiadomości (tekstowych + obrazowych),
    - pole wpisywania + ENTER / przycisk WYŚLIJ,
    - mini-loga z aktywnymi modelami,
    - delikatne tło (jeśli dostępny jest plik tła),
    - logo EPS w prawym górnym rogu,
    - narzędzia wejściowe: autokorekta PL/EN + podgląd tłumaczenia na EN przed wysłaniem.
    """

    def __init__(
        self,
        parent,
        get_selected_models: Callable[[], List[ModelInfo]],
        on_send: Optional[Callable[[str, List[ModelInfo]], None]] = None,
        chat_engine: Any | None = None,
        log_fn: Optional[Callable[[str], None]] = None,
        **kwargs,
    ) -> None:
        super().__init__(parent, fg_color="#e5f2ff", **kwargs)
        self.get_selected_models = get_selected_models
        self.on_send = on_send
        self.chat_engine = chat_engine
        self.log_fn = log_fn or (lambda msg: None)
        self._image_refs: list[ImageTk.PhotoImage] = []
        self._bg_image_ref: Optional[ImageTk.PhotoImage] = None
        self._logo_ref: Optional[ImageTk.PhotoImage] = None

        self._setup_background()
        self._build_layout()

    # LAYOUT

    def _setup_background(self) -> None:
        assets = Path(__file__).resolve().parent.parent / "assets"
        bg_path = assets / "tlo.png"
        if bg_path.exists():
            try:
                img = Image.open(bg_path)
                img = img.resize((1280, 720))  # lekkie skalowanie tła
                self._bg_image_ref = ImageTk.PhotoImage(img)
                bg_label = ctk.CTkLabel(self, image=self._bg_image_ref, text="")
                bg_label.place(relx=0.5, rely=0.5, anchor="center")
            except Exception:
                pass

    def _build_layout(self) -> None:
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)
        self.grid_columnconfigure(0, weight=1)

        # Górny pasek: logo + wybrane modele
        top = ctk.CTkFrame(self, fg_color="#e5f2ff")
        top.grid(row=0, column=0, sticky="ew", padx=8, pady=(8, 4))
        top.grid_columnconfigure(0, weight=1)
        top.grid_columnconfigure(1, weight=0)

        self.models_label = ctk.CTkLabel(
            top,
            text="MODELE: — brak —",
            font=("Consolas", 11),
            text_color="#4b5563",
        )
        self.models_label.grid(row=0, column=0, sticky="w", padx=4, pady=4)

        # Logo EPS w prawym górnym rogu
        logo_label = ctk.CTkLabel(top, text="")
        logo_label.grid(row=0, column=1, sticky="e", padx=4, pady=4)
        self._load_logo_into(logo_label)

        # Obszar wiadomości
        self.messages = ctk.CTkScrollableFrame(self, fg_color="#e5f2ff")
        self.messages.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 4))

        # Dolny pasek: input + przyciski + pomoc
        bottom = ctk.CTkFrame(self, fg_color="#e5f2ff")
        bottom.grid(row=2, column=0, sticky="ew", padx=8, pady=(4, 8))
        bottom.grid_rowconfigure(0, weight=0)
        bottom.grid_rowconfigure(1, weight=0)
        bottom.grid_columnconfigure(0, weight=1)
        bottom.grid_columnconfigure(1, weight=0)
        bottom.grid_columnconfigure(2, weight=0)

        self.entry = ctk.CTkEntry(
            bottom,
            placeholder_text="Wpisz wiadomość…",
        )
        self.entry.grid(row=0, column=0, sticky="ew", padx=(0, 4), pady=4)
        self.entry.bind("<Return>", self._on_enter)

        self.send_btn = ctk.CTkButton(
            bottom,
            text="Wyślij",
            command=self._on_send_click,
            fg_color="#2563eb",
            hover_color="#2563eb",
        )
        self.send_btn.grid(row=0, column=1, padx=(0, 0), pady=4)

        # Narzędzia wejściowe: autokorekta + tłumaczenie
        tools = ctk.CTkFrame(bottom, fg_color="#e5f2ff")
        tools.grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 4))
        tools.grid_columnconfigure(0, weight=0)
        tools.grid_columnconfigure(1, weight=0)
        tools.grid_columnconfigure(2, weight=1)

        self.autocorrect_btn = ctk.CTkButton(
            tools,
            text="Autokorekta PL/EN",
            width=150,
            command=self._on_autocorrect_click,
            fg_color="#3b82f6",
            hover_color="#2563eb",
        )
        self.autocorrect_btn.grid(row=0, column=0, padx=(0, 4), pady=2)

        self.translate_btn = ctk.CTkButton(
            tools,
            text="EN podgląd",
            width=120,
            command=self._on_translate_preview_click,
            fg_color="#3b82f6",
            hover_color="#2563eb",
        )
        self.translate_btn.grid(row=0, column=1, padx=(0, 4), pady=2)

        self.tools_hint = ctk.CTkLabel(
            tools,
            text=(
                "Autokorekta: poprawia tekst (PL/EN) z użyciem wybranego modelu. "
                "EN podgląd: pokazuje tłumaczenie na angielski przed wysłaniem."
            ),
            font=("Segoe UI", 9),
            text_color="#4b5563",
            wraplength=580,
            justify="left",
        )
        self.tools_hint.grid(row=0, column=2, sticky="w")

    def _load_logo_into(self, label: ctk.CTkLabel) -> None:
        assets = Path(__file__).resolve().parent.parent / "assets"
        logo_path = assets / "logo.jpg"
        if logo_path.exists():
            try:
                img = Image.open(logo_path)
                img.thumbnail((120, 40))
                self._logo_ref = ImageTk.PhotoImage(img)
                label.configure(image=self._logo_ref, text="")
            except Exception:
                label.configure(text="EPS", font=("Segoe UI", 14, "bold"), text_color="#38bdf8")
        else:
            label.configure(text="EPS", font=("Segoe UI", 14, "bold"), text_color="#38bdf8")

    # PUBLIC API

    def add_system_message(self, text: str) -> None:
        self._add_bubble(text, who="SYSTEM")

    def add_user_message(self, text: str) -> None:
        self._add_bubble(text, who="TY")

    def add_model_message(self, model_label: str, text: str) -> None:
        self._add_bubble(text, who=model_label)

    def add_image_message(self, model_label: str, image_path: str) -> None:
        """Dodaje bańkę z obrazem (np. wygenerowanym przez model)."""
        wrapper = ctk.CTkFrame(self.messages, fg_color="#e5f2ff")
        wrapper.pack(fill="x", padx=6, pady=4, anchor="w")

        header = ctk.CTkLabel(
            wrapper,
            text=f"[{model_label}]",
            font=("Segoe UI", 10, "bold"),
            text_color="#38bdf8",
        )
        header.pack(anchor="w")

        try:
            img = Image.open(image_path)
            img.thumbnail((420, 420))
            tk_img = ImageTk.PhotoImage(img)
            self._image_refs.append(tk_img)
            lbl = ctk.CTkLabel(wrapper, image=tk_img, text="")
            lbl.pack(anchor="w", pady=(2, 0))
        except Exception as exc:  # noqa: BLE001
            err = ctk.CTkLabel(
                wrapper,
                text=f"[BŁĄD PODGLĄDU OBRAZU] {exc}",
                text_color="#f97316",
                font=("Consolas", 10),
            )
            err.pack(anchor="w")

        self._scroll_to_bottom()

    def update_models_hint(self) -> None:
        models = self.get_selected_models()
        if not models:
            text = "MODELE: — brak —"
        else:
            text = "MODELE: " + ", ".join(f"{m.provider_id}:{m.model_id}" for m in models)
        self.models_label.configure(text=text)

    # INTERNAL – bańki

    def _add_bubble(self, text: str, who: str) -> None:
        wrapper = ctk.CTkFrame(self.messages, fg_color="#e5f2ff")
        wrapper.pack(fill="x", padx=6, pady=4, anchor="w")

        header = ctk.CTkLabel(
            wrapper,
            text=f"[{who}]",
            font=("Segoe UI", 10, "bold"),
            text_color="#0f172a" if who != "SYSTEM" else "#38bdf8",
        )
        header.pack(anchor="w")

        body = ctk.CTkTextbox(
            wrapper,
            wrap="word",
        )
        body.insert("end", text)
        body.configure(state="disabled")
        body.pack(anchor="w", pady=(2, 0), fill="x")

        self._scroll_to_bottom()

    def _scroll_to_bottom(self) -> None:
        try:
            self.messages._parent_canvas.yview_moveto(1.0)  # type: ignore[attr-defined]
        except Exception:
            pass

    # INPUT HANDLERS

    def _on_enter(self, event=None) -> None:  # type: ignore[override]
        self._on_send_click()

    def _on_send_click(self) -> None:
        text = self.entry.get().strip()
        if not text:
            return
        self.entry.delete(0, "end")
        self.add_user_message(text)
        models = self.get_selected_models()
        self.update_models_hint()
        if not models:
            self.add_system_message("Brak wybranych modeli – wybierz w panelu MODELE.")
            return
        if self.on_send:
            self.on_send(text, models)

    # INPUT TOOLS (autokorekta / tłumaczenie)

    def _ensure_tool_ready(self) -> tuple[Optional[ModelInfo], Optional[str]]:
        """Sprawdza, czy dostępny jest model + tekst do przetworzenia."""
        if self.chat_engine is None:
            self.add_system_message("Funkcje autokorekty i tłumaczenia wymagają skonfigurowanego ChatEngine.")
            return None, None
        text = self.entry.get().strip()
        if not text:
            return None, None
        models = self.get_selected_models()
        if not models:
            self.add_system_message("Wybierz co najmniej jeden model w panelu MODELE, aby użyć autokorekty/tłumaczenia.")
            return None, None
        return models[0], text  # używamy pierwszego zaznaczonego modelu

    def _create_preview_window(self, title: str, original: str) -> tuple[ctk.CTkToplevel, ctk.CTkLabel, ctk.CTkButton]:
        win = ctk.CTkToplevel(self)
        win.title(title)
        win.geometry("700x420")
        win.configure(fg_color="#e5f2ff")

        win.grid_rowconfigure(1, weight=1)
        win.grid_columnconfigure(0, weight=1)
        win.grid_columnconfigure(1, weight=1)

        header = ctk.CTkLabel(
            win,
            text=title,
            font=("Segoe UI", 13, "bold"),
            text_color="#0f172a",
        )
        header.grid(row=0, column=0, columnspan=2, sticky="w", padx=8, pady=(8, 4))

        orig_label = ctk.CTkLabel(win, text="Oryginał", font=("Segoe UI", 10, "bold"))
        orig_label.grid(row=1, column=0, sticky="w", padx=8, pady=(0, 2))

        prop_label = ctk.CTkLabel(win, text="Propozycja", font=("Segoe UI", 10, "bold"))
        prop_label.grid(row=1, column=1, sticky="w", padx=8, pady=(0, 2))

        orig_text = ctk.CTkTextbox(win, wrap="word")
        orig_text.grid(row=2, column=0, sticky="nsew", padx=8, pady=(0, 4))
        orig_text.insert("end", original)
        orig_text.configure(state="disabled")

        proposed_text = ctk.CTkTextbox(win, wrap="word")
        proposed_text.grid(row=2, column=1, sticky="nsew", padx=8, pady=(0, 4))
        proposed_text.insert("end", "Przetwarzanie – proszę czekać…")
        proposed_text.configure(state="disabled")

        btn_frame = ctk.CTkFrame(win, fg_color="#e5f2ff")
        btn_frame.grid(row=3, column=0, columnspan=2, sticky="ew", padx=8, pady=(4, 8))
        btn_frame.grid_columnconfigure(0, weight=0)
        btn_frame.grid_columnconfigure(1, weight=1)
        btn_frame.grid_columnconfigure(2, weight=0)

        use_btn = ctk.CTkButton(
            btn_frame,
            text="Użyj w polu",
            state="disabled",
            fg_color="#16a34a",
            hover_color="#22c55e",
        )
        use_btn.grid(row=0, column=0, padx=(0, 4))

        close_btn = ctk.CTkButton(
            btn_frame,
            text="Zamknij",
            command=win.destroy,
            fg_color="#3b82f6",
            hover_color="#93c5fd",
        )
        close_btn.grid(row=0, column=2, padx=(4, 0))

        # zapamiętujemy kontrolkę tekstu, którą zaktualizujemy
        win._proposed_textbox = proposed_text  # type: ignore[attr-defined]
        win._use_button = use_btn  # type: ignore[attr-defined]
        win._proposed_value = ""  # type: ignore[attr-defined]

        def _use_value() -> None:
            val = getattr(win, "_proposed_value", "")
            if val:
                self.entry.delete(0, "end")
                self.entry.insert(0, val)
            win.destroy()

        use_btn.configure(command=_use_value)

        return win, proposed_text, use_btn

    def _on_autocorrect_click(self) -> None:
        model, text = self._ensure_tool_ready()
        if not model or text is None:
            return

        win, proposed_box, use_btn = self._create_preview_window("Autokorekta PL/EN", text)

        prompt = (
            "Popraw błędy językowe, gramatyczne i interpunkcyjne w poniższym tekście.\n"
            "Tekst może być po polsku lub angielsku. Zachowaj styl użytkownika.\n"
            "Zwróć TYLKO poprawioną wersję tekstu, bez żadnych komentarzy ani wyjaśnień.\n\n"
            f"Tekst:\n{text}"
        )

        def on_finished(result) -> None:
            def update() -> None:
                proposed_box.configure(state="normal")
                proposed_box.delete("1.0", "end")
                proposed = result.text or ""
                if not proposed:
                    proposed = "[Brak odpowiedzi z modelu]"
                proposed_box.insert("end", proposed)
                proposed_box.configure(state="disabled")
                use_btn.configure(state="normal")
                setattr(win, "_proposed_value", proposed)
            self.after(0, update)
            self.log_fn("[TOOLS] Autokorekta zakończona.")

        # wywołanie narzędzia przez ChatEngine
        try:
            self.chat_engine.chat_async(model, prompt, on_finished=on_finished, stream=False)  # type: ignore[union-attr]
        except Exception as exc:  # noqa: BLE001
            self.add_system_message(f"[BŁĄD AUTOKOREKTY] {exc}")
            win.destroy()

    def _on_translate_preview_click(self) -> None:
        model, text = self._ensure_tool_ready()
        if not model or text is None:
            return

        win, proposed_box, use_btn = self._create_preview_window("Tłumaczenie na angielski – podgląd", text)

        prompt = (
            "Przetłumacz poniższy tekst użytkownika na naturalny, poprawny język angielski.\n"
            "Zachowaj znaczenie i ton, ale możesz lekko wygładzić styl.\n"
            "Zwróć TYLKO przetłumaczony tekst po angielsku, bez żadnych komentarzy.\n\n"
            f"Tekst:\n{text}"
        )

        def on_finished(result) -> None:
            def update() -> None:
                proposed_box.configure(state="normal")
                proposed_box.delete("1.0", "end")
                proposed = result.text or ""
                if not proposed:
                    proposed = "[Brak odpowiedzi z modelu]"
                proposed_box.insert("end", proposed)
                proposed_box.configure(state="disabled")
                use_btn.configure(state="normal")
                setattr(win, "_proposed_value", proposed)
            self.after(0, update)
            self.log_fn("[TOOLS] Tłumaczenie na EN zakończone.")

        try:
            self.chat_engine.chat_async(model, prompt, on_finished=on_finished, stream=False)  # type: ignore[union-attr]
        except Exception as exc:  # noqa: BLE001
            self.add_system_message(f"[BŁĄD TŁUMACZENIA] {exc}")
            win.destroy()
