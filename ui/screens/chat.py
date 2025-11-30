import time
import threading
import queue
from kivy.core.window import Window
from kivy.clock import Clock, mainthread
from kivy.properties import BooleanProperty, StringProperty, NumericProperty
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.app import MDApp
from ui.widgets.bubble import ChatBubble
from ui.widgets.file_item import FileItem # Upewnij się że masz ten plik, jeśli nie - usuń ten import

class ChatScreenLogic(MDBoxLayout):
    is_processing = BooleanProperty(False)
    status_message = StringProperty("SYSTEM IDLE")
    response_time = StringProperty("0.00s")
    start_timestamp = 0
    current_streaming_bubble = None
    loaded_files = []

    def on_kv_post(self, base_widget):
        # Bind Keyboard for Ctrl+Enter
        Window.bind(on_key_down=self._on_keyboard_down)
        # Drag & Drop Support
        Window.bind(on_drop_file=self._on_file_drop)

    def _on_keyboard_down(self, instance, keyboard, keycode, text, modifiers):
        # keycode[1] to nazwa klawisza np. 'enter'
        if 'ctrl' in modifiers and keycode[1] == 'enter':
            self.send_message()
            return True # Konsumuj zdarzenie
        return False

    def _on_file_drop(self, window, file_path, x, y):
        # Prosta obsługa upuszczania
        self.ids.message_input.text += f" [File: {file_path.decode('utf-8')}] "

    def send_message(self):
        text = self.ids.message_input.text.strip()
        if not text: return
        
        self.ids.message_input.text = ""
        self.add_bubble(text, is_user=True)
        
        # Start Animation
        self.start_timer()
        self.status_message = "NEURAL PROCESSING..."
        
        app = MDApp.get_running_app()
        if hasattr(app, 'brain') and app.brain:
            self.response_queue = queue.Queue()
            threading.Thread(
                target=app.brain.worker_gemini_generator,
                args=(text, self.response_queue),
                daemon=True
            ).start()
            Clock.schedule_interval(self._consume_queue, 0.05)
        else:
            self.add_bubble("CRITICAL: Brain Disconnected", is_user=False)
            self.stop_timer()

    def _consume_queue(self, dt):
        try:
            while not self.response_queue.empty():
                msg_type, content = self.response_queue.get_nowait()
                
                if msg_type == "MSG_CHUNK":
                    self._update_streaming_bubble(content)
                elif msg_type == "ERROR":
                    self.add_bubble(f"ERROR: {content}", is_user=False)
                elif msg_type == "DONE":
                    self.stop_timer()
                    self.status_message = "RESPONSE COMPLETE"
                    self.current_streaming_bubble = None
                    return False 
        except: pass
        return True

    @mainthread
    def _update_streaming_bubble(self, chunk):
        if not self.current_streaming_bubble:
            self.current_streaming_bubble = self.add_bubble("", is_user=False)
        self.current_streaming_bubble.text += chunk

    def add_bubble(self, text, is_user):
        bubble = ChatBubble(text=text, is_user=is_user)
        self.ids.chat_list.add_widget(bubble)
        self.ids.scroll_view.scroll_to(bubble)
        return bubble

    def clear_view(self):
        self.ids.chat_list.clear_widgets()

    # --- Timer Logic ---
    def start_timer(self):
        self.is_processing = True
        self.start_timestamp = time.time()
        self.timer_event = Clock.schedule_interval(self.update_timer, 0.05)

    def stop_timer(self):
        self.is_processing = False
        if hasattr(self, 'timer_event'): self.timer_event.cancel()

    def update_timer(self, dt):
        delta = time.time() - self.start_timestamp
        self.response_time = f"{delta:.2f}s"