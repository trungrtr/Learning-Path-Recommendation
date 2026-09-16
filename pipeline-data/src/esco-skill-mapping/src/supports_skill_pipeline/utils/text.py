"""Text normalization utilities cho supports_skill_pipeline.

Chuẩn hóa văn bản: loại HTML, chuẩn hóa khoảng trắng, unicode.
"""

from __future__ import annotations

import re
import unicodedata


def normalize_whitespace(text: str) -> str:
    """Chuẩn hóa khoảng trắng: loại bỏ thừa, trim."""
    if not text:
        return ""
    text = text.strip()
    text = re.sub(r"\s+", " ", text)
    return text


def strip_html_tags(text: str) -> str:
    """Loại bỏ HTML tags khỏi text."""
    if not text:
        return ""
    return re.sub(r"<[^>]+>", " ", text)


def normalize_unicode(text: str) -> str:
    """Chuẩn hóa unicode (NFC form)."""
    if not text:
        return ""
    return unicodedata.normalize("NFC", text)


def clean_text(text: str) -> str:
    """Pipeline chuẩn hóa text đầy đủ: HTML → unicode → whitespace."""
    text = strip_html_tags(text)
    text = normalize_unicode(text)
    text = normalize_whitespace(text)
    return text


def slugify_label(label: str) -> str:
    """Chuyển label thành slug cho tên file.

    Ví dụ: "database design" → "database_design"
    """
    if not label:
        return "unknown"
    slug = label.strip().lower()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s-]+", "_", slug)
    return slug
