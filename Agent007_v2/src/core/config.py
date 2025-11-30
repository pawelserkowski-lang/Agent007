import os
from pathlib import Path
from dotenv import load_dotenv
import logging

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load .env
load_dotenv()

class AppConfig:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AppConfig, cls).__new__(cls)
            cls._instance.init_config()
        return cls._instance

    def init_config(self):
        self.API_KEY = os.getenv("GOOGLE_API_KEY")
        self.MODEL_NAME = os.getenv("MODEL_NAME", "gemini-1.5-pro")
        
        if not self.API_KEY:
            logger.warning("BRAK KLUCZA API W ZMIENNYCH ŚRODOWISKOWYCH! Ustaw GOOGLE_API_KEY.")

    def get_api_key(self):
        return self.API_KEY

config = AppConfig()
