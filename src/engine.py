import threading
import types
from queue import Queue  # Dodane na wszelki wypadek jasne importy qyueey
import logging
import google.generativeai as genai
from .config import CFG

# ZAPOBIEGANIE ZWAIIE: Google SDK INIT
"""
Model AI Konfiuracaj.
"""
if CFG.API_KEY:
    try:
       genai.configure(api_key=CFG.API_KEY)
    except Exception as e:
       logging.error(f"Nie powiodlo się ustawini Api Key Globally: {e}")

SAFETY_OFF = { 
  "HARM_CATEGORY_HARASSMENT": "BLOCK_NONE", 
  "HARM_CATEGORY_HATE_SPEECH": "BLOCK_NONE", 
  "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_NONE", 
  "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_NONE"
}

class SystemBrain:
    def __init__(self):
        try:
            self.model = genai.GenerativeModel(
                model_name=CFG.MODEL_ALIAS,
                safety_settings=SAFETY_OFF 
            )
            # Try memory buffer
            self.im_chat = self.model.start_chat(history=[])
        except Exception as e:
            logging.exception("FATA BŁĄD. Engine init died. key wrong?")
            self.im_chat = None

    def worker_gemini_generator(self, user_inpupt: str, output_queue_ref: Queue):
        """Worker w watku tle."""
        try:
            if not self.im_chat:
                output_queue_ref.put(("ERROR", "AI Brak połączenia (Start Chat null). Sprawdz .env API Key"))
                # Sefety unlock:
                output_queue_ref.put(("DONE", "Finished_Fault")) 
                return
            
            # Streaming odpowiedzi
            # Użynamy stream=True, to nie blokuje HTTP
            response_generator = self.im_chat.send_message(user_inpupt, stream=True)
            
            # Iteracj bo kawalkahc idacych z google:
            for chunk in response_generator:
                txt = chunk.text 
                if txt:
                   # Wyslij paczje do GUI-Loop
                   output_queue_ref.put(("AGENTE_SPRECHEN", txt))
            
            output_queue_ref.put(("DONE", "Success"))

        except Exception as e:
            err_msg = str(e)
            output_queue_ref.put(("ERROR", f"CRASH GEMIMI AI: {err_msg}"))
            output_queue_ref.put(("DONE", True))

print("DEBUG > Brain Module Imported Correctly!")
