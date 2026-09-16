"""Tiện ích xử lý text dùng chung cho toàn pipeline."""

from __future__ import annotations

import re
import unicodedata


def normalize_whitespace(text: str) -> str:
    """Chuẩn hóa whitespace: collapse multiple spaces, strip."""
    return " ".join(str(text or "").split())


def strip_noise(text: str) -> str:
    """Loại bỏ noise phổ biến trong text evidence.

    - Ký tự điều khiển Unicode
    - Khoảng trắng thừa
    - Dấu bullet/numbering đầu dòng
    """
    if not text:
        return ""
    # Loại ký tự điều khiển
    text = "".join(
        ch for ch in text
        if unicodedata.category(ch) != "Cc" or ch in ("\n", "\t")
    )
    # Loại bullet/numbering đầu dòng: "1.", "a)", "•", "-"
    text = re.sub(r"^\s*[\d]+[.)]\s*", "", text)
    text = re.sub(r"^\s*[a-zA-Z][.)]\s*", "", text)
    text = re.sub(r"^\s*[•\-–—]\s*", "", text)
    return normalize_whitespace(text)


# Các marker chỉ sự kiện chấm điểm — không phải evidence thật
_GRADING_MARKERS = frozenset({
    "advisor grade", "reviewer grade", "final grade",
    "assessment method", "grading criteria",
})


def is_grading_event(text: str) -> bool:
    """Phát hiện câu liên quan đến chấm điểm — không phải evidence thật."""
    lowered = text.casefold()
    return any(marker in lowered for marker in _GRADING_MARKERS)


def truncate_for_model(text: str, max_tokens: int = 512) -> str:
    """Cắt text thô theo số từ (proxy cho token) để fit model input.

    Lưu ý: đây là approximation. Với transformer tokenizer thực,
    dùng tokenizer.encode() rồi truncate sẽ chính xác hơn.
    """
    words = text.split()
    if len(words) <= max_tokens:
        return text
    return " ".join(words[:max_tokens])
