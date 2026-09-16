"""EvidenceUnit v3 — đơn vị minh chứng chuẩn hóa cho teaches-skill pipeline.

Cập nhật so với EvidenceUnit cũ (pipeline.shared_models):
- source_type dùng 4 giá trị: MO_TA, MUC_TIEU, CLO, BAI_HOC
- Thêm source_id (G1, L1, L01...) để nối provenance
- Thêm meta dict chứa loai_muc_tieu, content_richness, linked_clo
- Luôn ưu tiên text tiếng Anh (_en) cho extraction
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .enums import SourceType, ContentRichness, LoaiMucTieu


@dataclass(frozen=True)
class EvidenceUnit:
    """Một đơn vị minh chứng đã chuẩn hóa, sẵn sàng đưa vào extraction.

    Attributes:
        evidence_id: ID duy nhất, format: {course_code}_{source_type}_{source_id}
            Ví dụ: "IT6204_MUCTIEU_G2", "IT6204_CLO_L1", "IT6204_BAIHOC_05"
        course_code: Mã học phần (IT6204).
        source_type: MO_TA | MUC_TIEU | CLO | BAI_HOC.
        source_id: Mã con bên trong source (G1, L1, L05...). Với MO_TA thì "MAIN".
        text: Văn bản tiếng Anh đã chuẩn hóa (dùng cho extraction/matching).
        text_vi: Văn bản tiếng Việt gốc (chỉ dùng hiển thị / human review).
        meta: Metadata bổ sung, tùy loại evidence:
            - MUC_TIEU: {"loai_muc_tieu": "KY_NANG"}
            - BAI_HOC: {"content_richness": "title_only", "linked_clo": ["L2","L3"]}
            - CLO: {"pi_so": [...]}
    """
    evidence_id: str
    course_code: str
    source_type: SourceType
    source_id: str
    text: str
    text_vi: str = ""
    meta: dict[str, Any] = field(default_factory=dict)
    # [PATCH v3.0 — Evidence Quality Weighting & Boilerplate Filter]
    # Lý do: Gán trọng số chất lượng bằng chứng và gắn cờ câu mẫu khuôn sáo
    # Ảnh hưởng: models/evidence.py, t05_evidence, t1_extraction, t5_decision
    evidence_weight: float = 0.30
    is_boilerplate: bool = False

    @property
    def content_richness(self) -> ContentRichness:
        """Trả về độ giàu thông tin của evidence."""
        return self.meta.get("content_richness", "full")

    @property
    def loai_muc_tieu(self) -> LoaiMucTieu | None:
        """Trả về loại mục tiêu nếu evidence là MUC_TIEU."""
        return self.meta.get("loai_muc_tieu")

    @property
    def linked_clo(self) -> list[str]:
        """Trả về danh sách CLO liên kết (cho BAI_HOC)."""
        return self.meta.get("linked_clo", [])
