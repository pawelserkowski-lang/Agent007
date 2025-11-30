import os
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
    logs_text = StringProperty("--- DEBUG DRUID v42.0 [STRICT MODE] ---\n")
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
        self.logs_text += msg + "\n"

    def update_api_key(self, text):
        toast("Zmiana klucza zablokowana. Użyj zmiennych systemowych.")

    def refresh_model_discovery(self):
        toast("Model jest zablokowany (Strict Mode).")
