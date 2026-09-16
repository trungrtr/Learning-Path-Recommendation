"""Layer 01 — Extraction: LLM-based Mention Extraction.

Thay vì dùng Ensemble (ESCOXLM-R, SkillSpan) phức tạp,
chúng ta dùng trực tiếp Gemini để bóc tách RawMention.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Any

from ..models.schemas import EvidenceUnit, RawMention

logger = logging.getLogger(__name__)

_BATCH_EXTRACTION_PROMPT = """You are a skill/knowledge extraction expert for academic course content.

Given the following course content text excerpts, extract all explicit skill and knowledge mentions.
Return ONLY a JSON object containing a "results" array. Each item in the array must have "unit_id" (string) and "mentions" (array of strings).

Rules:
- Extract concrete skills and knowledge topics, not vague descriptions.
- Each mention should be 2-6 words.
- Do not include verbs like "understand", "apply" — only the noun phrases.
- Return empty array [] for "mentions" if no clear skills/knowledge can be identified.

Curriculum excerpts (JSON list):
{batch_json}

Output (JSON object only):
{{
  "results": [
    {{
      "unit_id": "<unit_id>",
      "mentions": ["skill 1", "skill 2"]
    }}
  ]
}}"""


async def _extract_batch_async(
    client: Any,
    batch: list[EvidenceUnit],
) -> dict[str, list[str]]:
    import json
    
    batch_data = [{"unit_id": u.evidence_id, "text": u.text} for u in batch]
    batch_json_str = json.dumps(batch_data, ensure_ascii=False, indent=2)
    
    prompt = _BATCH_EXTRACTION_PROMPT.format(batch_json=batch_json_str)
    
    data = await client.generate_json_async(prompt)
    if not data:
        logger.error("LLM returned empty data for batch!")
    
    results_map = {}
    if isinstance(data, dict) and "results" in data:
        for item in data["results"]:
            if isinstance(item, dict):
                uid = item.get("unit_id")
                mentions = item.get("mentions", [])
                if uid and isinstance(mentions, list):
                    results_map[uid] = [str(s) for s in mentions if s]
    else:
        logger.error("Invalid JSON structure from LLM: %s", data)
    return results_map


class LLMExtractor:
    """Trích xuất mention thô bằng LLM (hỗ trợ Async Batching)."""

    def __init__(self, config: Any):
        self._model = getattr(config.extraction, "llm_model", "gemini-3.1-flash-lite")
        self._temperature = getattr(config.extraction, "llm_temperature", 0.0)
        cache_dir = getattr(config.extraction, "cache_dir", "cache/extraction")
        self._cache_dir = Path(cache_dir) if cache_dir else None
        self._prompt_version = "v1_llm_main_batched"
        
        # Initialize async client
        from ..utils.async_llm import AsyncGeminiClient
        self._async_client = AsyncGeminiClient(model_name=self._model, temperature=self._temperature)

    def run(self, evidence_units: list[EvidenceUnit]) -> list[RawMention]:
        """Thực thi extraction trên danh sách evidence units (sử dụng Async Batching)."""
        import asyncio
        mentions: list[RawMention] = []
        
        # Bỏ qua các câu boilerplate
        active_units = [u for u in evidence_units if not u.is_boilerplate]
        
        # Chia các units thành cached và uncached
        uncached_units = []
        for unit in active_units:
            cached = self._load_cache(unit.evidence_id)
            if cached is not None:
                mentions.extend(cached)
            else:
                uncached_units.append(unit)

        if uncached_units:
            batch_size = 15
            batches = [uncached_units[i:i + batch_size] for i in range(0, len(uncached_units), batch_size)]
            
            async def run_all_batches():
                tasks = [_extract_batch_async(self._async_client, b) for b in batches]
                return await asyncio.gather(*tasks)
                
            batch_results = asyncio.run(run_all_batches())
            
            # Gộp kết quả từ các batches
            results_map = {}
            for res in batch_results:
                results_map.update(res)
                
            # Tạo RawMention object
            for unit in uncached_units:
                unit_mention_texts = results_map.get(unit.evidence_id, [])
                unit_mentions = [
                    RawMention(
                        text=text.strip(),
                        evidence_id=unit.evidence_id,
                        source="llm_extraction",
                    )
                    for text in unit_mention_texts
                    if text.strip() and len(text.strip()) >= 2
                ]
                self._save_cache(unit.evidence_id, unit_mentions)
                mentions.extend(unit_mentions)

        logger.info(
            "Layer 01 (LLM Extraction): Extracted %d mentions from %d active units (via Async Batching)",
            len(mentions), len(active_units),
        )
        return mentions

    # --- Cache ---
    def _cache_key(self, evidence_id: str) -> Path | None:
        if self._cache_dir is None:
            return None
        key = f"llm_{self._prompt_version}_{evidence_id}"
        safe = hashlib.md5(key.encode()).hexdigest()
        return self._cache_dir / f"llm_main_{safe}.json"

    def _load_cache(self, evidence_id: str) -> list[RawMention] | None:
        path = self._cache_key(evidence_id)
        if path is None or not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return [RawMention(**item) for item in data]
        except Exception:
            return None

    def _save_cache(self, evidence_id: str, mentions: list[RawMention]) -> None:
        path = self._cache_key(evidence_id)
        if path is None:
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        data = [
            {
                "text": m.text,
                "evidence_id": m.evidence_id,
                "source": m.source,
                "head_type": m.head_type,
                "confidence": m.confidence,
                "char_start": m.char_start,
                "char_end": m.char_end,
                "source_text": m.source_text,
            }
            for m in mentions
        ]
        path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
