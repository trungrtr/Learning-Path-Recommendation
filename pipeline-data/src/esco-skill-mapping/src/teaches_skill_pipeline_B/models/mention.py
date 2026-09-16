"""RawMention — mention thô trích xuất từ Tầng 1 (NLP ensemble).

Đây là sản phẩm trung gian giữa Tầng 1 (extraction) và Tầng 2 (matching).
Mention thô chưa có ESCO URI — cần đi qua BM25/Dense matcher để tìm ESCO
concept tương ứng.

Ngoại lệ: Nguồn B (esco-extract-skill) trả thẳng ESCO URI → dùng
DirectCandidate thay vì RawMention, bỏ qua Tầng 2.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .enums import ExtractionSource, HeadType


@dataclass(frozen=True)
class RawMention:
    """Mention thô từ extraction — chưa ánh xạ sang ESCO.

    Attributes:
        text: Chuỗi mention trích xuất (ví dụ: "software design").
        evidence_id: ID của evidence unit nguồn.
        source: Model/nguồn nào đã sinh ra mention này.
        head_type: Mention đến từ skill head hay knowledge head
            (chỉ có ý nghĩa với ESCOXLM-R). None cho các nguồn khác.
        confidence: Điểm tin cậy từ model (0.0–1.0). None nếu không có.
        char_start: Vị trí ký tự bắt đầu trong evidence text. None nếu không có.
        char_end: Vị trí ký tự kết thúc trong evidence text. None nếu không có.
    """
    text: str
    evidence_id: str
    source: ExtractionSource
    head_type: HeadType | None = None
    confidence: float | None = None
    char_start: int | None = None
    char_end: int | None = None
    source_text: str = ""


@dataclass(frozen=True)
class DirectCandidate:
    """Ứng viên ESCO trực tiếp từ esco-extract-skill (Nguồn B).

    Bỏ qua Tầng 2 (matching), đi thẳng vào Tầng 3 (RRF fusion).

    Attributes:
        skill_uri: URI ESCO đầy đủ.
        skill_label: Tên ESCO preferred label.
        evidence_id: ID evidence nguồn.
        score: Điểm từ esco-extract-skill.
        source: Luôn là "esco_extract_skill".
    """
    skill_uri: str
    skill_label: str
    evidence_id: str
    score: float = 0.0
    source: ExtractionSource = "esco_extract_skill"
