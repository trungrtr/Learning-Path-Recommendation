"""teaches-skill-pipeline v3 — Pipeline ánh xạ kỹ năng/kiến thức ESCO.

Entry point:
    from teaches_skill_pipeline import TeachesSkillPipeline, PipelineConfig

    config = PipelineConfig.from_yaml("configs/default_config.yaml")
    pipeline = TeachesSkillPipeline(config)
    records = pipeline.run_course("IT6204")

Kiến trúc:
    T0  (Ingestion)       → Đọc, validate 4 file JSON/học phần
    T0.5 (Evidence)       → Build 4 loại evidence: MO_TA, MUC_TIEU, CLO, BAI_HOC
    T1  (Extraction)      → Ensemble 4 nguồn NLP (ESCOXLM-R, esco-extract-skill,
                             SkillSpan, LLM fallback)
    T2  (Matching)        → BM25 + Dense (FAISS) matching mention → ESCO
    T3  (Fusion)          → Reciprocal Rank Fusion (RRF)
    T4  (Reranking)       → Cross-Encoder UniSkill rerank
    T5  (Decision)        → 3-tier threshold (PRIMARY/SECONDARY/OPTIONAL)
    T6  (Normalization)   → ESCO URI/label/skill_type chuẩn hóa
    T7  (Classification)  → Skill vs Knowledge (ESCO + tín hiệu phụ trợ)
    T8  (Provenance)      → Gắn nguồn gốc đầy đủ
    T9  (Aggregation)     → Dedup + trọng số evidence cấp học phần
    T10 (Export)          → JSON + Cypher/Neo4j
"""

from .pipeline import TeachesSkillPipeline
from .configs import PipelineConfig

__all__ = [
    "TeachesSkillPipeline",
    "PipelineConfig",
]
