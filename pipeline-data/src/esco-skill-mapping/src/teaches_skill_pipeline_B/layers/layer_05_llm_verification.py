"""Layer 05 — LLM Verification (LLM-as-a-judge).

Sử dụng LLM để xác nhận lại các kỹ năng đã được xếp hạng cao (Tier PRIMARY/SECONDARY)
bằng cách đối chiếu trực tiếp mô tả môn học và mô tả kỹ năng.
Giúp loại bỏ False Positive do Reranker nhầm lẫn.
"""

from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path
from typing import Any

from .layer_04_reranking import TieredCandidate
from ..models.schemas import EvidenceUnit

logger = logging.getLogger(__name__)

_VERIFICATION_PROMPT = """You are an expert curriculum evaluator.

Course Title: {course_title}
Course Content (Evidence):
{course_evidence}

Here are several skills/knowledge topics that might be taught in this course. 
For each one, determine if the course content explicitly teaches or develops it.
Base your decision ONLY on the provided course content and the skill description.

Respond ONLY with a JSON array of objects in this exact format:
[
  {{
    "skill_uri": "...",
    "is_taught": true/false,
    "reasoning": "brief explanation"
  }}
]

Skills to evaluate:
{skills_list}

Output (JSON array only):"""


async def _verify_batch_async(
    client: Any,
    batch: list[TieredCandidate],
    course_title: str,
    course_evidence_text: str,
) -> list[TieredCandidate]:
    skills_list_str = "\n\n".join(
        f"Skill URI: {c.candidate.skill_uri}\n"
        f"Label: {c.candidate.skill_label}\n"
        f"Description: {c.candidate.skill_description}"
        for c in batch
    )

    prompt = _VERIFICATION_PROMPT.format(
        course_title=course_title,
        course_evidence=course_evidence_text,
        skills_list=skills_list_str
    )

    try:
        results = await client.generate_json_async(prompt)
        if not isinstance(results, list):
            results = []
            
        result_map = {item.get("skill_uri"): item for item in results if isinstance(item, dict)}
        
        verified_batch = []
        for tc in batch:
            res = result_map.get(tc.candidate.skill_uri)
            if res:
                is_taught = res.get("is_taught", True)
                reasoning = res.get("reasoning", "")
                tc.llm_reasoning = reasoning
                
                if not is_taught:
                    tc.decision = "REJECT"
                    tc.reject_reason = "LLM_VERIFICATION_FAILED"
                    
            verified_batch.append(tc)
        return verified_batch
    except Exception as e:
        logger.warning("Batch verification error: %s", e)
        return batch


class LLMVerificationLayer:
    """Xác nhận lại candidates bằng LLM (hỗ trợ Async Batching)."""

    def __init__(self, config: Any):
        # We can reuse the extraction config for llm_model
        self._model = getattr(config.extraction, "llm_model", "gemini-3.1-flash-lite")
        self._temperature = getattr(config.extraction, "llm_temperature", 0.0)
        
        # Initialize async client
        from ..utils.async_llm import AsyncGeminiClient
        self._async_client = AsyncGeminiClient(model_name=self._model, temperature=self._temperature)

    def run(self, candidates: list[TieredCandidate], course_title: str, evidence_units: list[EvidenceUnit]) -> list[TieredCandidate]:
        """Thực thi verification trên danh sách candidates (chỉ xử lý PRIMARY và SECONDARY)."""
        import asyncio
        logger.info("Layer 05 (LLM Verification): Processing %d candidates (via Async Batching)", len(candidates))
        
        if not candidates:
            return []

        # Chỉ lọc những candidates được ACCEPT (PRIMARY/SECONDARY)
        to_verify = [c for c in candidates if c.decision == "ACCEPT"]
        others = [c for c in candidates if c.decision != "ACCEPT"]

        if not to_verify:
            return candidates

        course_evidence_text = "\n".join(
            f"- [{u.source_type}] {u.text}"
            for u in evidence_units
            if not u.is_boilerplate
        )

        # Batching: 10 candidates per request
        batch_size = 10
        batches = [to_verify[i : i + batch_size] for i in range(0, len(to_verify), batch_size)]
        
        async def run_all_batches():
            tasks = [
                _verify_batch_async(self._async_client, b, course_title, course_evidence_text)
                for b in batches
            ]
            return await asyncio.gather(*tasks)

        batch_results = asyncio.run(run_all_batches())
        
        verified_candidates = []
        for batch_res in batch_results:
            verified_candidates.extend(batch_res)

        logger.info("Layer 05 (LLM Verification): Verified %d candidates", len(verified_candidates))
        
        # Combine back
        final_list = verified_candidates + others
        return final_list
