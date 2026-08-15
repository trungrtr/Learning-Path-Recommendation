"""Tách course JSON thành text unit và chuẩn bị bản dịch tiếng Anh."""

from .course_units import extract_units, mock_translate_fn, translate_units
from .gemini_backend import build_gemini_translate_fn
from .glossary import load_glossary, translate_with_glossary

__all__ = [
    "build_gemini_translate_fn",
    "extract_units",
    "load_glossary",
    "mock_translate_fn",
    "translate_units",
    "translate_with_glossary",
]
