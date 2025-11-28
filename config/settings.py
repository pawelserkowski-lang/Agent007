import json
import os

CONFIG_FILE = "config.json"
DEFAULT_CONFIG = {"model_name": "gemini-1.5-flash", "temperature": 0.7, "max_tokens": 4096}

class SettingsManager:
    def __init__(self):
        self.config = self.load_config()
    def load_config(self):
        config = DEFAULT_CONFIG.copy()
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f: config.update(json.load(f))
            except: pass
        return config
    def save_config(self, new_config):
        if "api_key" in new_config: del new_config["api_key"]
        self.config.update(new_config)
        with open(CONFIG_FILE, "w", encoding="utf-8") as f: json.dump(new_config, f, indent=4)
    def get(self, key):
        if key == "api_key":
            return os.getenv("GOOGLE_API_KEY", self.config.get("api_key", ""))
        return self.config.get(key, DEFAULT_CONFIG.get(key))
