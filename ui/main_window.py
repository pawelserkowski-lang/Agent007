import customtkinter as ctk
from tkinter import filedialog
from PIL import Image
import os
import threading
from config.settings import SettingsManager
from core.ai_engine import GeminiAgent
from utils.vision_ops import VisionProcessor

# --- ZMIANA NA JASNY MOTYW ---
ctk.set_appearance_mode("Light") 
ctk.set_default_color_theme("blue") 

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("EPS CHAT ATOM & VISION")
        self.geometry("1150x850")
        
        # Ikona
        icon_path = "ikona.webp" if os.path.exists("ikona.webp") else "ikona.png"
        if os.path.exists(icon_path):
            try: self.iconphoto(False, ctk.CTkImage(Image.open(icon_path)))
            except: pass

        self.settings = SettingsManager()
        self.agent = GeminiAgent(self.settings)
        self.current_img_path = None
        
        # Główny kontener zakładek
        self.tabview = ctk.CTkTabview(self, width=1100, height=800)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Definicja zakładek
        self.tab_chat = self.tabview.add("Czat AI")
        self.tab_vision = self.tabview.add("Laboratorium (Vision)")
        self.tab_settings = self.tabview.add("Ustawienia")
        
        self._build_chat_tab()
        self._build_vision_tab()
        self._build_settings_tab()
        self._enforce_env_key()

    def _enforce_env_key(self):
        if os.getenv("GOOGLE_API_KEY"):
            self.api_entry.delete(0, "end")
            self.api_entry.insert(0, "KLUCZ Z PLIKU .ENV AKTYWNY")
            self.api_entry.configure(state="disabled", text_color_disabled="green")

    def _build_chat_tab(self):
        # Tło (jeśli jest)
        bg_file = "tlo.webp" if os.path.exists("tlo.webp") else "tlo.png"
        if os.path.exists(bg_file):
            bg_img = Image.open(bg_file)
            self.bg_image_ref = ctk.CTkImage(bg_img, size=(1200, 900))
            self.bg_lbl = ctk.CTkLabel(self.tab_chat, image=self.bg_image_ref, text="")
            self.bg_lbl.place(x=0, y=0, relwidth=1, relheight=1)

        # Historia Czatu (BIAŁE TŁO, CZARNY TEKST)
        self.chat_history = ctk.CTkTextbox(
            self.tab_chat, 
            font=("Arial", 14), 
            fg_color="white",          # Białe tło dla tekstu
            text_color="black",        # Czarny tekst
            border_width=1, 
            border_color="#cccccc"
        )
        self.chat_history.pack(fill="both", expand=True, padx=20, pady=(20, 10))
        self.chat_history.configure(state="disabled")

        # Ramka Input (JASNOSZARA)
        frm = ctk.CTkFrame(self.tab_chat, height=60, fg_color="#f0f0f0", border_width=1, border_color="#dcdcdc")
        frm.pack(fill="x", padx=20, pady=(0, 20))
        
        self.btn_attach = ctk.CTkButton(frm, text="📎", width=40, command=self._chat_attach, fg_color="white", text_color="black", hover_color="#e0e0e0")
        self.btn_attach.pack(side="left", padx=10, pady=10)
        
        self.entry = ctk.CTkEntry(
            frm, 
            placeholder_text="Zapytaj Gemini...", 
            fg_color="white", 
            text_color="black", 
            border_width=0
        )
        self.entry.pack(side="left", fill="x", expand=True, padx=5, pady=10)
        self.entry.bind("<Return>", self._send)
        
        ctk.CTkButton(frm, text="Wyślij", width=80, command=self._send).pack(side="right", padx=10, pady=10)

    def _chat_attach(self):
        path = filedialog.askopenfilename(filetypes=[("Images", "*.jpg;*.png;*.webp")])
        if path:
            self.current_img_path = path
            self.btn_attach.configure(fg_color="#90ee90") # Light green
        else:
            self.current_img_path = None
            self.btn_attach.configure(fg_color="white")

    def _send(self, event=None):
        msg = self.entry.get()
        if not msg and not self.current_img_path: return
        self.entry.delete(0, "end")
        
        self._append_text(f"TY: {msg}")
        if self.current_img_path: self._append_text(f"[Załączono: {os.path.basename(self.current_img_path)}]")
        
        def task():
            try:
                resp = self.agent.send_message(msg, self.current_img_path)
                self.current_img_path = None
                self.btn_attach.configure(fg_color="white")
                self._append_text("\nAI: ", newline=False)
                for chunk in resp:
                    if chunk.text: self._append_text(chunk.text, newline=False)
                self._append_text("\n")
            except Exception as e: self._append_text(f"\nBŁĄD: {e}\n")
        threading.Thread(target=task).start()

    def _append_text(self, text, newline=True):
        self.chat_history.configure(state="normal")
        self.chat_history.insert("end", text + ("\n" if newline else ""))
        self.chat_history.see("end")
        self.chat_history.configure(state="disabled")

    def _build_vision_tab(self):
        self.tab_vision.grid_columnconfigure(0, weight=1)
        self.tab_vision.grid_columnconfigure(1, weight=1)
        
        # Menu (JASNOSZARE)
        menu = ctk.CTkFrame(self.tab_vision, fg_color="#f9f9f9")
        menu.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=10)
        
        ctk.CTkButton(menu, text="Otwórz Obraz", command=self._vis_open).pack(side="left", padx=10, pady=10)
        ctk.CTkButton(menu, text="AutoCrop (6%)", command=self._vis_process, fg_color="#e67e22").pack(side="left", padx=10)
        
        self.vis_status = ctk.CTkLabel(menu, text="Gotowy", text_color="black")
        self.vis_status.pack(side="left", padx=20)
        
        # Ramki podglądu (BIAŁE)
        self.f_left = ctk.CTkFrame(self.tab_vision, fg_color="white", border_width=1, border_color="#ccc")
        self.f_left.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        ctk.CTkLabel(self.f_left, text="ORYGINAŁ", text_color="gray").pack()
        self.lbl_orig = ctk.CTkLabel(self.f_left, text="")
        self.lbl_orig.pack(expand=True)
        
        self.f_right = ctk.CTkFrame(self.tab_vision, fg_color="white", border_width=1, border_color="#ccc")
        self.f_right.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)
        ctk.CTkLabel(self.f_right, text="PO OBRÓBCE", text_color="gray").pack()
        self.lbl_proc = ctk.CTkLabel(self.f_right, text="")
        self.lbl_proc.pack(expand=True)
        self.vis_img_path = None

    def _vis_open(self):
        path = filedialog.askopenfilename()
        if path:
            self.vis_img_path = path
            self.vis_status.configure(text=f"Plik: {os.path.basename(path)}")
            pil = Image.open(path); pil.thumbnail((400,400))
            self.lbl_orig.configure(image=ctk.CTkImage(pil, size=pil.size), text="")

    def _vis_process(self):
        if not self.vis_img_path: return
        self.vis_status.configure(text="Przetwarzanie..."); self.update()
        res, msg = VisionProcessor.process_image(self.vis_img_path)
        if res:
            self.vis_status.configure(text=msg); res.thumbnail((400,400))
            self.lbl_proc.configure(image=ctk.CTkImage(res, size=res.size), text="")

    def _build_settings_tab(self):
        logo_file = "logo.webp" if os.path.exists("logo.webp") else "logo.png"
        if os.path.exists(logo_file):
            pil = Image.open(logo_file)
            r = pil.height/pil.width; w=300; h=int(w*r)
            ctk.CTkLabel(self.tab_settings, image=ctk.CTkImage(pil, size=(w,h)), text="").pack(pady=20)
        else: ctk.CTkLabel(self.tab_settings, text="EPS CHAT ATOM", font=("Arial", 24), text_color="black").pack(pady=20)

        ctk.CTkLabel(self.tab_settings, text="Klucz API:", text_color="gray").pack(anchor="w", padx=20)
        self.api_entry = ctk.CTkEntry(self.tab_settings, width=400, placeholder_text="Klucz API", text_color="black", fg_color="white")
        self.api_entry.pack(pady=5)
        
        ctk.CTkLabel(self.tab_settings, text="Model AI:", text_color="gray").pack(anchor="w", padx=20, pady=(10,0))
        self.combo = ctk.CTkComboBox(self.tab_settings, values=self.agent.list_models(), fg_color="white", text_color="black")
        self.combo.pack(pady=5)
        
        ctk.CTkButton(self.tab_settings, text="Zapisz Model", command=lambda: self.settings.save_config({"model_name": self.combo.get()})).pack(pady=20)
