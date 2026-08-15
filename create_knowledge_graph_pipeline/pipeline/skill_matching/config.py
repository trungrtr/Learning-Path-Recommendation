"""Cấu hình và resolve đường dẫn cho pipeline đối sánh skill."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pipeline.extract_course.cau_hinh import DEFAULT_CONFIG, ROOT_DIR, load_settings


def _resolve_path(value: str) -> Path:
    """Resolve đường dẫn cấu hình tương đối với thư mục gốc pipeline."""
    path = Path(value)
    return path if path.is_absolute() else ROOT_DIR / path


@dataclass(frozen=True)
class SkillMatchingConfig:
    """Các dependency và ngưỡng điều khiển bốn bước A→D của skill matching."""

    input_dir: Path
    output_dir: Path
    evidence_validation_cache_dir: Path
    pool_cache_dir: Path
    data_dir: Path
    esco_occupations_csv: Path
    esco_skills_csv: Path
    esco_relations_csv: Path
    embedding_model_dir: Path
    retrieval_threshold: float
    retrieval_top_k: int
    retrieval_query_types: tuple[str, ...]
    description_chunk_tokens: int
    description_chunk_overlap_tokens: int
    uniskill_seed_dir: Path
    uniskill_model_dir: Path
    allow_seed_model_fallback: bool
    positive_label_id: int
    rerank_threshold: float
    max_validation_evidence: int
    validator_top_n_per_course: int
    max_skills_per_course: int | None
    evidence_validator_enabled: bool
    evidence_validator_model: str
    evidence_validator_prompt_version: str
    evidence_validator_temperature: float
    evidence_validator_max_retries: int
    validation_confidence_threshold: float | None
    output_calibration_status: str
    device: str | None
    embedding_batch_size: int
    rerank_batch_size: int
    max_length: int
    training_pairs_path: Path
    training_epochs: int
    training_batch_size: int
    training_learning_rate: float
    negatives_per_positive: int
    training_seed: int


def load_skill_matching_config(config_path: Path = DEFAULT_CONFIG) -> SkillMatchingConfig:
    """Tạo config typed từ ``config.yaml`` mà không hard-code đường dẫn/model trong module."""
    settings: dict[str, Any] = load_settings(config_path)
    paths = settings["paths"]
    matching = settings["skill_matching"]
    return SkillMatchingConfig(
        input_dir=_resolve_path(paths["translated_units_dir"]),
        output_dir=_resolve_path(paths["skill_matches_dir"]),
        evidence_validation_cache_dir=_resolve_path(paths["evidence_validation_cache_dir"]),
        pool_cache_dir=_resolve_path(paths["skill_pool_cache_dir"]),
        data_dir=_resolve_path(paths["skill_matching_data_dir"]),
        esco_occupations_csv=_resolve_path(matching["esco_occupations_csv"]),
        esco_skills_csv=_resolve_path(matching["esco_skills_csv"]),
        esco_relations_csv=_resolve_path(matching["esco_relations_csv"]),
        embedding_model_dir=_resolve_path(matching["embedding_model_dir"]),
        retrieval_threshold=float(matching["retrieval_threshold"]),
        retrieval_top_k=int(matching["retrieval_top_k"]),
        retrieval_query_types=tuple(str(query_type) for query_type in matching["retrieval_query_types"]),
        description_chunk_tokens=int(matching["description_chunk_tokens"]),
        description_chunk_overlap_tokens=int(matching["description_chunk_overlap_tokens"]),
        uniskill_seed_dir=_resolve_path(matching["uniskill_seed_dir"]),
        uniskill_model_dir=_resolve_path(matching["uniskill_model_dir"]),
        allow_seed_model_fallback=bool(matching["allow_seed_model_fallback"]),
        positive_label_id=int(matching["positive_label_id"]),
        rerank_threshold=float(matching["rerank_threshold"]),
        max_validation_evidence=int(matching["max_validation_evidence"]),
        validator_top_n_per_course=int(matching["validator_top_n_per_course"]),
        max_skills_per_course=(
            int(matching["max_skills_per_course"])
            if matching.get("max_skills_per_course") is not None
            else None
        ),
        evidence_validator_enabled=bool(matching["evidence_validator_enabled"]),
        evidence_validator_model=str(matching["evidence_validator_model"]),
        evidence_validator_prompt_version=str(matching["evidence_validator_prompt_version"]),
        evidence_validator_temperature=float(matching["evidence_validator_temperature"]),
        evidence_validator_max_retries=int(matching["evidence_validator_max_retries"]),
        validation_confidence_threshold=(
            float(matching["validation_confidence_threshold"])
            if matching.get("validation_confidence_threshold") is not None
            else None
        ),
        output_calibration_status=str(matching["output_calibration_status"]),
        device=matching.get("device"),
        embedding_batch_size=int(matching["embedding_batch_size"]),
        rerank_batch_size=int(matching["rerank_batch_size"]),
        max_length=int(matching["max_length"]),
        training_pairs_path=_resolve_path(paths["skill_training_pairs_path"]),
        training_epochs=int(matching["training_epochs"]),
        training_batch_size=int(matching["training_batch_size"]),
        training_learning_rate=float(matching["training_learning_rate"]),
        negatives_per_positive=int(matching["negatives_per_positive"]),
        training_seed=int(matching["training_seed"]),
    )
