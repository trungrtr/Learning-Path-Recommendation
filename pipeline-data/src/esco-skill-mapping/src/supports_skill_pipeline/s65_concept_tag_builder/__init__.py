"""Bước 6.5 — Concept Tag Builder cho supports_skill_pipeline.

Chuyển đổi Raw Concepts (từ S2) đã accepted (sau S6) thành:
- ConceptTag nodes (deduplicated, phân loại)
- HAS_CONCEPT edges: HocPhan → ConceptTag (role="support")
- EVIDENCE_FOR edges: ConceptTag → KyNangESCO

Side-output thuần túy — không ảnh hưởng SupportSkillRecord hay luồng chính.
"""

from .builder import build_concept_tags

__all__ = ["build_concept_tags"]
