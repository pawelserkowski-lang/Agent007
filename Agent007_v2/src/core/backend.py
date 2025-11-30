import google.generativeai as genai
from .config import config, logger

class AIBackend:
    def __init__(self):
        self.api_key = config.get_api_key()
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(config.MODEL_NAME)
            self.chat = self.model.start_chat(history=[])
        else:
            self.model = None
            logger.error("AI Backend nie został zainicjowany - brak klucza API.")

    def send_message(self, message: str) -> str:
        if not self.model:
            return "Błąd krytyczny: Brak konfiguracji API."
        
        try:
            # Synchroniczne wywołanie (zostanie owinięte w wątek w UI)
            response = self.chat.send_message(message)
            return response.text
        except Exception as e:
            logger.error(f"Błąd komunikacji z API: {e}")
            return f"Wystąpił błąd API: {str(e)}"
