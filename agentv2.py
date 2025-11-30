import os
from pathlib import Path

# --- KONFIGURACJA STRUKTURY PROJEKTU ---
BASE_DIR = Path("Agent007_v2")
SRC_DIR = BASE_DIR / "src"
CORE_DIR = SRC_DIR / "core"
UI_DIR = SRC_DIR / "ui"

dirs = [BASE_DIR, SRC_DIR, CORE_DIR, UI_DIR]
for d in dirs:
    d.mkdir(parents=True, exist_ok=True)
    (d / "__init__.py").touch()

# --- GENEROWANIE PLIKÓW ---

# 1. requirements.txt
req_content = """kivymd==1.1.1
kivy==2.3.0
google-generativeai
python-dotenv
"""
(BASE_DIR / "requirements.txt").write_text(req_content, encoding="utf-8")

# 2. .env (Template)
env_content = """# Zmień nazwę tego pliku na .env i wpisz swój klucz
GOOGLE_API_KEY=TWOJ_KLUCZ_API_TUTAJ
MODEL_NAME=gemini-1.5-flash
"""
(BASE_DIR / ".env.example").write_text(env_content, encoding="utf-8")

# 3. src/core/config.py (Nowoczesna konfiguracja)
config_code = """import os
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
"""
(CORE_DIR / "config.py").write_text(config_code, encoding="utf-8")

# 4. src/core/backend.py (Obsługa Gemini z Error Handling)
backend_code = """import google.generativeai as genai
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
"""
(CORE_DIR / "backend.py").write_text(backend_code, encoding="utf-8")

# 5. src/ui/screens.py (Komponenty UI)
ui_components_code = """from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivy.metrics import dp
from kivy.properties import StringProperty

class ChatBubble(MDCard):
    text = StringProperty()
    sender = StringProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.padding = dp(10)
        self.size_hint_y = None
        self.height = dp(60) # Dynamiczne dostosowanie w prawdziwej appce wymagałoby texture_size
        self.radius = [15, 15, 15, 0] if self.sender == 'bot' else [15, 15, 0, 15]
        self.md_bg_color = (0.1, 0.1, 0.1, 1) if self.sender == 'bot' else (0.2, 0.4, 0.8, 1)
        
        layout = MDBoxLayout(orientation='vertical')
        
        # Sender Label
        sender_lbl = MDLabel(text=self.sender.upper(), theme_text_color="Secondary", font_style="Caption", size_hint_y=None, height=dp(20))
        
        # Message Label
        msg_lbl = MDLabel(text=self.text, theme_text_color="Custom", text_color=(1,1,1,1))
        
        layout.add_widget(sender_lbl)
        layout.add_widget(msg_lbl)
        self.add_widget(layout)
"""
(UI_DIR / "screens.py").write_text(ui_components_code, encoding="utf-8")

# 6. src/ui/app.py (Główna aplikacja + Threading)
app_code = """import threading
from kivy.clock import Clock
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.scrollview import MDScrollView
from kivy.metrics import dp

from src.core.backend import AIBackend
from src.ui.screens import ChatBubble

class MainLayout(MDBoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = dp(20)
        self.spacing = dp(10)
        
        # Backend initialization
        self.backend = AIBackend()

        # Chat History Area
        self.scroll = MDScrollView()
        self.chat_list = MDBoxLayout(orientation='vertical', adaptive_height=True, spacing=dp(10))
        self.scroll.add_widget(self.chat_list)
        
        # Input Area
        input_box = MDBoxLayout(size_hint_y=None, height=dp(60), spacing=dp(10))
        self.text_input = MDTextField(hint_text="Wpisz wiadomość...", mode="rectangle")
        send_btn = MDRaisedButton(text="Wyślij", on_release=self.send_message)
        
        input_box.add_widget(self.text_input)
        input_box.add_widget(send_btn)

        self.add_widget(self.scroll)
        self.add_widget(input_box)

    def send_message(self, instance):
        text = self.text_input.text
        if not text:
            return

        # Add user bubble
        self.add_bubble(text, "user")
        self.text_input.text = ""

        # Run backend in thread to avoid UI Freeze
        threading.Thread(target=self._backend_worker, args=(text,)).start()

    def _backend_worker(self, text):
        response = self.backend.send_message(text)
        # Schedule UI update on Main Thread
        Clock.schedule_once(lambda dt: self.add_bubble(response, "bot"))

    def add_bubble(self, text, sender):
        bubble = ChatBubble(text=text, sender=sender)
        self.chat_list.add_widget(bubble)
        # Auto scroll to bottom currently omitted for brevity, simple scroll usage

class AgentApp(MDApp):
    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "BlueGray"
        return MainLayout()
"""
(UI_DIR / "app.py").write_text(app_code, encoding="utf-8")

# 7. run.py (Entry Point)
run_code = """import sys
from pathlib import Path

# Dodajemy bieżący katalog do sys.path, aby Python widział moduł 'src'
sys.path.append(str(Path(__file__).parent))

from src.ui.app import AgentApp

if __name__ == "__main__":
    AgentApp().run()
"""
(BASE_DIR / "run.py").write_text(run_code, encoding="utf-8")

print(f"✅ Sukces! Zmodernizowany projekt został wygenerowany w folderze: {BASE_DIR.absolute()}")
print("👉 Kolejne kroki:")
print("1. Wejdź do folderu Agent007_v2")
print("2. Zainstaluj biblioteki: pip install -r requirements.txt")
print("3. Zmień nazwę .env.example na .env i dodaj swój API KEY")
print("4. Uruchom: python run.py")