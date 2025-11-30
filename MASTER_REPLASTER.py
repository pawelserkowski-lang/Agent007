"""
AGENT 007 REFACTOR SCRIPT: OPERATION SKYFALL CLEANUP
To narzędzie Architekta Systemowego. Czyści zastany bajzel, strukturyzuje projektv0.2
i generuje nowoczesny kod Pytania z KivyMD/Gemini.

Instrukcja: 
1. Wklej ten plik do folderu z "Agent007".
2. Zainstaluj biblioteki: pip install kivymd kivy google-generativeai python-dotenv
3. Uruchom skrypt: python MASTER_REPLASTER.py
"""
import os
import shutil
import keyword
from pathlib import Path

# ================= KOD ŹRÓDŁOWY PLIKÓW PROJEKTOWYCH =================

CONFIG_PY_CONTENT = '''from pathlib import Path
from dataclasses import dataclass, field
import os
import logging
from dotenv import load_dotenv

load_dotenv()  # Auto Load .env at startup

# Konfiguracja logowania (Professional Trace)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [CORE-%(module)s]: %(message)s",
    datefmt="%H:%M:%S"
)

@dataclass(frozen=True)
class Settings:
    """Niemodyfikowalny singleton ustawień"""
    APP_NAME: str = "DRUID AGENT v1.6-Stable"
    MODEL_ALIAS: str = os.getenv("GEMINI_MODEL", "gemini-1.5-flash") # 1.5 jest oszczędniejsze
    API_KEY: str = os.getenv("GEMINI_KEY", "")
    VERSION: str = "2.0.0 Refactor"
    
    # Paths construction setup
    ROOT_DIR: Path = field(default_factory=lambda: Path(__file__).parent.parent)

    def sanity_check(self):
        logging.info("--- START ENV VALIDATION ---")
        if not self.API_KEY:
            logging.critical("API KIEY IS MISSING! Sprawdź plik .env Użytkowniku!")
            return False
            # Możemy tu wymuszać, ale w GUI ładniej pokazać błąd
        return True

CFG = Settings()
'''

BRAIN_PY_CONTENT = '''import threading
import types
import generatedcode
import inspect
from queue import  Queue
import logging
import google.generativeai as genai
from .config import CFG

# ZAPOBIEGANIE ZWAIIE: Google SDK
if CFG.API_KEY:
    genai.configure(api_key=CFG.API_KEY)

SAFETY_OFF = { 
  "HARM_CATEGORY_HARASSMENT": "BLOCK_NONE", 
  "HARM_CATEGORY_HATE_SPEECH": "BLOCK_NONE", 
  "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_NONE", 
  "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_NONE"
}

class SystemBrain:
    def __init__(self):
        try:
            self.model = genai.GenerativeModel(
                model_name=CFG.MODEL_ALIAS,
                safety_settings=SAFETY_OFF 
            )
            # Używamy lekkiej historii w pamięci sesji
            self.im_chat = self.model.start_chat(history=[])
        except Exception as e:
            logging.exception("FATA BŁĄD. Czy model jest dobrze nazwany w Config?")
            self.im_chat = None

    def worker_gemini_generator(self, user_inpupt: str, output_queue_ref: Queue):
        """Ten funkcja BIEGNIE W CIENIU - jest w Workr_Worker Thread."""
        try:
            if not self.im_chat:
                output_queue_ref.put(("ERROR", "Brain Disconneceted. No API Key or Init fail."))
                output_queue_ref.put(("DONE", True)) 
                return
            
            # Streaming odpowiedzi
            # Użynamy stream=True, to nie blokuje HTTP requestem na 10 sekund!
            response_generator = self.im_chat.send_message(user_inpupt, stream=True)
            
            for chunk in response_generator:
                txt = chunk.text
                if txt:
                   # Przekazujemy k kawałki (chunks) spowrotem wątku GUI
                   output_queue_ref.put(("AGENTE_SPRECHEN", txt))
            
            output_queue_ref.put(("DONE", "Success"))

        except Exception as e:
            err_msg = str(e)
            output_queue_ref.put(("ERROR", f"CRASH: {err_msg}"))
            output_queue_ref.put(("DONE", True))

''' 

GUI_PY_CONTENT = '''## Pamiętaj -> Interfejs ma być idiotoodporny -> KivyMVVM LITE Style.
from kivy.lang import Builder
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.app import MDApp
# Import Modern Layouts:
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from sys import exit

### THREADING SECIDITY #######:
import threading
from concurrent.futures import ThreadPoolExecutor
# To jst mechanizm Bezpieczny - UI update mozne wywlac tylkco mainthr:ad\t.
from kivy.clock import Clock, mainthread
from queue import Queue, Empty


KEYY_STRING_KV = """
# :kivy 2.3.0
<AgentUI@MDBoxLayout>:
    orientation: 'vertical'
    md_bg_color: 0.1, 0.1, 0.1, 1 
    
    MDTopAppBar:
        title: "Agent 007 v2 [Thread Secured]"
        anchor_title: "left"
        elevation: 2
        md_bg_color: 0.2, 0.4, 0.2, 1
        priority: 10

    ScrollView:
        id: scroller
        scroll_y: 0 # Force scroll bottom on append
        MDBoxLayout:
            id: chat_container
            valign: 'top'
            orientation: 'vertical'
            size_hint_y: None
            adaptive_height: True 
            height: self.minimum_height
            spacing: "15dp"
            padding: "20dp"

	            # Init Placeholder
            MDLabel:
                text: "SYSTEM: Druidic Uplink ready... Ootymisation Check ok."
                theme_text_color: "Custom"
                text_color: "green"
                adaptive_height: True

    MDSeparator:
        height: "2dp"

    MDBoxLayout:
        orientation:'horizontal'
        size_hint_y: None
        padding: 5
        height: 75
        
        MDTextField: # Legacy KIVYMD style might change in v2.0 - use safely
            id: user_input_field
            hint_text: "Co Agent ma naprawuic tym razem?"
            color_mode: 'accent'            
            multiline: False
            mode: "rectangle"

            # Hit Ent to send
            on_text_validate: app.root.get_screen("druidic_main").ids['agent_main'].interact_sequence()

        MDFabButton:
            id: send_button
            icon: "send"
            elevation: 3
			      theme_color: "Custom"
            on_release: app.root.get_screen("druidic_main").ids['agent_main'].interact_sequence()

MDScreen:
    name: "druidic_main"
    AgentUI:
        id: agent_main
"""

class AgentView(MDBoxLayout):  # Logika View-Model
    buffer_queue = Queue() 

    def __init__(self, **kw):
        super().__init__(**kw)
        try:
           # Opuszczamy inicjację "drogiego" modułu Mózgu na start - leniuszek
           Clock.schedule_once(self.late_bind_brain, 2.0)
        except: pass
        self.lock_ui = False
    
    def late_bind_brain(self, *dt):
        from . import engine 
        self.wrapper = engine.SystemBrain() # Brain init
        self.append_bubble("Agent: System gotowy. Gemini 1.5 w tle", "green")

    def interact_sequence(self):
        # 1. Block UI & Get Text
        box = self.ids['user_input_field']
        text = box.text
        if not text: return
        self.toggle_inputs(False) # blokuj guziki

        # 2. Add Bubble Use
        self.append_bubble(f"YOU: {text}", "yellow")
        box.text = '' # clean
        
        # 3. Fire Thread via method
        threading.Thread(target=self.bg_thread_entry, args=(text,), daemon=True).start()
        
        # 4. Spust Cron to nasłuchuje kolejki 30 razy sekunde
        self.buffer_reader_event = Clock.schedule_interval(self.consumer_clock, 1.0/30.0)

    # ------------ To się DZIEJE na THREADZIE POBONJCYZM -----------
    def bg_thread_entry(self, input_txt):
        import time
        if not hasattr(self, 'wrapper'): 
           self.buffer_queue.put(("ERROR", "Boot failed sorry. AI DEAD"))
           time.sleep(1)
           return
        
        # Call Synchro Block in Async Wrapper (paradox naming, clear logic)
        self.wrapper.worker_gemini_generator(input_txt,	self.buffer_queue)
    # -------------------------------------------------------------

    def consumer_clock(self, dt):
        """To nasłuchuje 'listow ze 'swiata watkow' i aplikowuje Kivy-UI update na Text"""
        try:
            while not self.buffer_queue.empty(): # pull all updates that araived in last 33ms; (dont block frames)
                param, payload   = self.buffer_queue.get_nowait()
                
                if param == "AGENTE_SPRECHEN":
                     # To jest STUANL (stream) text. Dokllej do istneijceo.
                     self.stream_current_response(payload)
                
                elif param == "ERROR":
                     self.append_bubble(f"[RED]{payload}", error=True) 
                
                elif param == "DONE":
                     # Release locks
                     self.append_bubble("\\n---- EOT ----", "grey")
                     self.last_stream_widget = None # resey
                     self._release_clock()       
        except Empty: pass

    def stream_current_response(self, text_chunk):
        """Appendowanie do ostatniego lbla jesli to AI nadawalo przed chwiala - to da efekt Pisanai"""
        if hasattr(self, 'last_stream_widget') and self.last_stream_widget:
             if self.last_stream_widget.text == '...':  self.last_stream_widget.text = "" # removeloader
             self.last_stream_widget.text += text_chunk
                
        else: # Nowy chmk p;oprostu
             from kivymd.uix.label import MDLabel
             new_w = MDLabel( 
                  text=text_chunk,
	                  adaptive_height = True, 
	                  text_color = (0, 1, 0, 1), 
                    theme_text_color = "Custom", markup=True)
             self.ids.chat_container.add_widget(new_w)       
             self.last_stream_widget = new_w  
       
    def toggle_inputs(self, active=True):
        self.ids.send_button.disabled = not active

    def _release_clock(self):
         self.toggle_inputs(True)
         Clock.unschedule(self.buffer_reader_event)

    def append_bubble(self, ttt, col='white', error=False):
        from kivymd.uix.label import MDLabel
        widg = MDLabel(text=ttt, size_hint_y=None, height=44)
        if hasattr(widg , 'adaptive_height'): widg.adaptive_height = True
        self.ids.chat_container.add_widget(widg)

class CoreKivyApp(MDApp):
    from . import config # Load setting at entry
    
    def build(self):
        self.theme_cls.theme_style = "Dark" 
        self.theme_cls.error_color = [0.9, 0, 0, 1] 
        self.theme_cls.primary_palette = "Teal"
        return Builder.load_string(KEYY_STRING_KV) # Auto boot kv

'''

BOOT_LAUNCHER_PY="""## START MANAGER ##
import sys
import logging 
from pathlib import Path


# Hard FIX of import paths - zeby python w Kivy widział w ogole moduł src:
LOCAL_SRC = str(Path(__file__).parent / 'src')
sys.path.append(LOCAL_SRC)

if __name__ == '__main__':
    from src.gui import CoreKivyApp
    import socket
    # Pro forma network check 
    try: 
      logging.info(f"Initial boot sequcen loaded...")
      CoreKivyApp().run() # Główna petlą programu GUI uruchamian jest tu i to ona RZADŽI wszystkkcim.
    except Exception as e:
      print("System Failure critical:")
      print(e)
      input("Crash Dumped... press enter")
"""

ENV_FILE_TEMPLATE="""# Pamiętaj, pliki .ENV trzymamy POZA GITHUBEM (.gitignore go juz blokuje)
GEMINI_KEY="WPISZ_TU_SWOJ_NOWIUTKI_KLUCZ_Z_GCOG_KONSOLE"
GEMINI_MODEL="gemini-1.5-pro-lateST"
"""

GITIGNORE_CONT = ".env\n__pycache__\n*.exe\n*.rar\nlog/*.log\n_ARCHIVE/"

def create_structure():
    base = Path.cwd()
    src = base / "src"
    arch = base / "_ARCHIVE_BEFORE_V2"

    print("---[ ROZPOCĘTE NANIESIENIE SYSTEMÓW V2 ]---")
    
    # KROK 1. CLEANUP STAROCI
    # Chodzi o to zeby stare bad-practice pliko nie robiły importu kolizyj
    patterns_to_move = ['napraw*', 'fix*.py', 'Debug*.bat', 'Agent*.spec' , '*.zip'] 
    
    if not arch.exists(): arch.mkdir()
    
    # Scan logic brute fiorcE
    found_garbage = 0 
    cleaned = []
    for fileobj in base.glob('*.py'): 
        if fileobj.name not in ["MASTER_REPLASTER.py", "start_fresh.py"]:
						# Safe check - dont movo dirs
            if fileobj.name in ["start_agenta.py","agent.py","new_test.py"] or fileobj.name.startswith("napraw") or "stare" in str(fileobj) or "backup" in str(fileobj).lower():
                  # Logiczne oznaczenie smieci. Przenies wszystko stare .py w korzzniu jako niebezpiecznen
                shutil.move(str(fileobj), str(arch / fileobj.name))
                cleaned.append(fileobj.name)
                found_garbage += 1


    print(f">> PRZENIISINO {found_garbage} ŚMIECIOWYCH SCRYPTÓW DO FOLDERU /_ARCHIVE... {cleaned[:3]}...")
    
    
    # KROK 2. TWORZENIE NOWCZEKIE (DIR STRUCTURE)
    src.mkdir(exist_ok=True)
    
    with open(src / "__init__.py", "w", encoding='utf-8') as f: f.write("# Source root pkg")
    with open(src / "config.py" ,  "w", encoding='utf-8') as f: f.write(CONFIG_PY_CONTENT)
    with open(src / "engine.py" ,  "w", encoding='utf-8') as f: f.write (BRAIN_PY_CONTENT)
    with open(src / "gui.py",     "w", encoding='utf-8') as f: f.write(GUI_PY_CONTENT)  
    
    # LAUINCHER KIVY w ROOT 
    with open(base / "start_system_v2.py" , "w", encoding='utf-8') as fla: fla.write(BOOT_LAUNCHER_PY)
    
    # Setup Envs if not existsq
    env_p = base / ".env"
    if not env_p.exists():
        with open (env_p, "w", encoding='utf-8') as f: f.write(ENV_FILE_TEMPLATE)
        print(">> UTWORZKZO PLIK KONEIGIRACYJYJ .ENV -> PROSZĘ UZUPEŁNIJ TO ŚRODOWISKE KLUCLEZ!!! (edyruj notatnikiem)") # Literocowkaw zamierdzon - attract eyes 
    
    # Git Ignore safety
    with open(base / ".gitignore", "w") as fg: fg.write(GITIGNORE_CONT)
    
    print("------- SUKCIES ----------")
    print("Nowa Archnitetrua Zaintalopwana p. (MVC Pattern).")
    print("1. Utowzono folder SRC z modulami.")
    print("2. Głowny plik startu do plik: -->   start_system_v2.py     <--.")
    print("PAMNIEAJ: Edytuj .env file wklejaja Klucz GOgoLe gemii!!")
    print("Zainstaluj deps zanim odpalais: 'pip install kivy kivymd filelock python-dotenv google-generativeai --upgrade' ")

if __name__ == "__main__":
    create_structure()