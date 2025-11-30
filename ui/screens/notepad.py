import os
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.app import MDApp
from kivymd.toast import toast

class NotepadLogic(MDBoxLayout):
    current_file = "scratchpad.txt"

    def on_kv_post(self, base_widget):
        # Auto-load przy starcie
        self.load_from_file()

    def save_to_file(self):
        text = self.ids.notepad_field.text
        try:
            with open(self.current_file, "w", encoding="utf-8") as f:
                f.write(text)
            toast(f"Saved to {self.current_file}")
        except Exception as e:
            toast(f"Save Error: {e}")

    def load_from_file(self):
        if os.path.exists(self.current_file):
            try:
                with open(self.current_file, "r", encoding="utf-8") as f:
                    self.ids.notepad_field.text = f.read()
            except Exception as e:
                print(f"Read Error: {e}")

    def clear_text(self):
        self.ids.notepad_field.text = ""

    def copy_to_clipboard(self):
        from kivy.core.clipboard import Clipboard
        Clipboard.copy(self.ids.notepad_field.text)
        toast("Copied to Clipboard")