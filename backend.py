import os
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

class GeminiBrain:
    def __init__(self, api_key):
        if not api_key:
            raise ValueError("Brak API KEY")
        genai.configure(api_key=api_key)
        self.chat_session = None
        self.uploaded_files = [] # Cache dla plików

    def prepare_model(self, model_name, sys_instruct, enable_search, enable_code, temp):
        """Konfiguruje model z wybranymi narzędziami."""
        tools = []
        if enable_code:
            tools.append("code_execution")
        if enable_search:
            # Wersje gemini-1.5 obsługują search jako narzędzie 'google_search_retrieval'
            # Uwaga: Dostępność zależy od regionu/konta. Fallback jest bezpieczny.
            tools.append("google_search_retrieval")

        # Konfiguracja generacji
        generation_config = genai.GenerationConfig(
            temperature=temp,
            max_output_tokens=8192,
        )

        # Ustawienia bezpieczeństwa (mniej restrykcyjne dla developera)
        safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_ONLY_HIGH,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
        }

        self.model = genai.GenerativeModel(
            model_name=model_name,
            system_instruction=sys_instruct,
            tools=tools,
            generation_config=generation_config,
            safety_settings=safety_settings
        )
        return self.model

    def start_chat(self, history=None):
        self.chat_session = self.model.start_chat(history=history or [])

    def process_files(self, file_paths):
        """Prosta obsługa kontekstu z plików tekstowych (Python, TXT, MD, JSON)."""
        file_context = ""
        for path in file_paths:
            try:
                # Sprawdzamy rozszerzenie - dla uproszczenia czytamy tekst
                ext = os.path.splitext(path)[1].lower()
                if ext in ['.py', '.txt', '.md', '.json', '.html', '.css', '.js', '.csv']:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        file_context += f"\n--- PLIK: {os.path.basename(path)} ---\n{content}\n"
                else:
                    file_context += f"\n[INFO] Plik {os.path.basename(path)} dołączony (tryb binarny pominięty w podglądzie).\n"
            except Exception as e:
                file_context += f"\n[ERROR] Nie udało się odczytać {os.path.basename(path)}: {e}\n"
        return file_context

    def send_query(self, user_text, file_paths=None):
        if not self.chat_session:
            self.start_chat()
        
        # Jeśli są pliki, doklejamy je do promptu (najbardziej niezawodna metoda dla kodu)
        full_prompt = user_text
        if file_paths:
            context = self.process_files(file_paths)
            if context:
                full_prompt = f"CONTEXT FILES:\n{context}\n\nUSER REQUEST:\n{user_text}"

        try:
            response = self.chat_session.send_message(full_prompt)
            return response.text
        except Exception as e:
            return f"API ERROR: {str(e)}"