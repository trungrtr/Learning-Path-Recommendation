"""Unit tests cho glossary thuật ngữ Việt-Anh đã duyệt."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline.extract_translate.glossary import translate_with_glossary


def test_glossary_translation_does_not_call_backend_for_approved_text() -> None:
    """Thuật ngữ khớp glossary phải bỏ qua hoàn toàn backend dịch."""
    def backend_should_not_run(texts: list[str]) -> list[str]:
        raise AssertionError(f"Backend must not receive glossary text: {texts}")

    translated = translate_with_glossary(
        ["  Phân tích định thức  "],
        backend_should_not_run,
        {"Phân tích định thức": "Determinant Calculation"},
    )

    assert translated == ["Determinant Calculation"]


def test_glossary_batches_only_unmatched_texts() -> None:
    """Chỉ các text không khớp mới được gửi tới backend trong một batch."""
    calls: list[list[str]] = []

    def backend(texts: list[str]) -> list[str]:
        calls.append(texts)
        return [f"EN:{text}" for text in texts]

    translated = translate_with_glossary(
        ["Phân tích định thức", "Nội dung khác", "Xử lý không gian véc tơ"],
        backend,
        {
            "Phân tích định thức": "Determinant Calculation",
            "Xử lý không gian véc tơ": "Working with Vector Spaces",
        },
    )

    assert calls == [["Nội dung khác"]]
    assert translated == ["Determinant Calculation", "EN:Nội dung khác", "Working with Vector Spaces"]
