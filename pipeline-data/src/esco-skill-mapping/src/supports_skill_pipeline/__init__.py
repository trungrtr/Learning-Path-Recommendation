"""supports-skill-pipeline M5 — Pipeline tìm và gán nhãn quan hệ SUPPORTS_SKILL.

Entry point:
    from supports_skill_pipeline import SupportsSkillPipeline, PipelineConfig

    config = PipelineConfig.from_yaml("configs/default_config.yaml")
    pipeline = SupportsSkillPipeline(config)

    # Bước 1→6: Trích xuất + export cho reviewer
    pipeline.run_course("IT304")

    # Bước 7: Sau khi reviewer hoàn thành → ghi SUPPORTS_SKILL
    records = pipeline.finalize_course("IT304")

Kiến trúc:
    S1  (Preprocessing)        → Gộp Description + Objectives + CLO thành context
    S2  (Concept Extraction)   → LLM trích xuất support concepts (keyword thô)
    S3  (Retrieval)            → BM25 + FAISS + ESCOXLM-R (3 kênh độc lập)
    S4  (RRF Fusion)           → Reciprocal Rank Fusion hợp nhất 3 kênh
    S5  (Multi-signal Ranking) → α·RRF + β·ESCOXLMR + γ·Evidence → Top 5-10
    S6  (Human Review)         → Export CSV/JSON cho reviewer (ACCEPT/REJECT)
    S7  (Export)               → JSON output + Cypher/Neo4j

Ràng buộc cứng:
    - LLM KHÔNG gán nhãn SUPPORTS_SKILL — chỉ trích concept thô
    - Phải qua Human Review trước khi ghi quan hệ chính thức
    - Pipeline ĐỘC LẬP với M4 (TEACHES_SKILL)
    - Mọi candidate phải thuộc Filtered ESCO Pool
"""

from .pipeline import SupportsSkillPipeline
from .configs import PipelineConfig

__all__ = [
    "SupportsSkillPipeline",
    "PipelineConfig",
]
