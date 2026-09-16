"""Bước 5.5 — LLM Verification cho supports_skill_pipeline.

Sử dụng LLM (Gemini) để xác nhận xem skill ESCO đề xuất
có thực sự được học phần **bổ trợ** (support) hay không.

Phân biệt rõ:
- SUPPORTS: Học phần cung cấp nền tảng, kiến thức liên quan, hoặc
  kỹ năng phụ trợ giúp người học phát triển skill đó gián tiếp.
- TEACHES: Học phần dạy trực tiếp skill đó (không phải mục tiêu ở đây).
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from ..models.candidate import ScoredCandidate

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Prompt
# ---------------------------------------------------------------------------

_VERIFICATION_PROMPT = """\
You are an expert curriculum evaluator specializing in identifying SUPPORT relationships between courses and skills.

A course SUPPORTS a skill when it provides foundational knowledge, related concepts, or complementary abilities that help a learner develop that skill indirectly — even if the course does not explicitly teach the skill itself.

Examples of SUPPORT relationships:
- A "Linear Algebra" course SUPPORTS "machine learning" — because linear algebra is a mathematical foundation.
- A "Data Structures" course SUPPORTS "software architecture" — because understanding data structures is a prerequisite.
- A "Statistics" course SUPPORTS "data analysis" — because statistics provides the theoretical backbone.

A course does NOT support a skill if:
- The skill is completely unrelated to the course content.
- The connection is too vague or superficial.

Course Title: {course_name}
Course Content:
{course_context}

Evaluate the following skills. For each one, determine if the course content provides genuine SUPPORT for developing that skill.

Respond ONLY with a JSON array:
[
  {{
    "skill_uri": "...",
    "is_supported": true/false,
    "reasoning": "brief explanation of why this course supports or does not support this skill"
  }}
]

Skills to evaluate:
{skills_list}

Output (JSON array only):"""


# ---------------------------------------------------------------------------
# Async batch verification
# ---------------------------------------------------------------------------

async def _verify_batch_async(
    client: Any,
    batch: list[ScoredCandidate],
    course_context: str,
    course_name: str,
) -> list[ScoredCandidate]:
    """Xác nhận 1 batch candidates bằng LLM."""

    skills_list_str = "\n\n".join(
        f"Skill URI: {c.skill_uri}\n"
        f"Label: {c.skill_label}\n"
        f"Description: {c.skill_description}\n"
        f"Skill Type: {c.skill_type}"
        for c in batch
    )

    prompt = _VERIFICATION_PROMPT.format(
        course_name=course_name,
        course_context=course_context[:6000],  # Giới hạn context tránh token overflow
        skills_list=skills_list_str,
    )

    try:
        results = await client.generate_json_async(prompt)
        if not isinstance(results, list):
            logger.warning("LLM verification returned non-list: %s", type(results))
            # Giữ nguyên tất cả candidates nếu LLM lỗi
            return batch

        result_map = {
            item.get("skill_uri"): item
            for item in results
            if isinstance(item, dict)
        }

        verified: list[ScoredCandidate] = []
        for cand in batch:
            res = result_map.get(cand.skill_uri)
            if res:
                is_supported = res.get("is_supported", True)
                reasoning = res.get("reasoning", "")
                cand.llm_reasoning = reasoning

                if is_supported:
                    verified.append(cand)
                else:
                    logger.info(
                        "  ✗ REJECTED by LLM: %s — %s",
                        cand.skill_label, reasoning,
                    )
            else:
                # LLM không trả kết quả cho candidate này → giữ lại (an toàn)
                verified.append(cand)

        return verified

    except Exception as e:
        logger.warning("LLM verification batch error: %s — keeping all candidates.", e)
        return batch


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def verify_support_candidates(
    candidates: list[ScoredCandidate],
    course_context: str,
    course_name: str,
    llm_config: Any,
) -> list[ScoredCandidate]:
    """Xác nhận toàn bộ candidates bằng LLM (Async Batching).

    Args:
        candidates: Danh sách ScoredCandidate từ Bước 5.
        course_context: Course context text từ Bước 1.
        course_name: Tên học phần.
        llm_config: LLMConfig chứa model, temperature.

    Returns:
        Danh sách ScoredCandidate đã lọc (chỉ giữ is_supported=True).
    """
    if not candidates:
        return []

    logger.info(
        "Bước 5.5 (LLM Verification): Verifying %d candidates...",
        len(candidates),
    )

    from ..utils.async_llm import AsyncGeminiClient

    client = AsyncGeminiClient(
        model_name=getattr(llm_config, "model", "gemini-3.1-flash-lite"),
        temperature=getattr(llm_config, "temperature", 0.0),
    )

    # Batch: gộp tối đa 10 candidates/request
    batch_size = 10
    batches = [candidates[i:i + batch_size] for i in range(0, len(candidates), batch_size)]

    tasks = [
        _verify_batch_async(client, batch, course_context, course_name)
        for batch in batches
    ]
    batch_results = await asyncio.gather(*tasks)

    verified: list[ScoredCandidate] = []
    for batch_res in batch_results:
        verified.extend(batch_res)

    logger.info(
        "Bước 5.5 (LLM Verification): %d/%d candidates verified as SUPPORTED.",
        len(verified), len(candidates),
    )

    return verified
