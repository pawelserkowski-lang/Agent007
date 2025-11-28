
from __future__ import annotations

from typing import List, Callable

import customtkinter as ctk

from ..model_manager.schemas import ModelInfo
from ..chat_engine import ChatEngine, ChatResult


class ChainTab(ctk.CTkFrame):
    """Tryb łańcuchowy (pipeline): model A -> wynik -> model B -> wynik -> ...

    - używa aktualnie wybranych modeli jako etapów łańcucha,
    - każdy krok dostaje albo czysty prompt (pierwszy),
      albo prompt + wynik poprzedniego modelu jako kontekst,
    - wyniki są wyświetlane sekwencyjnie w jednym oknie logu,
    - narzędzia wejściowe: autokorekta PL/EN i tłumaczenie na EN dla promptu łańcucha.
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

        self._running: bool = False
        self._chain_models: List[ModelInfo] = []
        self._chain_user_prompt: str = ""
        self._chain_index: int = 0
        self.chain_results: List[ChatResult] = []

        # GÓRA – prompt + start
        top = ctk.CTkFrame(self, fg_color="#e5f2ff")
        top.grid(row=0, column=0, sticky="ew", padx=8, pady=(8, 4))
        top.grid_columnconfigure(0, weight=1)
        top.grid_columnconfigure(1, weight=0)

        self.entry = ctk.CTkEntry(top, placeholder_text="Prompt dla łańcucha modeli…")
        self.entry.grid(row=0, column=0, sticky="ew", padx=(0, 4), pady=4)
        self.entry.bind("<Return>", self._on_enter)

        self.start_btn = ctk.CTkButton(
            top,
            text="Uruchom łańcuch",
            command=self._on_start,
            fg_color="#2563eb",
            hover_color="#2563eb",
        )
        self.start_btn.grid(row=0, column=1, pady=4)

        self.hint_label = ctk.CTkLabel(
            top,
            text="Łańcuch: modele są wywoływane po kolei, każdy widzi wynik poprzedniego.",
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
            text="Narzędzia wejściowe: najpierw popraw/przetłumacz prompt, potem uruchom łańcuch.",
            font=("Segoe UI", 9),
            text_color="#4b5563",
            wraplength=520,
            justify="left",
        )
        self.tools_hint.grid(row=0, column=2, sticky="w")

        # ŚRODEK – log łańcucha
        self.log_text = ctk.CTkTextbox(self, wrap="word")
        self.log_text.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 4))

        # DÓŁ – status
        self.status_bar = ctk.CTkLabel(
            self,
            text="Tryb łańcuchowy – nieaktywny.",
            font=("Consolas", 10),
            text_color="#4b5563",
        )
        self.status_bar.grid(row=2, column=0, sticky="ew", padx=8, pady=(0, 8))

    # ZDARZENIA

    def _on_enter(self, event=None) -> None:  # type: ignore[override]
        self._on_start()

    def _on_start(self) -> None:
        if self._running:
            self._append_log("[INFO] Łańcuch już trwa – poczekaj na zakończenie.")
            return

        prompt = self.entry.get().strip()
        if not prompt:
            return
        models = self.get_selected_models()
        if not models:
            self.status_bar.configure(text="Tryb łańcuchowy – wybierz najpierw modele w panelu MODELE.")
            return

        self.entry.delete(0, "end")
        self._start_chain(models, prompt)

    # LOGIKA ŁAŃCUCHA

    def _start_chain(self, models: List[ModelInfo], user_prompt: str) -> None:
        self._running = True
        self._chain_models = list(models)
        self._chain_user_prompt = user_prompt
        self._chain_index = 0
        self.chain_results = []

        self.log_text.delete("1.0", "end")
        self._append_log(f"[CHAIN] Start łańcucha dla {len(models)} modeli.")
        self.log_fn(f"[CHAIN] Start łańcucha dla {len(models)} modeli.")
        self._run_next_step(context_text=None)

    def _run_next_step(self, context_text: str | None) -> None:
        if self._chain_index >= len(self._chain_models):
            self._running = False
            self.status_bar.configure(text="Tryb łańcuchowy – zakończono wszystkie kroki.")
            self.log_fn("[CHAIN] Łańcuch zakończony.")
            return

        model = self._chain_models[self._chain_index]
        step_no = self._chain_index + 1
        total = len(self._chain_models)
        key = f"{model.provider_id}:{model.model_id}"

        self.status_bar.configure(
            text=f"Tryb łańcuchowy – krok {step_no}/{total}: {key}",
        )
        self._append_log(f"\n== KROK {step_no}/{total}: {key} ==")

        final_prompt = self._build_chain_prompt(self._chain_user_prompt, context_text)

        def on_finished(result: ChatResult, step_no=step_no, key=key, model=model) -> None:
            # wykonuje się w wątku – przełączamy do głównego wątku
            self.after(0, lambda r=result, s=step_no, k=key, m=model: self._on_step_finished(r, s, k, m))

        self.chat_engine.chat_async(model, final_prompt, on_finished=on_finished, stream=False)

    def _build_chain_prompt(self, user_prompt: str, context_text: str | None) -> str:
        if context_text is None:
            return user_prompt
        return (
            "To jest wynik poprzedniego modelu w łańcuchu:\n"
            f"{context_text}\n\n"
            "Na podstawie tego wyniku odpowiedz na poniższe polecenie użytkownika:\n"
            f"{user_prompt}"
        )

    def _on_step_finished(self, result: ChatResult, step_no: int, key: str, model: ModelInfo) -> None:
        self.chain_results.append(result)

        if result.error:
            self._append_log(f"[{key}] BŁĄD ({result.error})")
            if result.text:
                self._append_log(result.text)
            self.log_fn(f"[CHAIN] Krok {step_no} ({key}) zakończony błędem: {result.error}")
        else:
            it = result.input_tokens or 0
            ot = result.output_tokens or 0
            self._append_log(f"[{key}] OK • in={it} • out={ot}")
            if result.text:
                self._append_log(result.text)
            self.log_fn(f"[CHAIN] Krok {step_no} ({key}) OK.")

        context_text = result.text or ""
        self._chain_index += 1
        self._run_next_step(context_text=context_text)

    # EXPORT

    def export_chain(self) -> list[dict]:
        """Zwraca prostą listę kroków łańcucha (do ewentualnego logowania/zapisu)."""
        out: list[dict] = []
        for res in self.chain_results:
            m = res.model
            out.append(
                {
                    "provider_id": m.provider_id,
                    "model_id": m.model_id,
                    "display_name": m.display_name,
                    "text": res.text,
                    "input_tokens": res.input_tokens,
                    "output_tokens": res.output_tokens,
                    "cost": res.cost,
                    "error": res.error,
                    "latency_s": res.latency_s,
                }
            )
        return out

    # Narzędzia wejściowe – autokorekta/tłumaczenie

    def _ensure_tool_ready(self):
        if self.chat_engine is None:
            self._append_log("[TOOLS] Brak ChatEngine – nie można użyć autokorekty/tłumaczenia.")
            return None, None
        text = self.entry.get().strip()
        if not text:
            return None, None
        models = self.get_selected_models()
        if not models:
            self.status_bar.configure(text="Tryb łańcuchowy – wybierz najpierw modele w panelu MODELE.")
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

        win, proposed_box, use_btn = self._create_preview_window("Autokorekta PL/EN (Łańcuch)", text)

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
            self._append_log("[TOOLS] Autokorekta (Łańcuch) zakończona.")

        try:
            self.chat_engine.chat_async(model, prompt, on_finished=on_finished, stream=False)
        except Exception as exc:  # noqa: BLE001
            self._append_log(f"[TOOLS] Błąd autokorekty (Łańcuch): {exc}")
            win.destroy()

    def _on_translate_preview_click(self) -> None:
        model, text = self._ensure_tool_ready()
        if not model or text is None:
            return

        win, proposed_box, use_btn = self._create_preview_window("Tłumaczenie na EN (Łańcuch)", text)

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
            self._append_log("[TOOLS] Tłumaczenie na EN (Łańcuch) zakończone.")

        try:
            self.chat_engine.chat_async(model, prompt, on_finished=on_finished, stream=False)
        except Exception as exc:  # noqa: BLE001
            self._append_log(f"[TOOLS] Błąd tłumaczenia (Łańcuch): {exc}")
            win.destroy()

    # INTERNAL

    def _append_log(self, msg: str) -> None:
        self.log_text.insert("end", msg + "\n")
        self.log_text.see("end")
