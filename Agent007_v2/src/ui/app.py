import threading
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
