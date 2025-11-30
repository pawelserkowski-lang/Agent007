import os
import sys
import threading
from pathlib import Path

# --- IMPORTY I SPRAWDZANIE ZALEŻNOŚCI ---
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
    # Fallback dla braku bibliotek
    print(f"CRITICAL ERROR: {e}")
    sys.exit(1)

# --- KONFIGURACJA WINDOWS ---
# Wymuszenie twardego restartu OpenGL dla kart Intel
os.environ['KIVY_GL_BACKEND'] = 'angle_sdl2'

# --- UI LAYOUT (High Contrast Version) ---
KV_ULTIMATE = '''
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
        # WYRAŹNE KOLORY DYMKÓW
        md_bg_color: (0.1, 0.4, 0.1, 1) if root.is_user else (0.25, 0.25, 0.25, 1)
        radius: [15, 15, 0, 15] if root.is_user else [15, 15, 15, 0]
        padding: dp(10)
        elevation: 2
        
        MDLabel:
            text: root.text
            theme_text_color: "Custom"
            text_color: (1, 1, 1, 1)  # ZAWSZE BIAŁY
            size_hint_y: None
            height: self.texture_size[1]
            markup: True

        MDIconButton:
            icon: "content-copy"
            theme_text_color: "Custom"
            text_color: (0.7, 0.7, 0.7, 1)
            icon_size: "16sp"
            pos_hint: {'right': 1}
            size_hint: None, None
            size: dp(24), dp(24)
            on_release: root.copy_content()

<MainWindow>:
    # TŁO CAŁEJ APLIKACJI (Bardzo ciemny szary, nie czarny)
    md_bg_color: (0.05, 0.05, 0.05, 1)
    
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
                do_scroll_x: False
                
                MDList:
                    id: chat_list
                    spacing: dp(10)
                    padding: dp(10)

            # POLE WPISYWANIA
            MDCard:
                size_hint_y: None
                height: dp(60)
                radius: [25]
                md_bg_color: (0.15, 0.15, 0.15, 1)
                padding: [15, 5, 5, 5]
                elevation: 2

                MDTextField:
                    id: user_input
                    hint_text: "Zapytaj DebugDruida..."
                    mode: "fill"
                    fill_color_normal: (0, 0, 0, 0)
                    fill_color_focus: (0, 0, 0, 0)
                    active_line: False
                    line_color_normal: (0,0,0,0)
                    text_color_normal: (1, 1, 1, 1)
                    hint_text_color_normal: (0.6, 0.6, 0.6, 1)
                    multiline: False
                    on_text_validate: app.send_message()
                    pos_hint: {"center_y": .5}

                MDIconButton:
                    icon: "send"
                    theme_text_color: "Custom"
                    text_color: (0, 1, 0, 1) # Jasny zielony
                    pos_hint: {"center_y": .5}
                    on_release: app.send_message()

        # --- SEPARATOR ---
        MDBoxLayout:
            size_hint_x: None
            width: dp(2)
            md_bg_color: (0.2, 0.2, 0.2, 1)

        # --- PRAWY PANEL (CONTROLS) ---
        # Używamy MDCard jako tła dla prawego panelu dla lepszego renderowania
        MDCard:
            size_hint_x: 0.3
            md_bg_color: (0.12, 0.12, 0.12, 1)
            radius: [0]
            orientation: 'vertical'

            MDScrollView:
                do_scroll_x: False
                
                MDBoxLayout:
                    orientation: 'vertical'
                    padding: dp(15)
                    spacing: dp(20)
                    size_hint_y: None
                    height: self.minimum_height

                    MDLabel:
                        text: "PANEL STEROWANIA"
                        halign: "center"
                        font_style: "H6"
                        theme_text_color: "Custom"
                        text_color: (0, 1, 0, 1)
                        size_hint_y: None
                        height: dp(30)

                    # --- WYBÓR MODELU ---
                    MDCard:
                        orientation: "vertical"
                        size_hint_y: None
                        height: dp(90)
                        padding: dp(10)
                        radius: [10]
                        md_bg_color: (0.18, 0.18, 0.18, 1)
                        line_color: (0.3, 0.3, 0.3, 1)

                        MDLabel:
                            text: "Aktualny Model:"
                            font_style: "Caption"
                            theme_text_color: "Custom"
                            text_color: (0.8, 0.8, 0.8, 1)
                            size_hint_y: None
                            height: dp(20)
                        
                        MDRaisedButton:
                            id: btn_model
                            text: "gemini-1.5-pro"
                            md_bg_color: (0.2, 0.6, 0.2, 1)
                            pos_hint: {'center_x': 0.5}
                            size_hint_x: 1
                            on_release: app.open_model_menu()

                    # --- INSTRUKCJE SYSTEMOWE ---
                    MDLabel:
                        text: "System Instructions:"
                        theme_text_color: "Custom"
                        text_color: (0.9, 0.9, 0.9, 1)
                        size_hint_y: None
                        height: dp(20)

                    MDCard:
                        size_hint_y: None
                        height: dp(100)
                        md_bg_color: (0.08, 0.08, 0.08, 1)
                        padding: dp(5)
                        
                        MDTextField:
                            id: sys_instr
                            text: "Jesteś ekspertem Python."
                            mode: "fill"
                            fill_color_normal: (0,0,0,0)
                            line_anim: False
                            text_color_normal: (0.9, 1, 0.9, 1)
                            multiline: True

                    # --- TEMPERATURA ---
                    MDBoxLayout:
                        orientation: 'vertical'
                        size_hint_y: None
                        height: dp(60)
                        
                        MDLabel:
                            text: f"Kreatywność (Temp): {round(slider_temp.value, 1)}"
                            theme_text_color: "Custom"
                            text_color: (0.9, 0.9, 0.9, 1)
                            font_style: "Caption"
                        
                        MDSlider:
                            id: slider_temp
                            min: 0
                            max: 2.0
                            value: 1.0
                            step: 0.1
                            color: (0, 1, 0, 1)
                            thumb_color_active: (0, 1, 0, 1)

                    # --- TOOLS ---
                    MDLabel:
                        text: "Narzędzia:"
                        font_style: "Subtitle1"
                        theme_text_color: "Custom"
                        text_color: (0.5, 1, 0.5, 1)
                        size_hint_y: None
                        height: dp(30)

                    MDBoxLayout:
                        size_hint_y: None
                        height: dp(40)
                        MDLabel:
                            text: "Wykonywanie Kodu"
                            theme_text_color: "Custom"
                            text_color: (1, 1, 1, 1)
                        MDSwitch:
                            id: switch_code
                            active: True
                            thumb_color_active: (0, 1, 0, 1)

                    MDBoxLayout:
                        size_hint_y: None
                        height: dp(40)
                        MDLabel:
                            text: "Google Search"
                            theme_text_color: "Custom"
                            text_color: (1, 1, 1, 1)
                        MDSwitch:
                            id: switch_search
                            active: True
                            thumb_color_active: (0, 1, 0, 1)

                    # --- PLIKI ---
                    MDLabel:
                        text: "Załączone pliki:"
                        font_style: "Subtitle1"
                        theme_text_color: "Custom"
                        text_color: (0.5, 1, 0.5, 1)
                        size_hint_y: None
                        height: dp(30)
                    
                    MDList:
                        id: file_list
                        # Explicit bg color
'''

class ChatMessageBubble(MDBoxLayout):
    text = StringProperty("")
    is_user = BooleanProperty(True)

    def copy_content(self):
        Clipboard.copy(self.text)
        toast("Skopiowano!")

class MainWindow(MDScreen):
    pass

class DebugDruidUltimateApp(MDApp):
    dropped_files = ListProperty([])
    current_model_name = StringProperty("gemini-1.5-pro")

    def build(self):
        self.title = "Agent 007 - Ultimate Console"
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Green"
        self.theme_cls.material_style = "M3"
        
        # Konfiguracja API
        load_dotenv()
        api_key = os.getenv("GOOGLE_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
        
        Window.bind(on_drop_file=self._on_file_drop)
        return Builder.load_string(KV_ULTIMATE)

    def on_start(self):
        # Menu Modeli
        menu_items = [
            {"text": "gemini-1.5-pro", "viewclass": "OneLineListItem", 
             "on_release": lambda x="gemini-1.5-pro": self.set_model(x)},
            {"text": "gemini-1.5-flash", "viewclass": "OneLineListItem",
             "on_release": lambda x="gemini-1.5-flash": self.set_model(x)},
            {"text": "gemini-1.0-pro", "viewclass": "OneLineListItem",
             "on_release": lambda x="gemini-1.0-pro": self.set_model(x)},
        ]
        self.menu = MDDropdownMenu(caller=self.root.ids.btn_model, items=menu_items, width_mult=4)

        # TEST RENDEROWANIA - Powiadomienie powitalne
        self.root.ids.chat_list.add_widget(
            ChatMessageBubble(text="[b]SYSTEM START:[/b] Jeśli to widzisz, rendering działa poprawnie!", is_user=False)
        )
        # Dodaj dummy plik żeby zobaczyć prawy panel
        self._add_file_to_ui("instrukcja_startowa.txt")

    def open_model_menu(self):
        self.menu.open()

    def set_model(self, model_name):
        self.current_model_name = model_name
        self.root.ids.btn_model.text = model_name
        self.menu.dismiss()
        toast(f"Wybrano: {model_name}")

    def _on_file_drop(self, window, file_path, x, y):
        try:
            path_str = file_path.decode("utf-8")
            if path_str not in self.dropped_files:
                self.dropped_files.append(path_str)
                self._add_file_to_ui(os.path.basename(path_str))
                toast("Plik dodany!")
        except Exception as e:
            print(f"Drop error: {e}")

    def _add_file_to_ui(self, filename):
        item = OneLineIconListItem(
            text=filename,
            theme_text_color="Custom",
            text_color=(0.9, 0.9, 0.9, 1) # Biały tekst pliku
        )
        icon = IconLeftWidget(
            icon="file-document-outline",
            theme_text_color="Custom",
            text_color=(0, 1, 0, 1) # Zielona ikona
        )
        item.add_widget(icon)
        self.root.ids.file_list.add_widget(item)

    def send_message(self):
        user_input = self.root.ids.user_input
        text = user_input.text.strip()
        if not text: return

        self.root.ids.chat_list.add_widget(ChatMessageBubble(text=text, is_user=True))
        user_input.text = ""

        # UI Thread Worker
        threading.Thread(target=self._ai_worker, args=(text,), daemon=True).start()

    def _ai_worker(self, text):
        # Symulacja AI
        response = f"Otrzymano: {text}\nModel: {self.current_model_name}"
        Clock.schedule_once(lambda dt: self._update_chat(response))

    def _update_chat(self, text):
        self.root.ids.chat_list.add_widget(ChatMessageBubble(text=text, is_user=False))

if __name__ == "__main__":
    DebugDruidUltimateApp().run()