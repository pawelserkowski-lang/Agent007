import google.generativeai as genai
import PIL.Image
from config.settings import SettingsManager

class GeminiAgent:
    def __init__(self, settings: SettingsManager):
        self.settings = settings
        self.chat_session = None
        self._setup_api()
    def _setup_api(self):
        api_key = self.settings.get("api_key")
        if api_key:
            try: genai.configure(api_key=api_key); return True
            except: return False
        return False
    def list_models(self):
        self._setup_api()
        if not self.settings.get("api_key"): return ["BRAK KLUCZA API"]
        try:
            models = [m.name.replace("models/", "") for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            if "gemini-3-pro-preview" not in models: models.append("gemini-3-pro-preview (Placeholder)")
            return models
        except: return ["Błąd połączenia"]
    def send_message(self, user_message, image_path=None):
        self._setup_api()
        model_name = self.settings.get("model_name").split(" ")[0]
        try:
            model = genai.GenerativeModel(model_name=model_name)
            if not self.chat_session: self.chat_session = model.start_chat(history=[])
            content = [user_message]
            if image_path: content.insert(0, PIL.Image.open(image_path))
            return self.chat_session.send_message(content, stream=True)
        except Exception as e: raise e
