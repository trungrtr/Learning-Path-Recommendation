"""Unified Gemini wrapper: rate limiting, retry, token budget tracking,
pin model version theo config.yaml -> models.*. Mọi module gọi LLM đều
phải qua đây, không tự khởi tạo client riêng.

Environment variables (loaded from .env):
    GEMINI_API_KEY1   — primary key
    GEMINI_API_KEY2   — fallback key (used if primary hits quota)
"""

import os
import time
from pathlib import Path

from dotenv import dotenv_values, load_dotenv

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parents[4] / ".env")

# Lazy-init: client is created once on first call_gemini invocation.
_client = None
_key_index = 0
_API_KEYS = [
    os.getenv("GEMINI_API_KEY1", ""),
    os.getenv("GEMINI_API_KEY2", ""),
]


def _get_client():
    """Return a cached genai.Client, initializing on first call."""
    global _client, _key_index
    if _client is None:
        from google import genai
        key = _API_KEYS[_key_index]
        if not key:
            raise RuntimeError(
                "No Gemini API key found. Set GEMINI_API_KEY1 in .env"
            )
        _client = genai.Client(api_key=key)
    return _client


def _rotate_key():
    """Switch to the next API key and reset the cached client."""
    global _client, _key_index
    _key_index = (_key_index + 1) % len(_API_KEYS)
    _client = None


def call_gemini(
    prompt: str,
    model: str,
    max_retries: int = 3,
    retry_delay: float = 5.0,
    **kwargs,
) -> str:
    """Send *prompt* to Gemini and return the text response.

    Args:
        prompt:      Full prompt string (system + user content combined).
        model:       Model name from config.yaml (e.g. "gemini-3.1-flash-lite").
        max_retries: Number of retries on transient / quota errors.
        retry_delay: Base sleep in seconds between retries (doubles each attempt).

    Returns:
        The model's text response as a plain string.

    Raises:
        RuntimeError: If all retries are exhausted.
    """
    from google.genai import types

    last_exc: Exception | None = None
    delay = retry_delay

    for attempt in range(1, max_retries + 1):
        try:
            client = _get_client()
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.1,      # low temp for deterministic translation
                    max_output_tokens=8192,
                ),
            )
            return response.text

        except Exception as exc:
            last_exc = exc
            err_str = str(exc).lower()

            # Quota / rate-limit → try rotating to the next key first
            if "quota" in err_str or "resource_exhausted" in err_str or "429" in err_str:
                _rotate_key()

            if attempt < max_retries:
                time.sleep(delay)
                delay *= 2  # exponential back-off
            # else: fall through to raise

    raise RuntimeError(
        f"call_gemini failed after {max_retries} attempt(s): {last_exc}"
    ) from last_exc
