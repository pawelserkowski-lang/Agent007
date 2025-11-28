
from __future__ import annotations
import customtkinter as ctk
from typing import List, Callable, Dict
import time

from ..model_manager.schemas import ModelInfo
from ..chat_engine import ChatEngine, ChatResult


class ModelPanel(ctk.CTkFrame):
    """Panel wyników dla pojedynczego modelu w trybie porównawczym."""
    def __init__(self, parent, model: ModelInfo, **kwargs) -> None:
        super().__init__(parent, fg_color="#e5f2ff", **kwargs)
        self.model = model
        self._start_ts: float | None = None

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        header = ctk.CTkLabel(
            self,
            text=f"{model.provider_id}:{model.model_id}",
            font=("Segoe UI", 11, "bold"),
            text_color="#38bdf8",
        )
        header.grid(row=0, column=0, sticky="w", padx=4, pady=(4, 2))

        self.text = ctk.CTkTextbox(self, wrap="word", width=10)
        self.text.grid(row=1, column=0, sticky="nsew", padx=4, pady=2)

        self.status = ctk.CTkLabel(
            self,
            text="Stan: oczekiwanie",
            font=("Consolas", 10),
            text_color="#4b5563",
        )
        self.status.grid(row=2, column=0, sticky="ew", padx=4, pady=(0, 4))

    def start(self) -> None:
        self._start_ts = time.time()
        self.text.delete("1.0", "end")
        self.status.configure(text="Stan: wysyłanie…", text_color="#4b5563")

    def append_text(self, chunk: str) -> None:
        if not chunk:
            return
        self.text.insert("end", chunk)
        self.text.see("end")

    def finish(self, result: ChatResult) -> None:
        if self._start_ts is not None:
            latency = result.latency_s if result.latency_s is not None else (time.time() - self._start_ts)
        else:
            latency = result.latency_s or 0.0

        if result.error:
            self.status.configure(
                text=f"Stan: BŁĄD ({result.error}) • {latency:.2f}s",
                text_color="#f97316",
            )
            if result.text:
                self.append_text("\n" + result.text)
            return

        it = result.input_tokens or 0
        ot = result.output_tokens or 0
        cost = result.cost or 0.0

        self.status.configure(
            text=f"Stan: OK • czas {latency:.2f}s • in={it} • out={ot} • koszt~{cost:.5f}",
            text_color="#22c55e",
        )
        if result.text:
            self.append_text("\n" + result.text)


class CompareTab(ctk.CTkFrame):
    """Tryb porównawczy: jedno okno, wiele modeli, równoległe odpowiedzi
    + pełen dostęp krzyżowy do wyników poprzednich modeli.

    Logika:
    - każde zapytanie zapisuje ChatResult per model w self.results,
    - użytkownik może wybrać źródło kontekstu (brak / wszyscy / konkretny model),
    - przy kolejnym zapytaniu treść kontekstu jest dołączana do promptu,
    - stan wyników można eksportować/importować jako scenariusz eksperymentu,
    - dolne narzędzia wejściowe: autokorekta PL/EN i tłumaczenie na EN przed wysłaniem.
    """
    def __init__(
        self,
        parent,
        get_selected_models: Callable[[], List[ModelInfo]],
        chat_engine: ChatEngine,
        log_fn: Callable[[str], None],
        **kwargs,
    ) -> None:
        super().__init__(parent, fg_color="#e5f2ff", **kwargs)
        self.get_selected_models = get_selected_models
        self.chat_engine = chat_engine
        self.log_fn = log_fn

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # PRZECHOWYWANIE WYNIKÓW (pełen dostęp krzyżowy)
        self.panels: Dict[str, ModelPanel] = {}
        self.results: Dict[str, ChatResult] = {}
        self._active_requests = 0

        # GÓRNY PASEK: prompt + porównaj
        top = ctk.CTkFrame(self, fg_color="#e5f2ff")
        top.grid(row=0, column=0, sticky="ew", padx=8, pady=(8, 4))
        top.grid_columnconfigure(0, weight=1)
        top.grid_columnconfigure(1, weight=0)

        self.entry = ctk.CTkEntry(top, placeholder_text="Prompt do porównania modeli…")
        self.entry.grid(row=0, column=0, sticky="ew", padx=(0, 4), pady=4)
        self.entry.bind("<Return>", self._on_enter)

        self.send_btn = ctk.CTkButton(
            top,
            text="Porównaj",
            command=self._on_send,
            fg_color="#2563eb",
            hover_color="#2563eb",
        )
        self.send_btn.grid(row=0, column=1, pady=4)

        # krótki opis funkcji
        self.hint_label = ctk.CTkLabel(
            top,
            text="Porównanie: ten sam prompt trafia równolegle do wszystkich wybranych modeli.",
            font=("Segoe UI", 9),
            text_color="#4b5563",
        )
        self.hint_label.grid(row=1, column=0, columnspan=2, sticky="w", padx=4, pady=(0, 2))

        # Narzędzia wejściowe: autokorekta + tłumaczenie dla promptu
        tools = ctk.CTkFrame(top, fg_color="#e5f2ff")
        tools.grid(row=2, column=0, columnspan=2, sticky="w", padx=4, pady=(0, 2))
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
            text="Narzędzia wejściowe: najpierw popraw/przetłumacz prompt, potem naciśnij 'Porównaj'.",
            font=("Segoe UI", 9),
            text_color="#4b5563",
            wraplength=520,
            justify="left",
        )
        self.tools_hint.grid(row=0, column=2, sticky="w")

        # ŚRODKOWA CZĘŚĆ: panele modeli
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="#e5f2ff")
        self.scroll.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 4))
        self.scroll.grid_columnconfigure(0, weight=1)

        # DOLNY PASEK: status + selekcja kontekstu (pełen dostęp krzyżowy)
        bottom = ctk.CTkFrame(self, fg_color="#e5f2ff")
        bottom.grid(row=2, column=0, sticky="ew", padx=8, pady=(0, 8))
        bottom.grid_columnconfigure(1, weight=1)

        self.status_bar = ctk.CTkLabel(
            bottom,
            text="Tryb porównawczy – brak aktywnych zapytań.",
            font=("Consolas", 10),
            text_color="#4b5563",
        )
        self.status_bar.grid(row=0, column=0, sticky="w", padx=(0, 8), pady=4)

        self.context_mode_var = ctk.StringVar(value="brak")
        self.context_selector = ctk.CTkOptionMenu(
            bottom,
            variable=self.context_mode_var,
            values=["brak"],
            fg_color="#3b82f6",
            button_color="#2563eb",
            button_hover_color="#2563eb",
            text_color="#0f172a",
        )
        self.context_selector.grid(row=0, column=1, sticky="e", pady=4)

        self._refresh_context_options()

    # EVENT HANDLERS

    def _on_enter(self, event=None) -> None:  # type: ignore[override]
        self._on_send()

    def _on_send(self) -> None:
        prompt = self.entry.get().strip()
        if not prompt:
            return
        models = self.get_selected_models()
        if not models:
            self.status_bar.configure(text="Tryb porównawczy – wybierz najpierw modele w panelu MODELE.")
            return

        self.entry.delete(0, "end")

        # zbuduj prompt z kontekstem (pełen dostęp krzyżowy)
        final_prompt = self._build_prompt_with_context(prompt)

        self._reset_panels(models)
        self._active_requests = len(models)
        self._update_status_bar()
        self.log_fn(f"[COMPARE] Wysłano prompt do {len(models)} modeli.")

        for m in models:
            key = f"{m.provider_id}:{m.model_id}"
            panel = self.panels[key]
            panel.start()

            def on_finished(result: ChatResult, panel=panel, key=key) -> None:
                # wywołanie z wątku – przekazujemy do głównego wątku
                self.after(0, lambda r=result, p=panel, k=key: self._handle_result(r, p, k))

            self.chat_engine.chat_async(m, final_prompt, on_finished=on_finished, stream=False)

    # INTERNAL LOGIC

    def _reset_panels(self, models: List[ModelInfo]) -> None:
        for child in self.scroll.winfo_children():
            child.destroy()
        self.panels.clear()
        # UWAGA: nie czyścimy self.results – chcemy mieć dostęp do poprzednich wyników jako kontekstu
        for m in models:
            key = f"{m.provider_id}:{m.model_id}"
            panel = ModelPanel(self.scroll, m)
            panel.grid(sticky="nsew", padx=4, pady=4)
            self.panels[key] = panel

    def _handle_result(self, result: ChatResult, panel: ModelPanel, key: str) -> None:
        # zapisz wynik do magazynu wyników (pełen dostęp krzyżowy)
        self.results[key] = result

        panel.finish(result)
        self._active_requests = max(0, self._active_requests - 1)
        self._update_status_bar()
        self._refresh_context_options()
        state = "OK" if not result.error else f"BŁĄD:{result.error}"
        self.log_fn(f"[COMPARE] {key} → {state} ({(result.latency_s or 0.0):.2f}s).")

    def _update_status_bar(self) -> None:
        if self._active_requests <= 0:
            self.status_bar.configure(text="Tryb porównawczy – brak aktywnych zapytań.")
        else:
            self.status_bar.configure(
                text=f"Tryb porównawczy – aktywne zapytania: {self._active_requests}…",
            )

    # KONTEXT KRZYŻOWY

    def _refresh_context_options(self) -> None:
        """Aktualizuje listę opcji w selektorze kontekstu na podstawie dostępnych wyników."""
        options = ["brak"]
        if self.results:
            options.append("wszyscy")
            options.extend(sorted(self.results.keys()))
        current = self.context_mode_var.get()
        if current not in options:
            current = "brak"
        self.context_selector.configure(values=options)
        self.context_mode_var.set(current)

    def _build_prompt_with_context(self, prompt: str) -> str:
        """Buduje finalny prompt, doklejając wybrany kontekst z wyników innych modeli.

        tryby:
        - "brak"     -> brak kontekstu (zwykły prompt),
        - "wszyscy"  -> kontekst z wszystkich dostępnych wyników,
        - "provider:model" -> kontekst tylko z jednego modelu.
        """
        mode = self.context_mode_var.get()
        if mode == "brak" or not self.results:
            return prompt

        context_chunks: list[str] = []
        if mode == "wszyscy":
            for key, res in self.results.items():
                if not res.text:
                    continue
                context_chunks.append(f"[{key}]\n{res.text}")
        else:
            # traktujemy wartość jako klucz modelu
            res = self.results.get(mode)
            if res and res.text:
                context_chunks.append(f"[{mode}]\n{res.text}")

        if not context_chunks:
            return prompt

        context_block = "\n\n".join(context_chunks)
        final_prompt = (
            "Kontekst z poprzednich modeli (wyniki krzyżowe):\n"
            f"{context_block}\n\n"
            "Na podstawie powyższego kontekstu odpowiedz na poniższe polecenie użytkownika:\n"
            f"{prompt}"
        )
        return final_prompt

    # SCENARIUSZE EKSPERYMENTÓW

    def export_scenario(self) -> dict:
        """Eksportuje aktualny stan self.results do prostego słownika JSON-owalnego."""
        scenario: dict[str, dict] = {}
        for key, res in self.results.items():
            m = res.model
            scenario[key] = {
                "provider_id": m.provider_id,
                "model_id": m.model_id,
                "display_name": m.display_name,
                "capabilities": list(m.capabilities),
                "is_multimodal": bool(m.is_multimodal),
                "context_window": m.context_window,
                "license": m.license,
                "is_default": bool(m.is_default),
                "text": res.text,
                "input_tokens": res.input_tokens,
                "output_tokens": res.output_tokens,
                "cost": res.cost,
                "error": res.error,
                "latency_s": res.latency_s,
            }
        return scenario

    def import_scenario(self, results_data: dict) -> None:
        """Czyści aktualne panele i ładuje wyniki z podanego scenariusza."""
        # wyczyść UI
        for child in self.scroll.winfo_children():
            child.destroy()
        self.panels.clear()
        self.results.clear()

        # odtwórz panele i wyniki
        for key, rd in results_data.items():
            provider_id = rd.get("provider_id", "")
            model_id = rd.get("model_id", "")
            if not provider_id or not model_id:
                continue
            display_name = rd.get("display_name") or f"{provider_id}:{model_id}"

            m = ModelInfo(
                provider_id=provider_id,
                model_id=model_id,
                display_name=display_name,
                capabilities=rd.get("capabilities") or [],
                is_multimodal=bool(rd.get("is_multimodal", False)),
                context_window=rd.get("context_window"),
                license=rd.get("license"),
                is_default=bool(rd.get("is_default", False)),
                raw=None,
            )

            res = ChatResult(
                model=m,
                text=rd.get("text") or "",
                input_tokens=rd.get("input_tokens"),
                output_tokens=rd.get("output_tokens"),
                cost=rd.get("cost"),
                error=rd.get("error"),
                latency_s=rd.get("latency_s"),
                raw=None,
            )

            key2 = f"{provider_id}:{model_id}"
            panel = ModelPanel(self.scroll, m)
            panel.grid(sticky="nsew", padx=4, pady=4)

            self.panels[key2] = panel
            self.results[key2] = res

            panel.finish(res)

        self._refresh_context_options()
        self._active_requests = 0
        self._update_status_bar()

    # Narzędzia wejściowe – wspólne helpery

    def _ensure_tool_ready(self) -> tuple[ModelInfo | None, str | None]:
        if self.chat_engine is None:
            self.log_fn("[TOOLS] Brak ChatEngine – nie można użyć autokorekty/tłumaczenia.")
            return None, None
        text = self.entry.get().strip()
        if not text:
            return None, None
        models = self.get_selected_models()
        if not models:
            self.status_bar.configure(text="Tryb porównawczy – wybierz najpierw modele w panelu MODELE.")
            return None, None
        return models[0], text

    def _create_preview_window(self, title: str, original: str):
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

        win, proposed_box, use_btn = self._create_preview_window("Autokorekta PL/EN (Porównanie)", text)

        prompt = (
            "Popraw błędy językowe, gramatyczne i interpunkcyjne w poniższym tekście.\n"
            "Tekst może być po polsku lub angielsku. Zachowaj styl użytkownika.\n"
            "Zwróć TYLKO poprawioną wersję tekstu, bez żadnych komentarzy ani wyjaśnień.\n\n"
            f"Tekst:\n{text}"
        )

        def on_finished(result: ChatResult) -> None:
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
            self.log_fn("[TOOLS] Autokorekta (Porównanie) zakończona.")

        try:
            self.chat_engine.chat_async(model, prompt, on_finished=on_finished, stream=False)
        except Exception as exc:  # noqa: BLE001
            self.log_fn(f"[TOOLS] Błąd autokorekty (Porównanie): {exc}")
            win.destroy()

    def _on_translate_preview_click(self) -> None:
        model, text = self._ensure_tool_ready()
        if not model or text is None:
            return

        win, proposed_box, use_btn = self._create_preview_window("Tłumaczenie na EN (Porównanie)", text)

        prompt = (
            "Przetłumacz poniższy tekst użytkownika na naturalny, poprawny język angielski.\n"
            "Zachowaj znaczenie i ton, ale możesz lekko wygładzić styl.\n"
            "Zwróć TYLKO przetłumaczony tekst po angielsku, bez żadnych komentarzy.\n\n"
            f"Tekst:\n{text}"
        )

        def on_finished(result: ChatResult) -> None:
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
            self.log_fn("[TOOLS] Tłumaczenie na EN (Porównanie) zakończone.")

        try:
            self.chat_engine.chat_async(model, prompt, on_finished=on_finished, stream=False)
        except Exception as exc:  # noqa: BLE001
            self.log_fn(f"[TOOLS] Błąd tłumaczenia (Porównanie): {exc}")
            win.destroy()
