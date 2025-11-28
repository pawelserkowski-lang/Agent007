# EPS Chat Atom 7.x – GUI

To jest pełna wersja modułowa EPS Chat Atom (v7.x) z interfejsem graficznym.

## Wymagania

- Python 3.10+
- System z obsługą Tkinter (Windows / macOS / Linux)
- Zależności z `requirements.txt`:
  - customtkinter
  - pillow
  - requests

## Konfiguracja kluczy API

Ustaw odpowiednie zmienne środowiskowe przed uruchomieniem, np.:

  - OPENAI_API_KEY
  - GEMINI_API_KEY
  - ANTHROPIC_API_KEY
  - MISTRAL_API_KEY
  - COHERE_API_KEY
  - GROQ_API_KEY
  - XAI_API_KEY
  - DEEPSEEK_API_KEY
  - TOGETHER_API_KEY

(opcjonalnie odpowiednie *_BASE_URL dla endpointów OpenAI-compatible).

Panel MODELE pokazuje tylko tych dostawców, dla których ustawiono klucz API.

## Instalacja zależności

W katalogu projektu:

```bash
pip install -r requirements.txt
```

## Uruchomienie GUI

```bash
python run_eps_chat_atom_gui.py
```

Aplikacja otworzy główne okno EPS Chat Atom z kartami:
- Chat
- Porównanie
- Łańcuch
- Obrazy
- Projekty
- Log
- Pomoc
