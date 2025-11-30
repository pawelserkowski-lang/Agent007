"""
FIX OSTATECZNY:
1. Wymuszenie modelu 'gemini-1.5-flash' (jest darmowy, szybki i stabilny).
2. Naprawa GUI, żeby pokazywało PRAWDZIWY błąd (np. 404, 403), a nie "Patrz Terminal".
"""
from pathlib import Path

# 1. NAPRAWA KONFIGURACJI (Wymuszenie flasha)
CONFIG_PATH = Path("src/config.py")
NEW_CONFIG = r'''from pathlib import Path
from dataclasses import dataclass, field
import os
import logging
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s]: %(message)s")

# Load Env (override=True ensures file fixes logic if env vars are messy, but System vars have priority logic below)
load_dotenv()

def get_best_key():
    # Szukamy klucza w systemie (PRIORYTET)
    candidates = ["GEMINI_KEY", "GOOGLE_API_KEY", "GEMINI_API_KEY"]
    for c in candidates:
        val = os.environ.get(c)
        if val and len(val) > 20 and "WPISZ" not in val:
            return val
    # Fallback to config file content check handled by os.getenv check above mostly
    return ""

@dataclass(frozen=True)
class Settings:
    APP_NAME: str = "DRUID AGENT v2.2-Final"
    # ZMIANA: Sztywny, bezpieczny model. Usunięto błędy 'lateST'.
    MODEL_ALIAS: str = "gemini-1.5-flash"
    API_KEY: str = field(default_factory=get_best_key)
    ROOT_DIR: Path = field(default_factory=lambda: Path(__file__).parent.parent)

CFG = Settings()
'''

# 2. NAPRAWA GUI (Odblokowanie komunikatów błędów)
GUI_PATH = Path("src/gui.py")
# Wczytujemy plik GUI i podmieniamy "złą" linijkę na "dobrą"
if GUI_PATH.exists():
    with open(GUI_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Podmiana blokady błędów
    # Stare (złe): if code == "ERROR": self.push_chat_info("AI ERROR","Złapano wyjatek modelu. Patrz Terminal.")
    # Nowe (dobre): if code == "ERROR": self.push_chat_info("AI ERROR", pack)
    
    if 'self.push_chat_info("AI ERROR","Złapano wyjatek modelu. Patrz Terminal.")' in content:
        content = content.replace(
            'self.push_chat_info("AI ERROR","Złapano wyjatek modelu. Patrz Terminal.")',
            'self.push_chat_info("AI ERROR", str(pack))' # Pokaż co boli
        )
    elif 'if code == "ERROR": self.push_chat_info("AI ERROR","Złapano wyjatek modelu. Patrz Terminal.")' in content:
         # Fallback dla formatowania
         content = content.replace(
            'if code == "ERROR": self.push_chat_info("AI ERROR","Złapano wyjatek modelu. Patrz Terminal.")',
            'if code == "ERROR": self.push_chat_info("AI ERROR", str(pack))'
         )

    with open(GUI_PATH, "w", encoding="utf-8") as f:
        f.write(content)
    print(">> GUI naprawione: Błędy będą widoczne na ekranie.")

# Zapis Configu
with open(CONFIG_PATH, "w", encoding="utf-8") as f:
    f.write(NEW_CONFIG)
print(">> Config naprawiony: Model ustawiony na 'gemini-1.5-flash'.")

print("-" * 40)
print("GOTOWE. Uruchom teraz: python start_system_v2.py")
print("Agent POWINIEN odpowiedzieć.")