
import os
import sys
import threading

# 1. GPU FIX (Ważne dla kart Intel/Windows)
os.environ['KIVY_GL_BACKEND'] = 'angle_sdl2'

try:
    from kivy.config import Config
    Config.set('graphics', 'width', '1300')
    Config.set('graphics', 'height', '900')
    Config.set('input', 'mouse', 'mouse,multitouch_on_demand')

    from kivymd.app import MDApp
    from kivymd.uix.screen import MDScreen
    from kivymd.uix.boxlayout import MDBoxLayout
    from kivymd.uix.card import MDCard
    from kivymd.uix.list import OneLineIconListItem, IconLeftWidget, MDList
    from kivymd.toast import toast
    from kivymd.uix.menu import MDDropdownMenu
    from kivymd.uix.button import MDIconButton, MDRaisedButton
    from kivymd.uix.textfield import MDTextField
    from kivymd.uix.label import MDLabel
    from kivymd.uix.selectioncontrol import MDSwitch
    from kivymd.uix.slider import MDSlider
    
    from kivy.core.window import Window
    from kivy.core.clipboard import Clipboard
    from kivy.lang import Builder
    from kivy.clock import Clock
    from kivy.properties import StringProperty, ListProperty, BooleanProperty
    from kivy.metrics import dp
    
    from dotenv import load_dotenv
    from backend import GeminiBrain
    
except ImportError as e:
    print(f"CRITICAL ERROR - BRAKUJE BIBLIOTEK: {e}")
    sys.exit(1)

# --- UI DEFINICJE ---
KV_UI = '''
<ChatMessageBubble>:
    orientation: 'vertical'
    size_hint_y: None
    height: self.minimum_height
    padding: [dp(10), dp(5), dp(10), dp(5)]
    
    MDCard:
        orientation: 'vertical'
        size_hint_x: 0.85
        pos_hint: {'right': 1} if root.is_user else {'left': 1}
        md_bg_color: (0.1, 0.25, 0.1, 1) if root.is_user else (0.22, 0.22, 0.22, 1)
        radius: [12]
        padding: dp(15)
        elevation: 0
        
        MDLabel:
            text: root.text
            theme_text_color: "Custom"
            text_color: (0.95, 0.95, 0.95, 1)
            size_hint_y: None
            height: self.texture_size[1]
            markup: True
            font_size: "14sp"
            line_height: 1.4

        MDIconButton:
            icon: "content-copy"
            theme_text_color: "Custom"
            text_color: (0.6, 0.6, 0.6, 1)
            icon_size: "16sp"
            pos_hint: {'right': 1}
            size_hint: None, None
            size: dp(20), dp(20)
            on_release: root.copy_content()

<MainWindow>:
    md_bg_color: (0.08, 0.08, 0.08, 1)
    
    MDBoxLayout:
        orientation: 'horizontal'

        # --- LEWY PANEL (CHAT) ---
        MDBoxLayout:
            orientation: 'vertical'
            size_hint_x: 0.72
            padding: dp(0)
            spacing: dp(0)

            MDScrollView:
                id: chat_scroll
                effect_cls: "ScrollEffect"
                
                MDList:
                    id: chat_list
                    spacing: dp(20)
                    padding: dp(20)

            # INPUT AREA
            MDCard:
                size_hint_y: None
                height: dp(80)
                md_bg_color: (0.12, 0.12, 0.12, 1)
                radius: [0]
                elevation: 3
                padding: [dp(20), dp(10), dp(20), dp(10)]
                
                MDCard:
                    radius: [25]
                    md_bg_color: (0.18, 0.18, 0.18, 1)
                    padding: [dp(15), 0, dp(5), 0]
                    
                    MDTextField:
                        id: user_input
                        hint_text: "Zapytaj o kod, błędy lub analizę..."
                        mode: "line"
                        line_color_normal: (0,0,0,0)
                        line_color_focus: (0,0,0,0)
                        text_color_normal: (1, 1, 1, 1)
                        hint_text_color_normal: (0.5, 0.5, 0.5, 1)
                        pos_hint: {'center_y': 0.5}
                        on_text_validate: app.send_message()

                    MDIconButton:
                        icon: "send-circle"
                        icon_size: "40sp"
                        theme_text_color: "Custom"
                        text_color: (0, 0.8, 0, 1)
                        pos_hint: {'center_y': 0.5}
                        on_release: app.send_message()

        # SEPARATOR
        MDBoxLayout:
            size_hint_x: None
            width: dp(1)
            md_bg_color: (0.25, 0.25, 0.25, 1)

        # --- PRAWY PANEL (CONTROLS) ---
        MDBoxLayout:
            orientation: 'vertical'
            size_hint_x: 0.28
            md_bg_color: (0.15, 0.15, 0.15, 1)

            MDLabel:
                text: "AI CONFIGURATION"
                font_style: "Button"
                halign: "center"
                theme_text_color: "Custom"
                text_color: (0.5, 0.8, 0.5, 1)
                size_hint_y: None
                height: dp(50)
                md_bg_color: (0.12, 0.12, 0.12, 1)

            MDScrollView:
                MDBoxLayout:
                    orientation: 'vertical'
                    adaptive_height: True
                    padding: dp(15)
                    spacing: dp(20)

                    # MODEL
                    MDLabel:
                        text: "MODEL"
                        font_style: "Caption"
                        theme_text_color: "Custom"
                        text_color: (0.7, 0.7, 0.7, 1)
                        size_hint_y: None
                        height: dp(20)

                    MDRaisedButton:
                        id: btn_model
                        text: "gemini-1.5-pro"
                        md_bg_color: (0.25, 0.25, 0.25, 1)
                        size_hint_x: 1
                        elevation: 0
                        on_release: app.open_model_menu()

                    # SYSTEM INSTRUCTIONS
                    MDLabel:
                        text: "SYSTEM INSTRUCTIONS"
                        font_style: "Caption"
                        theme_text_color: "Custom"
                        text_color: (0.7, 0.7, 0.7, 1)
                        size_hint_y: None
                        height: dp(20)
                    
                    MDCard:
                        size_hint_y: None
                        height: dp(100)
                        md_bg_color: (0.1, 0.1, 0.1, 1)
                        padding: dp(8)
                        radius: [5]
                        
                        MDTextField:
                            id: sys_instr
                            text: "Jesteś Senior Python Developerem."
                            mode: "fill"
                            fill_color_normal: (0,0,0,0)
                            active_line: False
                            multiline: True
                            text_color_normal: (0.9, 0.9, 0.9, 1)
                            font_size: "13sp"

                    # TOOLS
                    MDLabel:
                        text: "TOOLS"
                        font_style: "Caption"
                        theme_text_color: "Custom"
                        text_color: (0.7, 0.7, 0.7, 1)
                        size_hint_y: None
                        height: dp(20)

                    MDBoxLayout:
                        size_hint_y: None
                        height: dp(40)
                        MDLabel:
                            text: "Google Search"
                            theme_text_color: "Custom"
                            text_color: (0.9, 0.9, 0.9, 1)
                            font_size: "14sp"
                        MDSwitch:
                            id: switch_search
                            active: True
                            thumb_color_active: (0, 0.8, 0, 1)

                    MDBoxLayout:
                        size_hint_y: None
                        height: dp(40)
                        MDLabel:
                            text: "Code Execution"
                            theme_text_color: "Custom"
                            text_color: (0.9, 0.9, 0.9, 1)
                            font_size: "14sp"
                        MDSwitch:
                            id: switch_code
                            active: True
                            thumb_color_active: (0, 0.8, 0, 1)

                    # FILES
                    MDLabel:
                        text: "CONTEXT FILES (Drag & Drop)"
                        font_style: "Caption"
                        theme_text_color: "Custom"
                        text_color: (0.7, 0.7, 0.7, 1)
                        size_hint_y: None
                        height: dp(20)
                    
                    MDList:
                        id: file_list
                        bg_color: (0.1, 0.1, 0.1, 1)
                        spacing: dp(5)
'''

# --- LOGIKA APLIKACJI ---

class ChatMessageBubble(MDBoxLayout):
    text = StringProperty("")
    is_user = BooleanProperty(True)
    def copy_content(self):
        Clipboard.copy(self.text)
        toast("Skopiowano!")

class MainWindow(MDScreen):
    pass

class DebugDruidApp(MDApp):
    dropped_files = ListProperty([])
    current_model = StringProperty("gemini-1.5-pro")

    def build(self):
        self.title = "Agent 007 - Production Console"
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Green"
        
        load_dotenv()
        try:
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                print("WARNING: Brak klucza API!")
            self.brain = GeminiBrain(api_key=api_key)
        except Exception as e:
            print(f"Brain Error: {e}")

        Window.bind(on_drop_file=self._on_file_drop)
        
        # --- FIX KLUCZOWY ---
        Builder.load_string(KV_UI) # Najpierw załaduj KV
        return MainWindow()        # Potem zwróć instancję klasy
        # --------------------

    def on_start(self):
        # Menu Modeli
        menu_items = [
            {"text": "gemini-1.5-pro", "viewclass": "OneLineListItem", "on_release": lambda x="gemini-1.5-pro": self.set_model(x)},
            {"text": "gemini-1.5-flash", "viewclass": "OneLineListItem", "on_release": lambda x="gemini-1.5-flash": self.set_model(x)},
            {"text": "gemini-2.0-flash-exp", "viewclass": "OneLineListItem", "on_release": lambda x="gemini-2.0-flash-exp": self.set_model(x)},
        ]
        
        if hasattr(self.root.ids, 'btn_model'):
            self.menu = MDDropdownMenu(
                caller=self.root.ids.btn_model, items=menu_items, width_mult=4
            )
            self.root.ids.chat_list.add_widget(
                ChatMessageBubble(
                    text="[color=#00ff00]SYSTEM ONLINE.[/color] Czekam na rozkazy.", 
                    is_user=False
                )
            )

    def open_model_menu(self):
        self.menu.open()

    def set_model(self, name):
        self.current_model = name
        self.root.ids.btn_model.text = name
        self.menu.dismiss()
        toast(f"Model: {name}")

    def _on_file_drop(self, window, file_path, x, y):
        path_str = file_path.decode("utf-8")
        if path_str not in self.dropped_files:
            self.dropped_files.append(path_str)
            item = OneLineIconListItem(
                text=os.path.basename(path_str),
                theme_text_color="Custom",
                text_color=(0.9, 0.9, 0.9, 1),
                bg_color=(0.2, 0.2, 0.2, 1),
                radius=[5]
            )
            icon = IconLeftWidget(icon="file-document-outline", theme_text_color="Custom", text_color=(0,1,0,1))
            item.add_widget(icon)
            self.root.ids.file_list.add_widget(item)
            self.root.ids.chat_list.add_widget(ChatMessageBubble(text=f"Dodano plik: {os.path.basename(path_str)}", is_user=True))

    def send_message(self):
        inp = self.root.ids.user_input
        txt = inp.text.strip()
        if not txt: return
        
        self.root.ids.chat_list.add_widget(ChatMessageBubble(text=txt, is_user=True))
        inp.text = ""

        settings = {
            'model': self.current_model,
            'sys': self.root.ids.sys_instr.text,
            'search': self.root.ids.switch_search.active,
            'code': self.root.ids.switch_code.active,
            'temp': 1.0
        }
        threading.Thread(target=self._brain_worker, args=(txt, settings, list(self.dropped_files))).start()

    def _brain_worker(self, text, settings, files):
        try:
            if not self.brain:
                response = "Error: Backend offline."
            else:
                self.brain.prepare_model(
                    model_name=settings['model'],
                    sys_instruct=settings['sys'],
                    enable_search=settings['search'],
                    enable_code=settings['code'],
                    temp=settings['temp']
                )
                response = self.brain.send_query(text, files)
        except Exception as e:
            response = f"Error: {e}"

        Clock.schedule_once(lambda dt: self._update_chat(response))

    def _update_chat(self, text):
        self.root.ids.chat_list.add_widget(ChatMessageBubble(text=text, is_user=False))

if __name__ == "__main__":
    DebugDruidApp().run()
