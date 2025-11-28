
from __future__ import annotations

import customtkinter as ctk


class HelpTab(ctk.CTkFrame):
    """Karta 'Pomoc' – krótkie objaśnienia wszystkich głównych funkcji aplikacji."""
    def __init__(self, parent, **kwargs) -> None:
        super().__init__(parent, fg_color="#e5f2ff", **kwargs)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        text = ctk.CTkTextbox(self, wrap="word")
        text.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)

        content = (
            "EPS Chat Atom – skrócone objaśnienia funkcji:\n\n"
            "• Chat – główny czat z modelami.\n"
            "  Wpisz wiadomość, wybierz modele w panelu MODELE i naciśnij 'Wyślij'.\n"
            "  Przyciski pod polem:\n"
            "    - Autokorekta PL/EN – poprawia pisownię i gramatykę (polski / angielski)\n"
            "      z użyciem pierwszego wybranego modelu. Nic nie wysyła do rozmowy – tylko podmienia tekst w polu.\n"
            "    - EN podgląd – tłumaczy tekst na angielski i pokazuje podgląd przed wysłaniem.\n"
            "      Możesz zaakceptować lub odrzucić tę wersję.\n\n"
            "• MODELE – lewy panel.\n"
            "  Zawiera listę modeli pogrupowanych po providerach (OpenAI, Gemini, itd.).\n"
            "  Zaznaczone modele biorą udział w czacie, Porównaniu i Łańcuchu.\n\n"
            "• Pasek tokenów – na samej górze okna.\n"
            "  Pokazuje przybliżoną liczbę zużytych tokenów i łączny koszt (jeśli skonfigurowany).\n\n"
            "• Porównanie – równoległe odpowiedzi wielu modeli.\n"
            "  – wpisz prompt i naciśnij 'Porównaj'.\n"
            "  – każdy model ma osobne okno z odpowiedzią i statusem.\n"
            "  – selektor kontekstu pozwala użyć poprzednich odpowiedzi jako kontekstu (brak / wszyscy / pojedynczy model).\n"
            "  – pod polem promptu masz przyciski Autokorekta PL/EN i EN podgląd, tak jak w karcie Chat – działają\n"
            "    na treści promptu Porównania, zanim wyślesz go do wszystkich modeli.\n\n"
            "• Łańcuch – pipeline modeli A -> B -> C.\n"
            "  – używa aktualnie wybranych modeli jako kolejnych kroków.\n"
            "  – każdy krok dostaje wynik poprzedniego modelu + ten sam prompt użytkownika.\n"
            "  – przydatne do tworzenia wieloetapowych przepływów (plan -> rozwinięcie -> korekta).\n"
            "  – również tutaj pod polem promptu znajdziesz Autokorektę PL/EN oraz EN podgląd,\n"
            "    aby wygładzić/ przetłumaczyć tekst przed uruchomieniem łańcucha.\n\n"
            "• Projekty – scenariusze Porównania.\n"
            "  – 'Zapisz scenariusz' – zachowuje aktualny stan odpowiedzi z Porównania do pliku JSON.\n"
            "  – 'Wczytaj scenariusz' – ładuje zapisane odpowiedzi z pliku do karty Porównanie.\n\n"
            "• Obrazy – galeria wygenerowanych obrazów.\n"
            "  – możesz tu dodawać obrazy wygenerowane przez modele (z czatu lub osobnych narzędzi).\n"
            "  – kliknięcie miniatury otwiera powiększenie.\n\n"
            "• Log – dziennik zdarzeń systemowych.\n"
            "  – rejestruje m.in. pobieranie listy modeli, użycie ZIP, błędy API, uruchomienia trybów.\n\n"
            "• ZIP – przycisk 'Otwórz ZIP…' w lewym panelu.\n"
            "  – rozpakowuje archiwum ZIP z paskiem postępu (HUD ZIP).\n"
            "  – przydatne np. do szybkiego przygotowania plików projektów.\n\n"
            "Wskazówka: funkcje autokorekty i tłumaczenia korzystają z pierwszego zaznaczonego modelu\n"
            "– dotyczy to karty Chat, Porównanie oraz Łańcuch. Upewnij się, że wybierasz model obsługujący\n"
            "czat tekstowy i dobrze radzący sobie z PL/EN.\n\n"
            "Przykładowe zastosowania modeli (ogólne wskazówki):\n"
            "  – modele 'GPT-4' / 'GPT-4.1' (OpenAI) – bardzo dobre do ogólnej pracy, kodu i PL/EN.\n"
            "  – modele Gemini Pro (Google) – świetne do multimodalu (tekst + obraz) i tłumaczeń.\n"
            "  – modele Claude (Anthropic) – bardzo mocne przy długich dokumentach i analizie tekstu.\n"
            "Dobór konkretnego modelu zależy od Twojego klucza API i dostępnej oferty providera.\n"
        )

        text.insert("end", content)
        text.configure(state="disabled")
