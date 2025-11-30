import threading
import logging
import google.generativeai as genai
from queue import Queue
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from .config import CFG

try:
    genai.configure(api_key=CFG.API_KEY)
except Exception as e:
    logging.critical(f"Google AI SDK Configuration Failed: {e}")

SAFETY_SETTINGS = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
}

class SystemBrain:
    def __init__(self):
        self.chat_session = None
        self._init_model()

    def _init_model(self):
        try:
            logging.info(f"Initializing Model: {CFG.MODEL_ALIAS}")
            self.model = genai.GenerativeModel(
                model_name=CFG.MODEL_ALIAS,
                safety_settings=SAFETY_SETTINGS
            )
            self.chat_session = self.model.start_chat(history=[])
            logging.info("Brain Module: Online")
        except Exception as e:
            logging.error(f"Brain Init Error: {e}")
            self.chat_session = None

    def worker_gemini_generator(self, user_input: str, output_queue: Queue):
        if not self.chat_session:
            output_queue.put(("ERROR", "Brain Disconnected. Restart Application."))
            output_queue.put(("DONE", "Failed"))
            return

        try:
            response = self.chat_session.send_message(user_input, stream=True)
            
            for chunk in response:
                try:
                    text_part = chunk.text
                    if text_part:
                        output_queue.put(("MSG_CHUNK", text_part))
                except ValueError:
                    logging.warning("Empty chunk received (Safety Filter or Network artifact).")
                    continue

            output_queue.put(("DONE", "Success"))

        except Exception as e:
            error_msg = str(e)
            logging.error(f"Gemini Runtime Error: {error_msg}")
            output_queue.put(("ERROR", f"AI Error: {error_msg}"))
            output_queue.put(("DONE", "Crash"))

print("DEBUG > Brain Module Loaded.")
