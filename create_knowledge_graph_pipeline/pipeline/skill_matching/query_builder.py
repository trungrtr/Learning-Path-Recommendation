"""Build deterministic hierarchy-aware retrieval queries from translated units."""

from __future__ import annotations

import re
from typing import Any

from .config import SkillMatchingConfig
from .models import ContextualQuery
from .skill_pool import SkillPool


def _valid_units(units: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        unit
        for unit in units
        if isinstance(unit.get("course_id"), str)
        and isinstance(unit.get("unit_id"), str)
        and isinstance(unit.get("unit_type"), str)
        and isinstance(unit.get("text_en"), str)
        and unit["text_en"].strip()
    ]


def _token_count(text: str, tokenizer: Any | None) -> int:
    if tokenizer is not None and hasattr(tokenizer, "encode"):
        try:
            return len(tokenizer.encode(text, add_special_tokens=False))
        except TypeError:
            return len(tokenizer.encode(text))
    return len(text.split())


def _description_chunks(
    text: str,
    max_tokens: int,
    overlap_tokens: int,
    tokenizer: Any | None,
) -> list[str]:
    """Chunk by sentence/word boundaries without using an LLM."""
    words = text.split()
    if not words:
        return []
    chunks: list[str] = []
    start = 0
    while start < len(words):
        end = start
        best_end = start
        while end < len(words):
            candidate = " ".join(words[start : end + 1])
            if _token_count(candidate, tokenizer) > max_tokens:
                break
            best_end = end + 1
            end += 1
        if best_end == start:
            best_end = start + 1
        chunk = " ".join(words[start:best_end]).strip()
        # Prefer ending at the last sentence boundary inside the chunk when it
        # does not collapse the chunk to a very small fragment.
        boundaries = [match.end() for match in re.finditer(r"[.!?](?:\s|$)", chunk)]
        if best_end < len(words) and boundaries:
            sentence_chunk = chunk[: boundaries[-1]].strip()
            if _token_count(sentence_chunk, tokenizer) >= max(1, max_tokens // 3):
                sentence_words = len(sentence_chunk.split())
                best_end = start + sentence_words
                chunk = sentence_chunk
        chunks.append(chunk)
        if best_end >= len(words):
            break
        overlap_start = best_end
        while overlap_start > start:
            candidate = " ".join(words[overlap_start - 1 : best_end])
            if _token_count(candidate, tokenizer) > overlap_tokens:
                break
            overlap_start -= 1
        start = overlap_start if overlap_start < best_end else best_end
    return chunks


def _query(record: dict[str, Any]) -> dict[str, Any]:
    return ContextualQuery.model_validate(record).model_dump(exclude_none=True)


def build_match_queries(
    units: list[dict[str, Any]],
    source_key: str,
    pool: SkillPool,
    config: SkillMatchingConfig,
) -> list[dict[str, Any]]:
    """Create V1 course/CLO/chapter/lesson queries with exact provenance.

    Topic clustering and LLM skill generation are intentionally absent. Course
    type is context metadata only and never forces a teaches/supports relation.
    """
    del source_key
    valid_units = _valid_units(units)
    if not valid_units:
        return []
    course_id = valid_units[0]["course_id"]
    name_unit = next((unit for unit in valid_units if unit["unit_type"] == "name"), None)
    course_name = (
        (name_unit or {}).get("text_en")
        or valid_units[0].get("course_name_en")
        or valid_units[0].get("course_name_vi")
        or course_id
    )
    tokenizer = getattr(pool.model, "tokenizer", None)
    queries: list[dict[str, Any]] = []

    descriptions = [unit for unit in valid_units if unit["unit_type"] == "description"]
    if descriptions:
        for description in descriptions:
            chunks = _description_chunks(
                description["text_en"],
                config.description_chunk_tokens,
                config.description_chunk_overlap_tokens,
                tokenizer,
            )
            for chunk_index, chunk in enumerate(chunks):
                queries.append(
                    _query(
                        {
                            "course_id": course_id,
                            "query_id": f"course:{description['unit_id']}:{chunk_index}",
                            "query_type": "course",
                            "retrieval_text_en": f"{course_name} > {chunk}",
                            "evidence_text_en": chunk,
                            "source_unit_ids": [description["unit_id"]],
                            "source_unit_types": ["description"],
                            "chunk_index": chunk_index,
                        }
                    )
                )
    elif name_unit:
        queries.append(
            _query(
                {
                    "course_id": course_id,
                    "query_id": f"course:{name_unit['unit_id']}",
                    "query_type": "course",
                    "retrieval_text_en": course_name,
                    "evidence_text_en": name_unit["text_en"],
                    "source_unit_ids": [name_unit["unit_id"]],
                    "source_unit_types": ["name"],
                }
            )
        )

    for unit in valid_units:
        unit_type = unit["unit_type"]
        if unit_type == "clo":
            retrieval_text = f"{course_name} > {unit['text_en']}"
        elif unit_type == "chapter":
            retrieval_text = f"{course_name} > {unit['text_en']}"
        elif unit_type == "lesson":
            chapter_title = unit.get("chapter_title_en") or unit.get("chapter_title_vi")
            retrieval_text = " > ".join(
                part for part in (course_name, chapter_title, unit["text_en"]) if isinstance(part, str) and part.strip()
            )
        else:
            continue
        queries.append(
            _query(
                {
                    "course_id": course_id,
                    "query_id": f"{unit_type}:{unit['unit_id']}",
                    "query_type": unit_type,
                    "retrieval_text_en": retrieval_text,
                    "evidence_text_en": unit["text_en"],
                    "source_unit_ids": [unit["unit_id"]],
                    "source_unit_types": [unit_type],
                }
            )
        )
    return queries

