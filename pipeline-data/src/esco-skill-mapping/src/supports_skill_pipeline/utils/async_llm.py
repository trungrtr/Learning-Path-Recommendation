"""Async LLM Client with API Key Rotation for teaches_skill_pipeline_B."""

from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

class AsyncGeminiClient:
    """Async Gemini client supporting API key rotation for rate limits."""

    def __init__(self, model_name: str = "gemini-3.1-flash-lite", temperature: float = 0.0):
        self.model_name = model_name
        self.temperature = temperature
        
        # Load keys from environment
        self.api_keys = []
        for i in range(1, 10):
            key = os.environ.get(f"GEMINI_API_KEY{i}")
            if key and key.strip():
                self.api_keys.append(key.strip())
        
        # Fallback to GOOGLE_API_KEY if no GEMINI_API_KEY1..9 found
        if not self.api_keys:
            key = os.environ.get("GOOGLE_API_KEY")
            if key and key.strip():
                self.api_keys.append(key.strip())
                
        if not self.api_keys:
            logger.warning("No GEMINI_API_KEY found in environment! AsyncGeminiClient will fail.")
            
        self._current_key_idx = 0
        self._model = None

    async def generate_json_async(self, prompt: str) -> Any:
        import httpx
        
        max_retries = len(self.api_keys) * 2
        for attempt in range(max_retries):
            api_key = self.api_keys[self._current_key_idx]
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={api_key}"
            
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": self.temperature,
                    "responseMimeType": "application/json"
                }
            }
            
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.post(url, json=payload, timeout=60.0)
                    
                if resp.status_code == 429 or resp.status_code >= 500:
                    logger.warning(f"[ASYNC] API Error {resp.status_code} on key index {self._current_key_idx}. Rotating key and retrying...")
                    self._current_key_idx = (self._current_key_idx + 1) % len(self.api_keys)
                    await asyncio.sleep(2)
                    continue
                    
                resp.raise_for_status()
                
                resp_json = resp.json()
                raw_text = resp_json["candidates"][0]["content"]["parts"][0]["text"]
                
                # Clean markdown blocks if any
                if raw_text.startswith("```json"):
                    raw_text = raw_text.split("```json", 1)[1]
                if raw_text.startswith("```"):
                    raw_text = raw_text.split("```", 1)[1]
                if raw_text.endswith("```"):
                    raw_text = raw_text.rsplit("```", 1)[0]
                raw_text = raw_text.strip()
                
                return json.loads(raw_text)
            except httpx.HTTPStatusError as e:
                error_msg = str(e)
                if "429" in error_msg or "503" in error_msg or "500" in error_msg or "502" in error_msg or "504" in error_msg or "Quota exceeded" in error_msg or "ResourceExhausted" in error_msg:
                    logger.warning(f"[ASYNC] API Error '{e.response.status_code}' on key index {self._current_key_idx}. Rotating key...")
                    self._current_key_idx = (self._current_key_idx + 1) % len(self.api_keys)
                    await asyncio.sleep(2)
                    continue
                else:
                    logger.exception("Unrecoverable HTTP status error")
                    return {}
            except httpx.RequestError as e:
                logger.warning(f"[ASYNC] Network error '{e}' on key index {self._current_key_idx}. Retrying...")
                await asyncio.sleep(2)
                continue
            except Exception as e:
                error_msg = str(e)
                logger.warning(f"[ASYNC] Unexpected error '{error_msg}'. Rotating key and retrying...")
                self._current_key_idx = (self._current_key_idx + 1) % len(self.api_keys)
                await asyncio.sleep(2)
                continue
        
        logger.error("All API keys exhausted or max retries reached.")
        return {}
