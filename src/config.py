from pathlib import Path
from dataclasses import dataclass, field
import os
import sys
import logging

# Konfiguracja logowania
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s]: %(message)s")

def get_strict_system_key():
    val = os.environ.get("GEMINI_API_KEY")
    
    if not val:
        logging.critical("CRITICAL ERROR: 'GEMINI_API_KEY' not found in System Environment Variables.")
        logging.critical("ACTION REQUIRED: Set GEMINI_API_KEY in Windows (sysdm.cpl > Environment Variables).")
        sys.exit(1)
        
    if "WPISZ" in val or len(val) < 20:
        logging.critical("CRITICAL ERROR: 'GEMINI_API_KEY' seems invalid/placeholder.")
        sys.exit(1)
        
    return val

@dataclass(frozen=True)
class Settings:
    APP_NAME: str = "DRUID AGENT v2.2-Final"
    MODEL_ALIAS: str = "gemini-3-pro-preview"
    API_KEY: str = field(default_factory=get_strict_system_key)
    ROOT_DIR: Path = field(default_factory=lambda: Path(__file__).parent.parent)

try:
    CFG = Settings()
except Exception as e:
    logging.critical(f"Config Init Failed: {e}")
    sys.exit(1)
