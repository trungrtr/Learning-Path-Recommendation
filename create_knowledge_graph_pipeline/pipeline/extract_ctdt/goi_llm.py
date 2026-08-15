"""LLM call boundary for programme-level CTDT extraction."""

from __future__ import annotations

import json
import os
from typing import Any


def extract_ctdt_with_llm(
    source_text: str,
    prompt_template: str,
    llm_settings: dict[str, Any],
) -> dict[str, Any]:
    from pipeline import key_manager
    import time
    
    max_chars = int(llm_settings.get("max_chars", 120_000))
    prompt = prompt_template.replace("{source_text}", source_text[:max_chars])
    model = llm_settings.get("model") or os.getenv("CTDT_EXTRACTOR_MODEL") or "gemini-3.1-flash-lite"
    temperature = float(llm_settings.get("temperature", 0.0))
    
    max_attempts = key_manager.get_total_keys() * 2
    for attempt in range(max_attempts):
        api_key = key_manager.get_api_key()
        try:
            from google import genai
            from google.genai import types
            from google.genai.errors import APIError
            
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=temperature,
                ),
            )
            loaded = json.loads(response.text)
            if not isinstance(loaded, dict):
                raise ValueError("CTDT LLM output must be a JSON object.")
            return loaded
        except APIError as e:
            if e.code in (429, 503, 500) or "RESOURCE_EXHAUSTED" in str(e):
                key_manager.rotate_key(api_key)
                if attempt < max_attempts - 1:
                    time.sleep(2)
                    continue
            raise
    raise RuntimeError("Failed to extract CTDT after retries.")
