"""Backend Gemini có thể cắm vào bước dịch text unit Việt-Anh."""

from __future__ import annotations

import json
import os
from collections.abc import Callable

from pipeline.extract_translate.course_units import TranslateFunction


TRANSLATION_INSTRUCTIONS = """You are a senior Vietnamese-to-English translator for university course catalogues,
syllabi, learning outcomes, and professional skill taxonomies. Translate each input item into
terminologically precise, natural academic English suitable for downstream skill matching.

Terminology requirements:
- Use the established English term used internationally in the relevant discipline (for example,
  mathematics, computer science, engineering, business, and pedagogy), not a literal word-for-word
  rendering. Prefer the terminology commonly found in English-language university curricula,
  textbooks, and professional skill descriptions.
- Preserve the original technical meaning, scope, qualification, and relationships. Do not simplify,
  generalise, add examples, infer missing context, or turn a specific skill/topic into a broader one.
- Preserve standard abbreviations, proper names, formulae, numbers, and version identifiers. If a
  conventional English equivalent exists, use it; otherwise retain the specialist term faithfully.
- For course learning outcomes, use clear measurable academic verbs while retaining the intended
  competency level. For chapter titles and keyword skills, produce concise noun phrases rather than
  explanatory sentences.
- If an item is already accurate English, return it unchanged. Do not translate Vietnamese proper
  names unless they have a standard English exonym.

Output contract:
- Return only a valid JSON array of strings, with exactly the same number of elements and in exactly
  the same order as the input array.
- Do not return Markdown, commentary, labels, explanations, or additional items.
"""


def build_gemini_translate_fn(model_name: str) -> TranslateFunction:
    """Tạo hàm dịch batch dùng Gemini và kiểm tra chặt chẽ contract đầu ra JSON.

    API key được đọc từ ``GEMINI_API_KEY`` (hoặc ``LANGEXTRACT_API_KEY`` để tương
    thích cấu hình pipeline hiện có). Không có key thì raise lỗi để tránh ghi bản
    dịch mock/không đáng tin cậy vào output production.
    """
    try:
        from google import genai
        from google.genai import types
        from google.genai.errors import APIError
    except ImportError as exc:
        raise RuntimeError("Thiếu google-genai; hãy cài dependencies của pipeline.") from exc

    from pipeline import key_manager
    import time

    def translate(texts: list[str]) -> list[str]:
        """Dịch một batch Việt-Anh, bảo toàn số phần tử và thứ tự đầu vào."""
        prompt = (
            f"{TRANSLATION_INSTRUCTIONS}\n"
            f"Input JSON array:\n{json.dumps(texts, ensure_ascii=False)}"
        )
        
        max_attempts = key_manager.get_total_keys() * 2
        for attempt in range(max_attempts):
            api_key = key_manager.get_api_key()
            try:
                client = genai.Client(api_key=api_key)
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        temperature=0.0,
                    ),
                )
                try:
                    translated = json.loads(response.text)
                except (TypeError, json.JSONDecodeError) as exc:
                    raise RuntimeError("Gemini không trả về JSON hợp lệ cho batch dịch.") from exc
                if not isinstance(translated, list) or len(translated) != len(texts) or not all(
                    isinstance(text, str) and text.strip() for text in translated
                ):
                    raise RuntimeError("Gemini trả về số lượng hoặc kiểu phần tử không đúng contract dịch.")
                return translated
            except APIError as e:
                if e.code in (429, 503, 500) or "RESOURCE_EXHAUSTED" in str(e):
                    key_manager.rotate_key(api_key)
                    if attempt < max_attempts - 1:
                        time.sleep(2)
                        continue
                raise
        raise RuntimeError("Failed to translate batch after retries.")

    return translate
