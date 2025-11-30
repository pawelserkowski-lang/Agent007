from pathlib import Path
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
    MODEL_ALIAS: str = "gemini-3-pro-preview"
    API_KEY: str = field(default_factory=get_best_key)
    ROOT_DIR: Path = field(default_factory=lambda: Path(__file__).parent.parent)

CFG = Settings()
