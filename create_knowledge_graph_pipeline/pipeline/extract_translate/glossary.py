"""Glossary Việt-Anh đã duyệt cho các thuật ngữ học phần nhạy cảm ngữ cảnh."""

from __future__ import annotations

import json
import logging
from collections.abc import Callable
from pathlib import Path

LOGGER = logging.getLogger(__name__)
DEFAULT_GLOSSARY_FILENAME = "glossary_vi_en.json"


def load_glossary(path: str = DEFAULT_GLOSSARY_FILENAME) -> dict[str, str]:
    """Nạp glossary Việt-Anh; trả về dict rỗng và log cảnh báo nếu tệp không tồn tại.

    Đường dẫn mặc định được resolve cạnh module này để CLI có thể chạy từ thư mục dự án
    hoặc từ một thư mục làm việc khác mà vẫn tìm thấy glossary đóng gói cùng code.
    """
    glossary_path = Path(__file__).with_name(path) if path == DEFAULT_GLOSSARY_FILENAME else Path(path)
    if not glossary_path.exists():
        LOGGER.warning("Không tìm thấy glossary tại %s; tiếp tục dịch không dùng glossary.", glossary_path)
        return {}

    try:
        data = json.loads(glossary_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        LOGGER.warning("Không đọc được glossary %s: %s. Tiếp tục không dùng glossary.", glossary_path, exc)
        return {}
    if not isinstance(data, dict) or not all(isinstance(key, str) and isinstance(value, str) for key, value in data.items()):
        LOGGER.warning("Glossary %s phải có dạng {text_vi: text_en}; tiếp tục không dùng glossary.", glossary_path)
        return {}
    return data


def translate_with_glossary(
    texts: list[str],
    base_translate_fn: Callable[[list[str]], list[str]],
    glossary: dict[str, str],
) -> list[str]:
    """Dịch một batch, ưu tiên bản dịch đã duyệt trong glossary theo khớp chính xác.

    Mỗi text được ``strip`` chỉ để tra glossary. Các text không khớp được gom thành đúng
    một batch gọi ``base_translate_fn``; thứ tự và số lượng phần tử đầu ra luôn khớp đầu vào.
    """
    normalized_glossary = {key.strip(): value for key, value in glossary.items()}
    translated: list[str | None] = [None] * len(texts)
    unmatched_indexes: list[int] = []
    unmatched_texts: list[str] = []

    for index, text in enumerate(texts):
        approved_translation = normalized_glossary.get(text.strip())
        if approved_translation is not None:
            translated[index] = approved_translation
        else:
            unmatched_indexes.append(index)
            unmatched_texts.append(text)

    if unmatched_texts:
        base_translations = base_translate_fn(unmatched_texts)
        if len(base_translations) != len(unmatched_texts):
            raise ValueError("base_translate_fn phải trả về số phần tử đúng bằng batch đầu vào.")
        for index, translation in zip(unmatched_indexes, base_translations):
            translated[index] = translation

    return [translation for translation in translated if translation is not None]
