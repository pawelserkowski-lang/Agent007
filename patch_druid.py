import os
import sys

# Definicje plików i ich nowej zawartości
FILES_TO_PATCH = {
    "src/config.py": """from pathlib import Path
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
""",

    "src/engine.py": """import threading
import logging
import google.generativeai as genai
from queue import Queue
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from .config import CFG

try:
    genai.configure(api_key=CFG.API_KEY)
except Exception as e:
    logging.critical(f"Google AI SDK Configuration Failed: {e}")

SAFETY_SETTINGS = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
}

class SystemBrain:
    def __init__(self):
        self.chat_session = None
        self._init_model()

    def _init_model(self):
        try:
            logging.info(f"Initializing Model: {CFG.MODEL_ALIAS}")
            self.model = genai.GenerativeModel(
                model_name=CFG.MODEL_ALIAS,
                safety_settings=SAFETY_SETTINGS
            )
            self.chat_session = self.model.start_chat(history=[])
            logging.info("Brain Module: Online")
        except Exception as e:
            logging.error(f"Brain Init Error: {e}")
            self.chat_session = None

    def worker_gemini_generator(self, user_input: str, output_queue: Queue):
        if not self.chat_session:
            output_queue.put(("ERROR", "Brain Disconnected. Restart Application."))
            output_queue.put(("DONE", "Failed"))
            return

        try:
            response = self.chat_session.send_message(user_input, stream=True)
            
            for chunk in response:
                try:
                    text_part = chunk.text
                    if text_part:
                        output_queue.put(("MSG_CHUNK", text_part))
                except ValueError:
                    logging.warning("Empty chunk received (Safety Filter or Network artifact).")
                    continue

            output_queue.put(("DONE", "Success"))

        except Exception as e:
            error_msg = str(e)
            logging.error(f"Gemini Runtime Error: {error_msg}")
            output_queue.put(("ERROR", f"AI Error: {error_msg}"))
            output_queue.put(("DONE", "Crash"))

print("DEBUG > Brain Module Loaded.")
""",

    "ui/app.py": """import os
import sys
import json
import threading
import logging
import webbrowser
from kivy.lang import Builder
from kivy.properties import StringProperty, BooleanProperty, ListProperty, NumericProperty
from kivy.clock import Clock
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.list import OneLineListItem
from kivymd.toast import toast

from src.config import CFG
from src.engine import SystemBrain

try:
    from core.database import DatabaseManager
except ImportError:
    class DatabaseManager:
        def get_sessions(self): return []
        def get_messages(self, x): return []
        def delete_session(self, x): pass
    logging.warning("Core Database not found - using Mock.")

from core.logger import KivyLogHandler
from ui.widgets.session_item import SessionItem

def resource_path(relative_path):
    try: base_path = sys._MEIPASS
    except: base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class MainLayout(MDBoxLayout): pass
class RightControlPanel(MDBoxLayout): pass
class ModelListItem(OneLineListItem): pass

class DebugDruidApp(MDApp):
    logs_text = StringProperty("--- DEBUG DRUID v42.0 [STRICT MODE] ---\\n")
    current_main_model = StringProperty(CFG.MODEL_ALIAS)
    api_key = StringProperty(CFG.API_KEY)
    current_session_title = StringProperty("Nowa Sesja")
    current_session_id = NumericProperty(-1)
    use_google_search = BooleanProperty(True)
    is_dark_mode = BooleanProperty(False)
    param_temperature = NumericProperty(0.2)
    param_max_tokens = NumericProperty(8192)
    github_repo = StringProperty("")
    github_branch = StringProperty("main")
    github_files = StringProperty("")
    github_token = StringProperty("")

    def build(self):
        self.theme_cls.theme_style = "Light"
        self.theme_cls.primary_palette = "Blue"
        self.title = "DebugDruid (Gemini 3 Pro)"
        try: self.icon = resource_path("ikona.webp")
        except: pass
        
        log_handler = KivyLogHandler(self)
        logging.getLogger().addHandler(log_handler)

        self.db = DatabaseManager()
        
        logging.info("Inicjalizacja SystemBrain...")
        self.brain = SystemBrain()
        
        Builder.load_file(resource_path(os.path.join("ui", "layout.kv")))
        return MainLayout()

    def on_start(self):
        self._log_status()
        Clock.schedule_once(lambda dt: self.refresh_sessions_list(), 0.5)

    def _log_status(self):
        masked_key = f"{self.api_key[:4]}...{self.api_key[-4:]}" if len(self.api_key) > 8 else "INVALID"
        logging.info(f"[STRICT MODE] API Key Source: ENV (Windows)")
        logging.info(f"[STRICT MODE] Key Loaded: {masked_key}")
        logging.info(f"[STRICT MODE] Model Locked: {self.current_main_model}")

    def on_stop(self): 
        pass

    def refresh_sessions_list(self):
        try:
            history_list = self.root.ids.history_list
            history_list.clear_widgets()
            sessions = self.db.get_sessions()
            for sess_id, title in sessions:
                item = SessionItem(text=title, session_id=sess_id, title=title)
                history_list.add_widget(item)
        except Exception as e:
            logging.error(f"Error loading sessions: {e}")

    def start_new_chat(self):
        self.current_session_id = -1
        self.current_session_title = "Nowa Sesja"
        if self.brain.chat_session:
            self.brain.chat_session.history = []
        
        chat_screen = self.root.ids.get('chat_screen')
        if chat_screen:
            chat_screen.clear_view()
            
        nav = self.root.ids.get('nav_drawer_left')
        if nav: nav.set_state("close")

    def load_session(self, session_id):
        self.current_session_id = session_id
        self.root.ids.nav_drawer_left.set_state("close")

    def append_log(self, msg):
        self.logs_text += msg + "\\n"

    def update_api_key(self, text):
        toast("Zmiana klucza zablokowana. Użyj zmiennych systemowych.")

    def refresh_model_discovery(self):
        toast("Model jest zablokowany (Strict Mode).")
""",

    "ui/screens/chat.py": """import time
import os
import threading
import queue
from kivy.core.window import Window
from kivy.clock import Clock, mainthread
from kivy.properties import BooleanProperty
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.app import MDApp
from ui.widgets.file_item import FileItem
from ui.widgets.bubble import ChatBubble

class ChatScreenLogic(MDBoxLayout):
    is_processing = BooleanProperty(False)
    start_time = 0
    loaded_files = []
    
    current_streaming_bubble = None

    def on_kv_post(self, base_widget):
        Window.bind(on_drop_file=self._on_file_drop)

    def _on_file_drop(self, window, file_path, x, y):
        try:
            path = file_path.decode('utf-8')
            self.add_file_to_panel(path)
        except Exception as e:
            print(f"File Drop Error: {e}")

    def add_file_to_panel(self, path):
        for item in self.loaded_files:
            if item.filepath == path: return
        item = FileItem(filepath=path, remove_func=self.remove_file)
        self.ids.file_container.add_widget(item)
        self.loaded_files.append(item)

    def remove_file(self, item_widget):
        if item_widget in self.loaded_files:
            self.loaded_files.remove(item_widget)
            self.ids.file_container.remove_widget(item_widget)

    def clear_attachments(self):
        for item in list(self.loaded_files):
            self.remove_file(item)
        self.loaded_files = []

    def send_message(self):
        text = self.ids.message_input.text.strip()
        
        if not text and not self.loaded_files:
            return

        app = MDApp.get_running_app()
        
        full_prompt = text
        if self.loaded_files:
            full_prompt += "\\n\\n--- KONTEKST Z PLIKÓW ---\\n"
            for item in self.loaded_files:
                try:
                    with open(item.filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()[:20000] 
                        full_prompt += f"\\n>>> PLIK: {item.filename}\\n{content}\\n"
                except Exception as e:
                    full_prompt += f"\\n>>> PLIK: {item.filename} (Błąd odczytu: {e})\\n"

        display_text = text if text else f"[Wysłano {len(self.loaded_files)} plików]"
        self.add_bubble(display_text, is_user=True)
        self.ids.message_input.text = ""
        self.clear_attachments()
        
        self.start_timer()
        self.current_streaming_bubble = None 
        
        if hasattr(app, 'brain'):
            self.response_queue = queue.Queue()
            
            threading.Thread(
                target=app.brain.worker_gemini_generator,
                args=(full_prompt, self.response_queue),
                daemon=True
            ).start()
            
            Clock.schedule_interval(self._consume_queue, 0.05)
        else:
            self.add_bubble("CRITICAL: SystemBrain not connected.", is_user=False)
            self.stop_timer()

    def _consume_queue(self, dt):
        try:
            while not self.response_queue.empty():
                msg_type, content = self.response_queue.get_nowait()
                
                if msg_type == "MSG_CHUNK":
                    self._update_streaming_bubble(content)
                
                elif msg_type == "ERROR":
                    self.add_bubble(f"BŁĄD: {content}", is_user=False)
                
                elif msg_type == "DONE":
                    self.stop_timer()
                    self.current_streaming_bubble = None
                    return False 
                    
        except queue.Empty:
            pass
        return True

    @mainthread
    def _update_streaming_bubble(self, chunk):
        if not self.current_streaming_bubble:
            self.current_streaming_bubble = self.add_bubble("", is_user=False)
        
        if hasattr(self.current_streaming_bubble, 'text'):
            self.current_streaming_bubble.text += chunk
        else:
            print(f"DEBUG STREAM: {chunk}")

    def add_bubble(self, text, is_user):
        bubble = ChatBubble(text=text, is_user=is_user)
        self.ids.chat_list.add_widget(bubble)
        self.ids.scroll_view.scroll_to(bubble)
        return bubble

    def clear_view(self):
        self.ids.chat_list.clear_widgets()
        self.stop_timer()

    def start_timer(self):
        self.is_processing = True
        self.ids.progress_bar.start()
        self.start_time = time.time()
        self.timer_event = Clock.schedule_interval(self.update_timer, 0.05)

    def stop_timer(self):
        self.is_processing = False
        self.ids.progress_bar.stop()
        if hasattr(self, 'timer_event') and self.timer_event: 
            self.timer_event.cancel()

    def update_timer(self, dt):
        self.ids.timer_label.text = f"{time.time() - self.start_time:.2f}s"
""",

    "requirements.txt": """kivy>=2.3.0
kivymd>=1.2.0
google-generativeai>=0.4.0
python-dotenv
Pillow
docutils
"""
}

def apply_patch():
    print("--- DEBUG DRUID PATCHER ---")
    
    # Ensure directories exist
    os.makedirs("src", exist_ok=True)
    os.makedirs(os.path.join("ui", "screens"), exist_ok=True)
    
    for filepath, content in FILES_TO_PATCH.items():
        try:
            # Handle potential path separators for Windows
            safe_path = os.path.normpath(filepath)
            
            with open(safe_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"[OK] Patched: {safe_path}")
        except Exception as e:
            print(f"[ERROR] Failed to patch {filepath}: {e}")
            
    print("\nPATCH APPLIED SUCCESSFULLY.")
    print("Next steps:")
    print("1. Set GEMINI_API_KEY in Windows Environment Variables.")
    print("2. Run your application.")

if __name__ == "__main__":
    apply_patch()