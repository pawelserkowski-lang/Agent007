import os
import sys
import threading
from pathlib import Path

# --- DEPENDENCIES CHECK ---
try:
    from kivymd.app import MDApp
    from kivymd.uix.screen import MDScreen
    from kivymd.uix.boxlayout import MDBoxLayout
    from kivymd.uix.card import MDCard
    from kivymd.uix.list import OneLineIconListItem, IconLeftWidget
    from kivymd.toast import toast
    from kivymd.uix.menu import MDDropdownMenu
    from kivymd.uix.button import MDIconButton
    
    from kivy.core.window import Window
    from kivy.core.clipboard import Clipboard
    from kivy.lang import Builder
    from kivy.clock import Clock
    from kivy.properties import StringProperty, ListProperty, BooleanProperty
    from kivy.metrics import dp
    
    import google.generativeai as genai
    from dotenv import load_dotenv
except ImportError as e:
    print(f"CRITICAL: Brak bibliotek! Uruchom: pip install kivymd==1.1.1 google-generativeai python-dotenv\nError: {e}")
    sys.exit(1)

# --- UI LAYOUT (KV) ---
KV_INTERFACE = '''
<TooltipMDIconButton@MDIconButton+MDTooltip>

<ChatMessageBubble>:
    orientation: 'vertical'
    size_hint_y: None
    height: self.minimum_height
    padding: dp(10)
    spacing: dp(5)
    
    MDCard:
        orientation: 'vertical'
        size_hint_x: 0.85
        pos_hint: {'right': 1} if root.is_user else {'left': 1}
        md_bg_color: app.theme_cls.primary_color if root.is_user else (0.2, 0.2, 0.2, 1)
        radius: [15, 15, 0, 15] if root.is_user else [15, 15, 15, 0]
        elevation: 1
        padding: dp(10)
        
        MDLabel:
            text: root.text
            theme_text_color: "Custom"
            text_color: (1, 1, 1, 1)
            size_hint_y: None
            height: self.texture_size[1]
            markup: True

        MDIconButton:
            icon: "content-copy"
            theme_text_color: "Custom"
            text_color: (1, 1, 1, 0.5)
            icon_size: "16sp"
            pos_hint: {'right': 1}
            size_hint: None, None
            size: dp(24), dp(24)
            on_release: root.copy_content()

<MainWindow>:
    MDBoxLayout:
        orientation: 'horizontal'

        # --- LEWY PANEL (CHAT) ---
        MDBoxLayout:
            orientation: 'vertical'
            size_hint_x: 0.7
            padding: dp(10)
            spacing: dp(10)

            MDScrollView:
                id: chat_scroll
                MDList:
                    id: chat_list
                    spacing: dp(10)
                    padding: dp(10)

            MDBoxLayout:
                size_hint_y: None
                height: dp(60)
                spacing: dp(10)
                padding: [0, 10, 0, 10]

                MDTextField:
                    id: user_input
                    hint_text: "Zapytaj DebugDruida..."
                    mode: "round"
                    multiline: False
                    on_text_validate: app.send_message()
                    # Poprawka dla ciemnego motywu
                    current_hint_text_color: 0.6, 0.6, 0.6, 1
                    line_color_normal: 0.6, 0.6, 0.6, 1

                MDIconButton:
                    icon: "send"
                    theme_text_color: "Custom"
                    text_color: app.theme_cls.primary_color
                    on_release: app.send_message()

        # --- SEPARATOR ---
        MDBoxLayout:
            size_hint_x: None
            width: dp(1)
            md_bg_color: (0.3, 0.3, 0.3, 1)

        # --- PRAWY PANEL (USTAWIENIA) ---
        MDScrollView:
            size_hint_x: 0.3
            md_bg_color: (0.12, 0.12, 0.12, 1)
            
            MDBoxLayout:
                orientation: 'vertical'
                padding: dp(15)
                spacing: dp(20)
                size_hint_y: None
                height: self.minimum_height

                MDLabel:
                    text: "Run settings"
                    font_style: "H6"
                    theme_text_color: "Primary"
                    size_hint_y: None
                    height: dp(30)

                # MODEL SELECTION
                MDCard:
                    orientation: "vertical"
                    size_hint_y: None
                    height: dp(80)
                    padding: dp(10)
                    radius: [10]
                    md_bg_color: (0.18, 0.18, 0.18, 1)

                    MDLabel:
                        text: "Model"
                        font_style: "Caption"
                        theme_text_color: "Secondary"
                        size_hint_y: None
                        height: dp(20)
                    
                    MDRaisedButton:
                        id: btn_model
                        text: "gemini-1.5-pro"
                        pos_hint: {'center_x': 0.5}
                        size_hint_x: 1
                        on_release: app.open_model_menu()

                # SYSTEM INSTRUCTIONS
                MDTextField:
                    id: sys_instr
                    hint_text: "System Instructions"
                    text: "Jesteś Senior Python Developerem."
                    mode: "rectangle"
                    multiline: True
                    size_hint_y: None
                    height: dp(120)

                # TEMPERATURE
                MDBoxLayout:
                    orientation: 'vertical'
                    size_hint_y: None
                    height: dp(60)
                    
                    MDLabel:
                        text: f"Temperature: {round(slider_temp.value, 1)}"
                        font_style: "Caption"
                        theme_text_color: "Secondary"
                    
                    MDSlider:
                        id: slider_temp
                        min: 0
                        max: 2.0
                        value: 1.0
                        step: 0.1
                        hint: True

                # TOOLS SECTION
                MDLabel:
                    text: "Tools"
                    font_style: "Subtitle1"
                    size_hint_y: None
                    height: dp(30)

                MDBoxLayout:
                    size_hint_y: None
                    height: dp(40)
                    MDLabel:
                        text: "Code Execution"
                        theme_text_color: "Secondary"
                        font_style: "Body2"
                    MDSwitch:
                        id: switch_code
                        active: True
                        pos_hint: {'center_y': .5}

                MDBoxLayout:
                    size_hint_y: None
                    height: dp(40)
                    MDLabel:
                        text: "Google Search"
                        theme_text_color: "Secondary"
                        font_style: "Body2"
                    MDSwitch:
                        id: switch_search
                        active: True
                        pos_hint: {'center_y': .5}

                # DRAG & DROP FILES LIST
                MDLabel:
                    text: "Context Files (Drag Here)"
                    font_style: "Subtitle1"
                    size_hint_y: None
                    height: dp(30)
                
                MDList:
                    id: file_list
                    bg_color: (0.15, 0.15, 0.15, 1)
'''

# --- LOGIC ---

class ChatMessageBubble(MDBoxLayout):
    text = StringProperty("")
    is_user = BooleanProperty(True)

    def copy_content(self):
        Clipboard.copy(self.text)
        toast("Skopiowano!")

class MainWindow(MDScreen):
    pass

class DebugDruidProApp(MDApp):
    dropped_files = ListProperty([])
    current_model_name = StringProperty("gemini-1.5-pro")

    def build(self):
        self.title = "DebugDruid Agent 007 - PRO Console"
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Green"
        
        # Konfiguracja API
        load_dotenv()
        api_key = os.getenv("GOOGLE_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
        else:
            print("WARNING: Brak GOOGLE_API_KEY w pliku .env")

        # Obsługa Drag & Drop
        Window.bind(on_drop_file=self._on_file_drop)
        
        # FIX: Najpierw ładujemy style
        Builder.load_string(KV_INTERFACE)
        # FIX: Potem zwracamy KONKRETNĄ instancję
        return MainWindow()

    def on_start(self):
        # Konfiguracja menu modeli (musi być po zbudowaniu KV)
        menu_items = [
            {
                "text": "gemini-1.5-pro",
                "viewclass": "OneLineListItem",
                "on_release": lambda x="gemini-1.5-pro": self.set_model(x),
            },
            {
                "text": "gemini-1.5-flash",
                "viewclass": "OneLineListItem",
                "on_release": lambda x="gemini-1.5-flash": self.set_model(x),
            },
            {
                "text": "gemini-1.0-pro",
                "viewclass": "OneLineListItem",
                "on_release": lambda x="gemini-1.0-pro": self.set_model(x),
            }
        ]
        
        # Zabezpieczenie przed błędem 'NoneType' jeśli KV nie załadowało ID
        if hasattr(self.root, 'ids'):
            self.menu = MDDropdownMenu(
                caller=self.root.ids.btn_model,
                items=menu_items,
                width_mult=4,
            )
            # Powitanie
            self.root.ids.chat_list.add_widget(
                ChatMessageBubble(text="[color=#00ff00]System Online.[/color]\nPrzeciągnij pliki .py/.txt/.pdf tutaj aby dodać kontekst.", is_user=False)
            )

    def open_model_menu(self):
        self.menu.open()

    def set_model(self, model_name):
        self.current_model_name = model_name
        self.root.ids.btn_model.text = model_name
        self.menu.dismiss()
        toast(f"Aktywowano: {model_name}")

    def _on_file_drop(self, window, file_path, x, y):
        # Dekodowanie ścieżki Windows
        path_str = file_path.decode("utf-8")
        file_name = os.path.basename(path_str)
        
        if path_str not in self.dropped_files:
            self.dropped_files.append(path_str)
            
            # Update GUI
            item = OneLineIconListItem(text=file_name)
            icon = IconLeftWidget(icon="file-document-outline")
            item.add_widget(icon)
            self.root.ids.file_list.add_widget(item)
            
            toast(f"Dodano: {file_name}")

    def send_message(self):
        text_input = self.root.ids.user_input
        user_msg = text_input.text.strip()
        
        if not user_msg:
            return

        # 1. Dodaj dymek usera
        self.root.ids.chat_list.add_widget(
            ChatMessageBubble(text=user_msg, is_user=True)
        )
        text_input.text = ""

        # 2. Zbierz ustawienia (bez blokowania UI)
        params = {
            "model": self.current_model_name,
            "temp": self.root.ids.slider_temp.value,
            "sys_instr": self.root.ids.sys_instr.text,
            "tools": {
                "code": self.root.ids.switch_code.active,
                "search": self.root.ids.switch_search.active
            },
            "files": list(self.dropped_files) # Kopia listy
        }

        # 3. Odpowiedź AI w wątku
        threading.Thread(target=self._ai_worker, args=(user_msg, params)).start()

    def _ai_worker(self, message, params):
        """Logika uruchamiana w tle"""
        try:
            # Tu wpinasz prawdziwe Gemini API
            # tools_config = []
            # if params['tools']['code']: tools_config.append({'code_execution': {}})
            # model = genai.GenerativeModel(params['model'], tools=tools_config...)
            
            # Mock odpowiedzi na czas testu
            response_text = (
                f"Uruchamiam na modelu: [b]{params['model']}[/b]\n"
                f"Temperatura: {params['temp']:.1f}\n"
                f"Pliki w kontekście: {len(params['files'])}\n"
                f"Narzędzia: Search={'ON' if params['tools']['search'] else 'OFF'}, Code={'ON' if params['tools']['code'] else 'OFF'}\n"
                f"---\nOdpowiedź na: {message}"
            )
            
        except Exception as e:
            response_text = f"[color=#ff0000]ERROR:[/color] {str(e)}"

        # 4. Aktualizacja UI musi być w głównym wątku
        Clock.schedule_once(lambda dt: self._update_chat_ui(response_text))

    def _update_chat_ui(self, response_text):
        self.root.ids.chat_list.add_widget(
            ChatMessageBubble(text=response_text, is_user=False)
        )
        # Scroll na dół
        # self.root.ids.chat_scroll.scroll_to(...) # opcjonalnie

if __name__ == "__main__":
    DebugDruidProApp().run()