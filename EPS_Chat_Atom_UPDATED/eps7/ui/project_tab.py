
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Callable, Optional

import customtkinter as ctk


class ProjectTab(ctk.CTkFrame):
    """Karta 'Projekty' – scenariusze eksperymentów Porównania.

    Funkcje:
    - zapisuje aktualny stan CompareTab.export_scenario() do pliku JSON,
    - wczytuje scenariusz i przekazuje go do CompareTab.import_scenario(),
    - pokazuje prosty log operacji.
    """

    def __init__(
        self,
        parent,
        compare_tab: Any | None = None,
        log_fn: Callable[[str], None] | None = None,
        **kwargs,
    ) -> None:
        super().__init__(parent, fg_color="#e5f2ff", **kwargs)
        self.compare_tab = compare_tab
        self.log_fn = log_fn or (lambda msg: None)

        self.scenario_dir = Path.home() / "EPS_ChatAtom_Scenarios"
        self.scenario_dir.mkdir(parents=True, exist_ok=True)

        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            self,
            text="Scenariusze eksperymentów (Porównanie)",
            font=("Segoe UI", 13, "bold"),
            text_color="#0f172a",
        )
        title.grid(row=0, column=0, sticky="w", padx=12, pady=(8, 4))

        # GÓRNY PASEK – nazwa + Zapisz
        top = ctk.CTkFrame(self, fg_color="#e5f2ff")
        top.grid(row=1, column=0, sticky="ew", padx=8, pady=(0, 4))
        top.grid_columnconfigure(0, weight=1)
        top.grid_columnconfigure(1, weight=0)
        top.grid_columnconfigure(2, weight=0)

        self.name_entry = ctk.CTkEntry(
            top,
            placeholder_text="Nazwa scenariusza (opcjonalnie)…",
        )
        self.name_entry.grid(row=0, column=0, sticky="ew", padx=(0, 4), pady=4)

        save_btn = ctk.CTkButton(
            top,
            text="Zapisz scenariusz",
            command=self._save_scenario,
            fg_color="#16a34a",
            hover_color="#22c55e",
        )
        save_btn.grid(row=0, column=1, padx=(0, 4), pady=4)

        refresh_btn = ctk.CTkButton(
            top,
            text="Odśwież listę",
            command=self._refresh_scenarios,
            fg_color="#3b82f6",
            hover_color="#2563eb",
        )
        refresh_btn.grid(row=0, column=2, padx=(0, 0), pady=4)

        # ŚRODKOWY PASEK – wybór scenariusza + Wczytaj
        mid = ctk.CTkFrame(self, fg_color="#e5f2ff")
        mid.grid(row=2, column=0, sticky="ew", padx=8, pady=(0, 4))
        mid.grid_columnconfigure(0, weight=1)
        mid.grid_columnconfigure(1, weight=0)

        self.scenario_var = ctk.StringVar(value="")
        self.scenario_menu = ctk.CTkOptionMenu(
            mid,
            variable=self.scenario_var,
            values=["(brak scenariuszy)"],
            fg_color="#3b82f6",
            button_color="#2563eb",
            button_hover_color="#2563eb",
            text_color="#0f172a",
        )
        self.scenario_menu.grid(row=0, column=0, sticky="ew", padx=(0, 4), pady=4)

        load_btn = ctk.CTkButton(
            mid,
            text="Wczytaj scenariusz",
            command=self._load_scenario,
            fg_color="#2563eb",
            hover_color="#2563eb",
        )
        load_btn.grid(row=0, column=1, pady=4)

        # DÓŁ – log operacji
        self.log_text = ctk.CTkTextbox(self, wrap="word")
        self.log_text.grid(row=3, column=0, sticky="nsew", padx=8, pady=(0, 8))

        self._refresh_scenarios()
        self._log_local("Gotowe. Użyj Porównania, a następnie zapisz stan jako scenariusz.")

    # UTIL

    def _log_local(self, msg: str) -> None:
        self.log_text.insert("end", msg + "\n")
        self.log_text.see("end")

    # SCENARIUSZE

    def _list_scenario_files(self) -> list[Path]:
        return sorted(self.scenario_dir.glob("*.json"))

    def _refresh_scenarios(self) -> None:
        files = self._list_scenario_files()
        if not files:
            values = ["(brak scenariuszy)"]
            self.scenario_menu.configure(values=values)
            self.scenario_var.set(values[0])
            self._log_local("Brak zapisanych scenariuszy.")
            return

        names = [f.stem for f in files]
        self.scenario_menu.configure(values=names)
        if self.scenario_var.get() not in names:
            self.scenario_var.set(names[0])
        self._log_local(f"Dostępne scenariusze: {', '.join(names)}")

    def _save_scenario(self) -> None:
        if self.compare_tab is None:
            self._log_local("Brak referencji do CompareTab – nie można zapisać scenariusza.")
            return

        try:
            data = self.compare_tab.export_scenario()
        except Exception as exc:  # noqa: BLE001
            self._log_local(f"[BŁĄD] Nie udało się pobrać scenariusza z Porównania: {exc}")
            self.log_fn(f"[PROJECTS] Błąd export_scenario: {exc}")
            return

        if not data:
            self._log_local("Brak wyników w Porównaniu – nic do zapisania.")
            return

        name = self.name_entry.get().strip()
        if not name:
            name = time.strftime("scenario_%Y%m%d_%H%M%S")

        slug = "".join(c if c.isalnum() or c in "-_." else "_" for c in name)
        path = self.scenario_dir / f"{slug}.json"

        scenario = {
            "name": name,
            "created_at": time.time(),
            "results": data,
        }

        try:
            with path.open("w", encoding="utf-8") as f:
                json.dump(scenario, f, ensure_ascii=False, indent=2)
        except Exception as exc:  # noqa: BLE001
            self._log_local(f"[BŁĄD] Nie udało się zapisać scenariusza: {exc}")
            self.log_fn(f"[PROJECTS] Błąd zapisu scenariusza: {exc}")
            return

        self._log_local(f"Zapisano scenariusz: {name} ({path.name})")
        self.log_fn(f"[PROJECTS] Zapisano scenariusz: {path}")
        self._refresh_scenarios()

    def _load_scenario(self) -> None:
        if self.compare_tab is None:
            self._log_local("Brak referencji do CompareTab – nie można wczytać scenariusza.")
            return

        selected = self.scenario_var.get().strip()
        if not selected or selected == "(brak scenariuszy)":
            self._log_local("Nie wybrano scenariusza do wczytania.")
            return

        path = self.scenario_dir / f"{selected}.json"
        if not path.exists():
            self._log_local(f"[BŁĄD] Plik scenariusza nie istnieje: {path}")
            self.log_fn(f"[PROJECTS] Brak pliku scenariusza: {path}")
            return

        try:
            with path.open("r", encoding="utf-8") as f:
                scenario = json.load(f)
        except Exception as exc:  # noqa: BLE001
            self._log_local(f"[BŁĄD] Nie udało się odczytać scenariusza: {exc}")
            self.log_fn(f"[PROJECTS] Błąd odczytu scenariusza: {exc}")
            return

        results = scenario.get("results") or {}
        try:
            self.compare_tab.import_scenario(results)
        except Exception as exc:  # noqa: BLE001
            self._log_local(f"[BŁĄD] Nie udało się załadować scenariusza do Porównania: {exc}")
            self.log_fn(f"[PROJECTS] Błąd import_scenario: {exc}")
            return

        self._log_local(
            f"Wczytano scenariusz: {scenario.get('name', selected)} – "
            "wyniki zostały załadowane do karty 'Porównanie'."
        )
        self.log_fn(f"[PROJECTS] Wczytano scenariusz z pliku: {path}")
