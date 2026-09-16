"""Bước 2 — LLM Support-Concept Extraction.

Trích xuất các khái niệm/kỹ năng/kiến thức NỀN TẢNG mà học phần
CÓ KHẢ NĂNG hỗ trợ phát triển — KHÔNG phải nội dung dạy trực tiếp.

Ràng buộc cứng:
- LLM chỉ output concept/keyword thô, không gán skill_id
- Prompt phải phân biệt TEACHES vs SUPPORTS rõ ràng
- Output phải đúng JSON schema: {"support_concepts": [...]}
- Giới hạn 5-15 concepts/course
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from ..configs.pipeline_config import LLMConfig

logger = logging.getLogger(__name__)

# Default prompt template path (relative to package)
_PACKAGE_DIR = Path(__file__).parent.parent
_DEFAULT_PROMPT_PATH = _PACKAGE_DIR / "prompts" / "support_concept_extraction.txt"


def _load_prompt_template(template_path: str | Path | None = None) -> str:
    """Load prompt template từ file."""
    path = Path(template_path) if template_path else _DEFAULT_PROMPT_PATH

    # Thử relative path từ package dir
    if not path.is_absolute():
        path = _PACKAGE_DIR / path

    if not path.exists():
        raise FileNotFoundError(f"Prompt template not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _call_llm(prompt: str, config: LLMConfig) -> str:
    """Gọi LLM API để trích xuất support concepts.

    Hiện hỗ trợ Google Gemini API.
    """
    try:
        import google.generativeai as genai
    except ImportError:
        raise ImportError(
            "google-generativeai package is required. "
            "Install with: pip install google-generativeai"
        )

    import os
    import time
    import random
    from google.api_core import exceptions

    keys = []
    for i in range(1, 8):
        k = os.getenv(f"GEMINI_API_KEY{i}")
        if k: keys.append(k)
        
    if not keys and os.getenv("GOOGLE_API_KEY"):
        keys.append(os.getenv("GOOGLE_API_KEY"))
        
    if not keys:
        raise ValueError("No API keys found!")

    for attempt in range(7):
        key = random.choice(keys)
        genai.configure(api_key=key)
        model = genai.GenerativeModel(config.model)

        try:
            response = model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    temperature=config.temperature,
                    response_mime_type="application/json",
                ),
            )
            return response.text
        except exceptions.ResourceExhausted:
            if attempt < 6:
                import logging
                logging.getLogger(__name__).warning(f"Rate limit hit. Retrying (attempt {attempt+1}/6)...")
                time.sleep(1)
                continue
            raise
        except Exception as e:
            if attempt < 6:
                time.sleep(1)
                continue
            raise
    return ""


def _parse_and_validate(raw_response: str, max_concepts: int) -> list[str]:
    """Parse và validate JSON response từ LLM.

    Args:
        raw_response: Raw JSON string từ LLM.
        max_concepts: Số concept tối đa cho phép.

    Returns:
        Danh sách support concepts đã validate.

    Raises:
        ValueError: Nếu response không đúng schema.
    """
    # Thử parse JSON
    try:
        data = json.loads(raw_response)
    except json.JSONDecodeError:
        # Thử trích xuất JSON từ markdown code block
        import re
        json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw_response, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group(1))
        else:
            raise ValueError(f"LLM response is not valid JSON: {raw_response[:200]}")

    # Validate schema
    if not isinstance(data, dict):
        raise ValueError(f"Expected dict, got {type(data)}")

    concepts = data.get("support_concepts", [])
    if not isinstance(concepts, list):
        raise ValueError(f"'support_concepts' must be a list, got {type(concepts)}")

    # Filter và clean
    cleaned = []
    for concept in concepts:
        if isinstance(concept, str) and concept.strip():
            cleaned.append(concept.strip().lower())

    # Giới hạn số lượng
    if len(cleaned) > max_concepts:
        logger.warning(
            "LLM returned %d concepts, truncating to %d",
            len(cleaned), max_concepts,
        )
        cleaned = cleaned[:max_concepts]

    return cleaned


import asyncio
from ..utils.async_llm import AsyncGeminiClient

async def extract_support_concepts(
    course_context: str,
    config: LLMConfig | None = None,
) -> list[str]:
    """Trích xuất support concepts từ course context bằng LLM (bất đồng bộ)."""
    if config is None:
        config = LLMConfig()

    template = _load_prompt_template(config.prompt_template_path)
    prompt = template.replace("{course_context}", course_context)

    logger.info("Calling LLM (%s) for support concept extraction...", config.model)

    try:
        client = AsyncGeminiClient(model_name=config.model, temperature=config.temperature)
        data = await client.generate_json_async(prompt)
        import json
        raw_response = json.dumps(data) if isinstance(data, dict) else str(data)
        
        concepts = _parse_and_validate(raw_response, config.max_concepts)
        logger.info("Extracted %d support concepts: %s", len(concepts), concepts)
        return concepts

    except Exception as e:
        logger.error("LLM extraction failed: %s", e)
        raise
