"""
PATCH CONFIGU - PRIORYTET SYSTEMOWY
Ten skrypt modyfikuje src/config.py tak, aby:
1. Szukał zmiennych środowiskowych SYSTEMU (Windows) przed plikiem .env.
2. Obsługiwał alternatywne nazwy (GEMINI_KEY oraz GOOGLE_API_KEY).
3. Ignorował placeholder "WPISZ_TU_SWOJ...", jeśli ktoś zapomniał go usunąć z pliku.
"""
from pathlib import Path

TARGET = Path("src/config.py")

NEW_CONFIG_CONTENT = r'''from pathlib import Path
from dataclasses import dataclass, field
import os
import logging
from dotenv import load_dotenv

# Logowanie
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [CORE-%(module)s]: %(message)s",
    datefmt="%H:%M:%S"
)

# 1. Najpierw ładujemy .env, ale z flagą override=False
# To oznacza: "Jeśli zmienna już jest w Windowsie, NIE ZMIENIAJ JEJ. Użyj pliku tylko jeśli w systemie braku".
load_dotenv(override=False)

def get_clean_api_key():
    """Inteligentne pobieranie klucza - System First, File Second, Dummy Ignore."""
    # Lista zmiennych, pod którymi użytkownik mógł ustawić klucz w Windowsie
    possible_vars = ["GEMINI_KEY", "GOOGLE_API_KEY", "GEMINI_API_KEY"]
    
    for var_name in possible_vars:
        val = os.getenv(var_name)
        
        # Filtrowanie "śmieci" - jeśli wczytał się placeholder z pliku, ignorujemy go
        if val and "WPISZ_" not in val and len(val) > 10:
            logging.info(f"Klucz znaleziony w zmiennej: {var_name}")
            return val
            
    return ""

@dataclass(frozen=True)
class Settings:
    """Niemodyfikowalny singleton ustawień"""
    APP_NAME: str = "DRUID AGENT v1.6-Stable"
    # Pobieramy model z env lub default
    MODEL_ALIAS: str = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    
    # INTELIGENTNE POBIERANIE KLUCZA
    API_KEY: str = field(default_factory=get_clean_api_key)
    
    VERSION: str = "2.1.0 Env-System-First"
    
    # Paths construction setup
    ROOT_DIR: Path = field(default_factory=lambda: Path(__file__).parent.parent)

    def sanity_check(self):
        if not self.API_KEY:
            # Nie crashujemy tutaj, GUI to obsłuży ładniej
            logging.warning("!!! BRAK KLUCZA API !!! Aplikacja może nie działać.")
            return False
        return True

CFG = Settings()
'''

if __name__ == "__main__":
    with open(TARGET, "w", encoding="utf-8") as f:
        f.write(NEW_CONFIG_CONTENT)
    print("[OK] Config zaktualizowany.")
    print("   Teraz aplikacja najpierw sprawdza zmienne systemu Windows: GEMINI_KEY lub GOOGLE_API_KEY.")
    print("   Ignoruje też wpisy typu 'WPISZ_TU_SWOJ...' z pliku .env.")