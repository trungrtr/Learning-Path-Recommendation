import os
import logging
import threading

LOGGER = logging.getLogger(__name__)

class KeyManager:
    """Manages multiple API keys and handles round-robin fallback on rate limits."""
    def __init__(self):
        self.keys = []
        self.current_index = 0
        self.lock = threading.Lock()
        self.load_keys()

    def load_keys(self):
        keys_str = os.getenv("GEMINI_API_KEYS")
        if keys_str:
            self.keys = [k.strip() for k in keys_str.split(",") if k.strip()]
        else:
            k = os.getenv("GEMINI_API_KEY") or os.getenv("LANGEXTRACT_API_KEY")
            if k:
                self.keys = [k.strip()]
        
        if not self.keys:
            raise RuntimeError("Missing GEMINI_API_KEYS, GEMINI_API_KEY, or LANGEXTRACT_API_KEY in environment.")

    def get_api_key(self) -> str:
        with self.lock:
            return self.keys[self.current_index]

    def rotate_key(self, failed_key: str):
        with self.lock:
            if self.keys[self.current_index] == failed_key:
                old_index = self.current_index
                self.current_index = (self.current_index + 1) % len(self.keys)
                LOGGER.info("Rotated API Key from index %d to %d.", old_index, self.current_index)

manager = KeyManager()

def get_api_key() -> str:
    return manager.get_api_key()

def rotate_key(failed_key: str):
    manager.rotate_key(failed_key)

def get_total_keys() -> int:
    return len(manager.keys)
