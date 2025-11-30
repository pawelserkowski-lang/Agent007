import time
import os
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.properties import BooleanProperty
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.app import MDApp
from ui.widgets.file_item import FileItem
from ui.widgets.bubble import ChatBubble

class ChatScreenLogic(MDBoxLayout):
    is_processing = BooleanProperty(False)
    start_time = 0
    loaded_files = []
    loaded_images = []

    def on_kv_post(self, base_widget):
        Window.bind(on_drop_file=self._on_file_drop)

    def _on_file_drop(self, window, file_path, x, y):
        path = file_path.decode('utf-8')
        ext = os.path.splitext(path)[1].lower()
        if ext in ['.png', '.jpg', '.jpeg', '.webp', '.bmp']:
            self.add_image_to_panel(path)
        else:
            self.add_file_to_panel(path)

    def add_file_to_panel(self, path):
        for item in self.loaded_files:
            if item.filepath == path: return
        item = FileItem(filepath=path, remove_func=self.remove_file)
        self.ids.file_container.add_widget(item)
        self.loaded_files.append(item)

    def add_image_to_panel(self, path):
        for item in self.loaded_images:
            if item == path: return
        item = FileItem(filepath=path, remove_func=self.remove_image)
        self.ids.file_container.add_widget(item)
        self.loaded_images.append(path)

    def remove_file(self, item_widget):
        self.ids.file_container.remove_widget(item_widget)
        if item_widget in self.loaded_files: self.loaded_files.remove(item_widget)

    def remove_image(self, item_widget):
        self.ids.file_container.remove_widget(item_widget)
        if item_widget.filepath in self.loaded_images: self.loaded_images.remove(item_widget.filepath)

    def send_message(self):
        text = self.ids.message_input.text.strip()
        if not text and not self.loaded_files and not self.loaded_images: return
        
        app = MDApp.get_running_app()
        if app.current_session_id == -1:
            title = text[:30] + "..." if text else "Nowa rozmowa"
            app.current_session_id = app.db.create_session(title)
            app.current_session_title = title
            app.refresh_sessions_list()
        
        self.start_timer()
        self.add_bubble(text if text else "[Wsad]", is_user=True)
        self.ids.message_input.text = ""
        
        files_data = {}
        for item in self.loaded_files:
            if item.ids.checkbox.active:
                try:
                    with open(item.filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        files_data[item.filename] = f.read()[:200000]
                except: pass
        
        if app.agent:
            app.agent.send_message(app.current_session_id, text, files_data, self.loaded_images, self.on_success, self.on_error)

    def start_timer(self):
        self.is_processing = True
        self.ids.progress_bar.start()
        self.start_time = time.time()
        self.timer_event = Clock.schedule_interval(self.update_timer, 0.05)

    def stop_timer(self):
        self.is_processing = False
        self.ids.progress_bar.stop()
        if hasattr(self, 'timer_event') and self.timer_event: self.timer_event.cancel()

    def update_timer(self, dt):
        self.ids.timer_label.text = f"{time.time() - self.start_time:.2f}s"

    def on_success(self, text):
        print(text) #
        self.stop_timer()
        self.add_bubble(text, is_user=False)

    def on_error(self, msg):
        self.stop_timer()
        self.add_bubble(f"Błąd: {msg}", is_user=False)

    def add_bubble(self, text, is_user):
        bubble = ChatBubble(text=text, is_user=is_user)
        self.ids.chat_list.add_widget(bubble)
        Clock.schedule_once(lambda dt: setattr(self.ids.scroll_view, 'scroll_y', 0), 0.1)

    def clear_view(self):
        self.ids.chat_list.clear_widgets()
        self.ids.file_container.clear_widgets()
        self.loaded_files = []
        self.loaded_images = []
