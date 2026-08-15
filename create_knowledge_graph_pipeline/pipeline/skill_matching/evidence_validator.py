"""Evidence-based validation for consolidated course/ESCO candidates."""

from __future__ import annotations

import hashlib
import json
import logging
import os
import time
import unicodedata
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

from pipeline.extract_course.cau_hinh import ROOT_DIR

from .config import SkillMatchingConfig
from .models import ConsolidatedCandidate, EvidenceValidationResult, ValidatedCandidate

LOGGER = logging.getLogger(__name__)
ValidationBackend = Callable[[dict[str, Any]], Mapping[str, Any]]


def _normalized_text(value: str) -> str:
    """Normalize Unicode and whitespace for conservative quote containment checks."""
    return " ".join(unicodedata.normalize("NFC", value).casefold().split())


def _cache_key(candidate: ConsolidatedCandidate, config: SkillMatchingConfig) -> str:
    payload = {
        "model": config.evidence_validator_model,
        "prompt_version": config.evidence_validator_prompt_version,
        "candidate": candidate.model_dump(mode="json", exclude_none=True),
    }
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _insufficient(candidate: ConsolidatedCandidate, reason: str) -> EvidenceValidationResult:
    return EvidenceValidationResult(
        course_id=candidate.course_id,
        skill_uri=candidate.skill_uri,
        decision="insufficient",
        confidence=0.0,
        reason=reason,
    )


def _validated_response(
    candidate: ConsolidatedCandidate,
    raw: Mapping[str, Any],
    confidence_threshold: float | None,
) -> EvidenceValidationResult:
    payload = dict(raw)
    payload["course_id"] = candidate.course_id
    payload["skill_uri"] = candidate.skill_uri
    result = EvidenceValidationResult.model_validate(payload)

    if result.decision == "yes" and confidence_threshold is not None:
        if result.confidence < confidence_threshold:
            return _insufficient(candidate, "Validator confidence is below the configured threshold.")

    evidence_by_id = {item.unit_id: item for item in candidate.top_evidence}
    for unit_id, quote in zip(result.evidence_unit_ids, result.evidence_quotes):
        evidence = evidence_by_id.get(unit_id)
        if evidence is None:
            raise ValueError(f"Validator cited unknown evidence unit: {unit_id}")
        if _normalized_text(quote) not in _normalized_text(evidence.evidence_text_en):
            raise ValueError(f"Validator quote is not present in evidence unit: {unit_id}")
    return result


def build_gemini_validation_backend(
    config: SkillMatchingConfig,
    prompt_path: Path | None = None,
) -> ValidationBackend:
    """Create a deterministic Gemini backend that can judge only the supplied candidate."""
    try:
        from google import genai
        from google.genai import types
        from google.genai.errors import APIError
    except ImportError as exc:
        raise RuntimeError("google-genai is required for evidence validation.") from exc

    from pipeline import key_manager
    import time

    instructions_path = prompt_path or ROOT_DIR / "prompts" / "evidence_validation.txt"
    instructions = instructions_path.read_text(encoding="utf-8")

    def validate(candidate: dict[str, Any]) -> Mapping[str, Any]:
        prompt = (
            f"{instructions}\n\n"
            "Consolidated candidate JSON:\n"
            f"{json.dumps(candidate, ensure_ascii=False, indent=2)}"
        )
        time.sleep(4.2)  # Throttle to ~14 requests per minute to stay under the 15 RPM free tier limit
        
        max_attempts = key_manager.get_total_keys() * 2
        for attempt in range(max_attempts):
            api_key = key_manager.get_api_key()
            try:
                client = genai.Client(api_key=api_key)
                response = client.models.generate_content(
                    model=config.evidence_validator_model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        temperature=config.evidence_validator_temperature,
                    ),
                )
                parsed = json.loads(response.text)
                if not isinstance(parsed, dict):
                    raise ValueError("Evidence validator response must be a JSON object.")
                return parsed
            except APIError as e:
                if e.code in (429, 503, 500) or "RESOURCE_EXHAUSTED" in str(e):
                    key_manager.rotate_key(api_key)
                    if attempt < max_attempts - 1:
                        time.sleep(2)
                        continue
                raise
        raise RuntimeError("Failed to validate evidence after retries.")

    return validate


class EvidenceValidator:
    """Validate consolidated candidates with strict provenance and a versioned cache."""

    def __init__(
        self,
        config: SkillMatchingConfig,
        backend: ValidationBackend | None = None,
    ) -> None:
        self.config = config
        self.backend = backend
        if config.evidence_validator_enabled and self.backend is None:
            self.backend = build_gemini_validation_backend(config)

    def _read_cache(self, path: Path, candidate: ConsolidatedCandidate) -> EvidenceValidationResult | None:
        if not path.exists():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            return _validated_response(candidate, payload["validation"], self.config.validation_confidence_threshold)
        except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            LOGGER.warning("Ignoring invalid evidence-validation cache %s: %s", path, exc)
            return None

    def _write_cache(self, path: Path, result: EvidenceValidationResult) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": "1.0",
            "model": self.config.evidence_validator_model,
            "prompt_version": self.config.evidence_validator_prompt_version,
            "validation": result.model_dump(mode="json", exclude_none=True),
        }
        temporary = path.with_suffix(".tmp")
        temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.replace(path)

    def validate_one(self, raw_candidate: dict[str, Any]) -> dict[str, Any]:
        candidate = ConsolidatedCandidate.model_validate(raw_candidate)
        cache_path = self.config.evidence_validation_cache_dir / f"{_cache_key(candidate, self.config)}.json"
        cached = self._read_cache(cache_path, candidate)
        if cached is not None:
            return ValidatedCandidate(candidate=candidate, validation=cached).model_dump(exclude_none=True)

        if not self.config.evidence_validator_enabled:
            result = _insufficient(candidate, "Evidence validation is disabled; candidates cannot be auto-accepted.")
        else:
            assert self.backend is not None
            result = None
            last_error: Exception | None = None
            for _ in range(self.config.evidence_validator_max_retries + 1):
                try:
                    raw = self.backend(candidate.model_dump(mode="json", exclude_none=True))
                    result = _validated_response(
                        candidate,
                        raw,
                        self.config.validation_confidence_threshold,
                    )
                    break
                except Exception as exc:  # Backend/schema failures are fail-closed by design.
                    last_error = exc
                    LOGGER.warning(
                        "Evidence validation failed for %s + %s: %s",
                        candidate.course_id,
                        candidate.skill_uri,
                        exc,
                    )
            if result is None:
                result = _insufficient(candidate, f"Invalid validator response: {last_error}")

        self._write_cache(cache_path, result)
        return ValidatedCandidate(candidate=candidate, validation=result).model_dump(exclude_none=True)

    def validate(self, candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Validate each already-consolidated course/skill candidate exactly once."""
        return [self.validate_one(candidate) for candidate in candidates]
