import os
import sys
import logging
from kivy.lang import Builder
from kivy.properties import StringProperty, BooleanProperty, NumericProperty
from kivy.clock import Clock
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.list import OneLineListItem
from kivymd.toast import toast

from src.config import CFG

# Mock Database & Logger imports (zachowane z poprzedniej fazy)
try:
    from core.database import DatabaseManager
except ImportError:
    class DatabaseManager:
        def get_sessions(self): return []
        def delete_session(self, x): pass
try:
    from core.logger import KivyLogHandler
except ImportError:
    KivyLogHandler = None

def resource_path(relative_path):
    try: base_path = sys._MEIPASS
    except: base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class MainLayout(MDBoxLayout): pass

class DebugDruidApp(MDApp):
    # State Properties
    logs_text = StringProperty("--- SYSTEM READY ---\n")
    current_main_model = StringProperty(CFG.MODEL_ALIAS)
    api_key = StringProperty(CFG.API_KEY)
    current_session_title = StringProperty("New Session")
    current_session_id = NumericProperty(-1)
    
    # Config Flags
    use_google_search = BooleanProperty(True)
    is_dark_mode = BooleanProperty(True) # FORCE DARK
    param_auto_save_files = BooleanProperty(True)
    param_stackoverflow = BooleanProperty(False)
    
    # AI Params
    param_temperature = NumericProperty(0.2)
    param_max_tokens = NumericProperty(8192)
    param_custom_text = StringProperty("")
    
    # Github (Stub)
    github_repo = StringProperty("")
    github_branch = StringProperty("main")
    github_files = StringProperty("")
    github_token = StringProperty("")

    def build(self):
        # --- MODERNIZACJA GUI: DARK GREEN CYBERPUNK ---
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Green"
        self.theme_cls.accent_palette = "LightGreen"
        self.theme_cls.material_style = "M3"
        
        self.title = "Agent 007 [Command Console]"
        try: self.icon = resource_path("ikona.webp")
        except: pass
        
        if KivyLogHandler: logging.getLogger().addHandler(KivyLogHandler(self))
        self.db = DatabaseManager()
        
        # Lazy Load Engine
        logging.info("Booting Neural Engine...")
        try:
            from src.engine import SystemBrain
            self.brain = SystemBrain()
        except Exception as e:
            logging.critical(f"Engine Failure: {e}")
            self.brain = None
        
        kv_path = resource_path(os.path.join("ui", "layout.kv"))
        Builder.load_file(kv_path)
        return MainLayout()

    def on_start(self):
        # Clean start
        pass

    # --- Actions ---
    def start_new_chat(self):
        self.root.ids.chat_screen.clear_view()
        self.current_session_title = "Nowa Sesja"
        if self.brain and self.brain.chat_session:
            self.brain.chat_session.history = []

    def refresh_sessions_list(self): pass 
    def append_log(self, msg): self.logs_text += msg + "\n"
    def update_api_key(self, text): toast("Access Denied: ENV Variables Only")
    def fetch_github_files(self): toast("Module Offline")
    def refresh_model_discovery(self): toast("Model Locked")