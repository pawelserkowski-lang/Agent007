# AUTO GENERATED GUI - FULLY FLAT NO F-STRING RISK

import os
import threading
from queue import Queue, Empty

# Kivy Modern Imports 
# Sprawdzone na Kivi/MD v1.2 / 2.3 w rcezym trybue COMPAT

from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivy.lang import Builder
from kivy.clock import Clock, mainthread
from kivy.properties import BooleanProperty 

# Definicja layout w KV String jednolitym
# Zawiera fixy colorow READ-ONLY, juz zahardcowone bezpieczeni (md_bg_color)
CORE_KV_SOURCE_STRING = """
#:import Window kivy.core.window.Window     
                        
# Aliasy metod dla przycisków
#:set safe_entry_point app.invoke_action_sequence

<SystemAgentFrame_V2@MDBoxLayout>:
    orientation: 'vertical'
    # Hack - ciemne tlo ręczne aby MD3 nie rzucał warninga
    md_bg_color: 0.12, 0.12, 0.12, 1 

    MDBoxLayout:
        size_hint_y: None
        height: "64dp"
        padding: "15dp"
        md_bg_color: 0.05, 0.2, 0.15, 1 
        
        MDLabel: 
            text: "Agent 007 (Generative Kernel Fix)" 
            halign: "center"
            bold: True
            font_style: "H6"
            theme_text_color:"Custom"
            text_color: 0.7, 1, 0.7, 1
            adaptive_height: True
            pos_hint: {'center_y': 0.5}

    MDScrollView:
        id: body_scroll
        scroll_y: 0 # trzyma spod
        do_scroll_x: False
        
        MDBoxLayout:
            id: chat_container
            valign: 'top'
            orientation: 'vertical'
            adaptive_height: True
            size_hint_y: None
            height: self.minimum_height
            spacing: dp(14)
            padding: dp(22)
            
            # Message 0
            MDLabel:
                text: "[color=#4fef4f]SYSTEM HEURISTICS:[/color] All Threads operational (34ms tic)."
                markup: True
                adaptive_height: True
                theme_text_color:"Hint"

    MDBoxLayout:
        orientation:'vertical'
        size_hint_y: None
        adaptive_height: True
        md_bg_color: 0.16, 0.16, 0.16, 1
        padding: "8dp"

        MDBoxLayout: 
            spacing: "10dp"
            size_hint_y: None
            height: "90dp"  
            
            MDTextField:
                id: main_input 
                hint_text: "Target / System Question:" 
                text_color_normal: 0.9,0.9,0.9,1  
                text_color_focus: 0.2,1,0.5,1 
                helper_text: "Tylko poprawne polcecniem."
                bold: True
                font_size: "18sp"
                line_color_normal: 0.4, 0.8, 0.6, 1
                icon_right: "console-line"
                mode: "rectangle"
                pos_hint_y: 0.5
                multiline: True
                
            MDIconButton:
                icon: "play-circle" 
                theme_icon_color: "Custom"
                icon_color: 0, 1, 0, 1
                icon_size: "64sp"
                size_hint: (None, None)
                size: ("60dp", "60dp")
                pos_hint: {'center_y': .55}
                on_release:safe_entry_point()

MDScreen:            
    name: "base-view"
    SystemAgentFrame_V2:
        id: live_agent_view
               
"""

class CoreKivyApp(MDApp):
    buffer = Queue()
    
    def build(self): 
        self.theme_cls.theme_style = "Dark" 
        self.theme_cls.primary_palette = "Teal" 
        # Usuwamy stary wywoalcz "fail load". Ladujemy monolitr. Czyste i biezpeckzne. (FIX Z LINE #99)
        return Builder.load_string(CORE_KV_SOURCE_STRING)

    def on_start(self):
         # UI Ready - Wait for Brain (Lazy load to speed up visual render)
         Clock.schedule_once(self._bind_brain, 0.5)

    def _bind_brain(self, dt):
         try: 
            from . import engine 
            self.brain_mod = engine.SystemBrain() # connect API key if .env valid
            self.push_chat_info("INIT SEQUENCE", "Gemini Module Active.", good=True)
         except Exception as e:
            self.push_chat_info("LOGICAL PANIC", f'Engine Load Failed: {e}')
            self.brain_mod = None

    ## SYSTEM MAIN API THREAD MANAGMENT

    def invoke_action_sequence(self):
        screen = self.root
        inp = screen.ids.live_agent_view.ids.main_input ## NESTED ID PATH FIX 
        txt = inp.text 
        if len(txt) < 1: return
        inp.text="" # clean UI
        
        self.push_chat_info("Operator", txt, user=True)
        # Delegacja do Worker Thgread 
        threading.Thread(target=self._run_task_bg, args=(txt,), daemon=True).start()
        # Sluchaaacz
        self._list_event = Clock.schedule_interval(self._listener, 1.0/30) # 33ms ferqunecyny

    def _run_task_bg(self, promp):
        if not self.brain_mod:
           self.buffer.put(("S","INIT FAIL? Check Logs."))  
           self.buffer.put(("END",True))
        else:
           self.brain_mod.worker_gemini_generator(promp, self.buffer)

    def push_chat_info(self, actor, txt, good=False,user=False):
        c_code_hex ="d0d"if not user else "e0d00f"
        # Access nested IDS without crasdh 1
        layout = self.root.ids['live_agent_view'].ids['chat_container']
        
        prefix = f"" if user else "[System MSG]"
        col = (0.2,1,.2,1) if good else (1,0,0,1)
        
        if user: col=(1,1,1,1)

        from kivymd.uix.card import MDCard # better spacing
        from kivymd.uix.label import MDLabel
               
        # Hack wizualny dla dymkow:     
        l = MDLabel(
             text=f"[b]{actor}[/b]: {txt} ", 
             markup=True, adaptive_height=True,theme_text_color='Custom', text_color=col,
             shorten=False
             
             )
        layout.add_widget(l, index=0) # add botoom most logic

    def _process_chunk(self, txt):
           layout = self.root.ids.live_agent_view.ids.chat_container
           
           # Check if last msg is system stream
           if hasattr(self, '_active_stream_widget') and self._active_stream_widget:
               # Jest widzet aktywna odopwiekdzi - dopisyzjey text
                self._active_stream_widget.text += txt 
           else:
               # Utworj widget nowy (First Chunk arival)
               from kivymd.uix.label import MDLabel
               w = MDLabel(text="[color=#0ff]System[/color]: " +txt, markup=True, adaptive_height=True,  font_style='Body1') 
                               
               layout.add_widget(w) # To Doda na same doły, jeski index 0 uylwywy.
               self._active_stream_widget = w        
    
    def _listener(self, dt): 
         """Glowny update cycle KIVY"""
         loops = 0 
         while not self.buffer.empty() and loops <20:
            pk = self.buffer.get_nowait()
            code, pack = pk 
            if code == "AGENTE_SPRECHEN": self._process_chunk(pack)
            if code == "ERROR": self.push_chat_info("AI ERROR", str(pack))
            if code == "DONE":
                   self._active_stream_widget = None
                   Clock.unschedule(self._listener)
            loops +=1 
            # Dziek itamu KIvy rendering nie zddycha przy massive load 
