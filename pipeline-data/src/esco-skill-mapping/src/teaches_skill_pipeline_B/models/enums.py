"""Định nghĩa tất cả type literals và enum cho teaches-skill pipeline v3.

Tập trung hết kiểu dữ liệu phân loại vào 1 file duy nhất để đảm bảo
consistency xuyên suốt pipeline. Không import từ bất kỳ module nào
khác trong package.
"""

from __future__ import annotations

from typing import Literal

# ---------------------------------------------------------------------------
# Source Type — 4 loại evidence theo spec v3
# ---------------------------------------------------------------------------

SourceType = Literal["MO_TA", "MUC_TIEU", "CLO", "BAI_HOC"]

# ---------------------------------------------------------------------------
# Concept Type — trục phân tách skill / knowledge
# ---------------------------------------------------------------------------

ConceptType = Literal["skill", "knowledge"]

# ---------------------------------------------------------------------------
# Loại mục tiêu từ dữ liệu muc_tieu.json
# ---------------------------------------------------------------------------

LoaiMucTieu = Literal["KIEN_THUC", "KY_NANG", "TU_CHU_TRACH_NHIEM"]

# ---------------------------------------------------------------------------
# Content Richness — độ giàu thông tin của evidence
# ---------------------------------------------------------------------------

ContentRichness = Literal["full", "title_only"]

# ---------------------------------------------------------------------------
# Extraction Source — model nào đã sinh ra mention
# ---------------------------------------------------------------------------

ExtractionSource = Literal[
    "escoxlmr_skill",       # jjzha/escoxlmr_skill_extraction
    "escoxlmr_knowledge",   # jjzha/escoxlmr_knowledge_extraction
    "esco_extract_skill",   # công cụ nội bộ (trả ESCO URI trực tiếp)
    "skillspan",            # SkillSpan (bổ sung)
    "llm_fallback",         # LLM API fallback
]

# ---------------------------------------------------------------------------
# Extraction Head Type — skill head vs knowledge head (ESCOXLM-R)
# ---------------------------------------------------------------------------

HeadType = Literal["skill", "knowledge"]

# ---------------------------------------------------------------------------
# Retrieval Channel — kênh tìm kiếm
# ---------------------------------------------------------------------------

RetrievalChannel = Literal["bm25", "dense", "esco_extract"]

# ---------------------------------------------------------------------------
# Tier Level — phân tầng quyết định
# ---------------------------------------------------------------------------

TierLevel = Literal[
    "PRIMARY", "SECONDARY", "OPTIONAL",      # V3 tiers
    "HIGH", "MED", "low_confidence",          # Legacy backward-compat
]

# ---------------------------------------------------------------------------
# Confidence Level
# ---------------------------------------------------------------------------

ConfidenceLevel = Literal["HIGH", "MED", "LOW"]

# ---------------------------------------------------------------------------
# Relation Type — quan hệ trong Knowledge Graph
# ---------------------------------------------------------------------------

RelationType = Literal["TEACHES_SKILL", "TEACHES_KNOWLEDGE"]

# ---------------------------------------------------------------------------
# Course Type — loại học phần
# ---------------------------------------------------------------------------

CourseType = Literal["FOUNDATIONAL", "CORE", "SPECIALIZED"]

# ---------------------------------------------------------------------------
# Decision Status — trạng thái quyết định của candidate
# ---------------------------------------------------------------------------

DecisionStatus = Literal["ACCEPT", "REVIEW", "REJECT"]
