"""Pipeline Configuration — Pydantic v2 config cho teaches-skill pipeline v3.

Tập trung toàn bộ cấu hình vào 1 object, load từ YAML hoặc truyền trực tiếp.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field


class ExtractionConfig(BaseModel):
    """Cấu hình cho Tầng 1 (Ensemble Extraction)."""
    use_escoxlmr: bool = True
    use_esco_extract_skill: bool = True
    use_skillspan: bool = False
    use_llm_fallback: bool = True
    target_head: Literal["all", "skill", "knowledge"] = "all"
    
    escoxlmr_skill_model: str = "jjzha/escoxlmr_skill_extraction"
    escoxlmr_knowledge_model: str = "jjzha/escoxlmr_knowledge_extraction"
    skillspan_model: str | None = None   # None = tắt SkillSpan
    llm_model: str = "gemini-3.1-flash-lite"
    llm_temperature: float = 0.0
    enable_skillspan: bool = False       # Mặc định tắt — cần xác nhận checkpoint
    enable_llm_fallback: bool = True
    cache_dir: str = "cache/extraction"


class RetrievalConfig(BaseModel):
    """Cấu hình cho Tầng 2+3 — Matching + Fusion."""
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
    faiss_index_path: str = "data/esco_filtered/v1/faiss/esco_full.index"
    faiss_metadata_path: str = "data/esco_filtered/v1/faiss/esco_metadata.json"
    bm25_index_path: str = "data/esco_filtered/v1/bm25/bm25_corpus.pkl"
    top_k_per_channel: int = 50
    rrf_k: int = 60


class RerankConfig(BaseModel):
    """Cấu hình cho Tầng 4 — Cross-encoder reranking."""
    model: str = "nurlanm/UniSkill_Bert"
    rerank_top_k: int = 30         # Chỉ rerank top-K sau RRF
    rerank_weight: float = 0.7     # Trọng số rerank trong combined_score
    rrf_weight: float = 0.3        # Trọng số RRF trong combined_score


class ThresholdConfig(BaseModel):
    """Cấu hình cho Tầng 5 — Decision thresholds."""
    # Skill thresholds
    skill_primary: float = 0.85
    skill_secondary: float = 0.75
    skill_optional: float = 0.60
    skill_overflow: float = 0.40
    # Knowledge thresholds (hạ 5% so với skill)
    knowledge_primary: float = 0.80
    knowledge_secondary: float = 0.65
    knowledge_optional: float = 0.50
    knowledge_overflow: float = 0.35


class HardCapConfig(BaseModel):
    """Giới hạn số lượng tối đa theo course_type."""
    foundational_skill: int = 7
    foundational_knowledge: int = 13
    core_skill: int = 15
    core_knowledge: int = 15
    specialized_skill: int = 25
    specialized_knowledge: int = 15


class EvidenceWeightConfig(BaseModel):
    """Trọng số evidence theo loại — Tầng 9."""
    mo_ta: float = 1.0
    muc_tieu: float = 1.2          # Ưu tiên cao nhất — có loai_muc_tieu sẵn
    clo: float = 1.0
    bai_hoc_full: float = 0.7      # Có nội dung
    bai_hoc_title_only: float = 0.3 # Chỉ tiêu đề


class OutputConfig(BaseModel):
    """Cấu hình đường dẫn output."""
    output_dir: str = "data/data_teaches_skill"
    write_candidate_log: bool = True
    write_audit_log: bool = True
    write_provenance: bool = True


class EvidenceWeightingConfig(BaseModel):
    """Cấu hình cho PATCH A — Evidence Quality Weighting."""
    enabled: bool = True
    low_quality_threshold: float = 0.35
    weight_map: dict[str, float] = Field(default_factory=lambda: {
        "BAI_HOC_full": 1.00,
        "BAI_HOC_title_only": 0.30,
        "CLO_KIEN_THUC": 0.90,
        "CLO_KY_NANG": 0.85,
        "CLO_TU_CHU_TRACH_NHIEM": 0.20,
        "MUC_TIEU_KIEN_THUC": 0.70,
        "MUC_TIEU_KY_NANG": 0.65,
        "MUC_TIEU_TU_CHU_TRACH_NHIEM": 0.15,
        "MO_TA": 0.25,
        "default": 0.30,
    })


class BoilerplateFilterConfig(BaseModel):
    """Cấu hình cho PATCH B — Boilerplate Sentence Filter."""
    enabled: bool = True
    sparse_course_boilerplate_ratio: float = 0.60


class CourseFilterConfig(BaseModel):
    """Lọc các học phần không mang kỹ năng chuyên ngành (như Triết học, Chính trị)."""
    enabled: bool = True
    ignored_keywords: list[str] = Field(default_factory=lambda: [
        "triết học",
        "chính trị",
        "mác - lênin",
        "mác-lênin",
        "tư tưởng hồ chí minh",
        "đảng cộng sản",
        "chủ nghĩa xã hội",
        "pháp luật đại cương",
        "kinh tế",
        "âm nhạc",
        "giáo dục thể chất",
        "quốc phòng",
        "ngoại ngữ"
    ])


class DomainFilterConfig(BaseModel):
    """Cấu hình cho PATCH C — Domain Block List."""
    enabled: bool = True
    blocked_uris: list[str] = Field(default_factory=lambda: [
        "http://data.europa.eu/esco/skill/e8f80ec5-c423-4eb2-9f0f-805d22f844ae",
    ])
    keyword_block_enabled: bool = True


class SecurityDriftGuardConfig(BaseModel):
    """Cấu hình cho PATCH D — Security Cluster Drift Guard."""
    enabled: bool = True
    offensive_uris: list[str] = Field(default_factory=lambda: [
        "http://data.europa.eu/esco/skill/af313ba1-a39e-49ac-99ec-94630fbe4f7f",
    ])


class FrameworkItem(BaseModel):
    label: str
    aliases: list[str] = Field(default_factory=list)


class FrameworkGuardConfig(BaseModel):
    """Cấu hình cho PATCH E — IT Governance Framework Guard."""
    enabled: bool = True
    frameworks: list[dict[str, Any]] = Field(default_factory=list)


class CapstoneCoursesConfig(BaseModel):
    """Cấu hình cho PATCH F — Capstone Course Stricter Rules."""
    enabled: bool = True
    course_codes: list[str] = Field(default_factory=lambda: [
        "IT6205", "IT6206", "IT6207", "IT6208"
    ])
    detection_keywords: list[str] = Field(default_factory=lambda: [
        "internship", "graduation thesis", "graduation project", "final project"
    ])
    hard_cap_override: int = 10
    confidence_threshold_override: float = 0.740
    require_min_avg_evidence_weight: float = 0.40
    reject_if_sparse_and_mismatch: bool = True


class MismatchPenaltyConfig(BaseModel):
    """Cấu hình cho PATCH G — Mismatch Confidence Penalty."""
    enabled: bool = True
    penalty_value: float = 0.025


class PipelineConfig(BaseModel):
    """Cấu hình tổng cho toàn bộ teaches-skill pipeline v3."""
    # Đường dẫn đầu vào
    contract_dir: str = "../../contract"

    # Sub-configs
    extraction: ExtractionConfig = Field(default_factory=ExtractionConfig)
    retrieval: RetrievalConfig = Field(default_factory=RetrievalConfig)
    rerank: RerankConfig = Field(default_factory=RerankConfig)
    threshold: ThresholdConfig = Field(default_factory=ThresholdConfig)
    hard_cap: HardCapConfig = Field(default_factory=HardCapConfig)
    evidence_weight: EvidenceWeightConfig = Field(default_factory=EvidenceWeightConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)

    # Patch sub-configs (v3)
    evidence_weighting: EvidenceWeightingConfig = Field(default_factory=EvidenceWeightingConfig)
    boilerplate_filter: BoilerplateFilterConfig = Field(default_factory=BoilerplateFilterConfig)
    course_filter: CourseFilterConfig = Field(default_factory=CourseFilterConfig)
    domain_filter: DomainFilterConfig = Field(default_factory=DomainFilterConfig)
    security_drift_guard: SecurityDriftGuardConfig = Field(default_factory=SecurityDriftGuardConfig)
    framework_guard: FrameworkGuardConfig = Field(default_factory=FrameworkGuardConfig)
    capstone_courses: CapstoneCoursesConfig = Field(default_factory=CapstoneCoursesConfig)
    mismatch_penalty: MismatchPenaltyConfig = Field(default_factory=MismatchPenaltyConfig)

    # Neo4j
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_database: str = "neo4j"

    # Schema version
    schema_version: str = "3.0"

    @classmethod
    def from_yaml(cls, path: str | Path) -> PipelineConfig:
        """Load config từ file YAML."""
        import yaml
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return cls(**data)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PipelineConfig:
        """Load config từ dict."""
        return cls(**data)
