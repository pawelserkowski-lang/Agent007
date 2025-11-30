import time
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
            full_prompt += "\n\n--- KONTEKST Z PLIKÓW ---\n"
            for item in self.loaded_files:
                try:
                    with open(item.filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()[:20000] 
                        full_prompt += f"\n>>> PLIK: {item.filename}\n{content}\n"
                except Exception as e:
                    full_prompt += f"\n>>> PLIK: {item.filename} (Błąd odczytu: {e})\n"

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
