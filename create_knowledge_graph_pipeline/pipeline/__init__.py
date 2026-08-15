"""Các bước xử lý dữ liệu của course_kg_pipeline."""

__all__ = ["clean_extracted_document", "is_garbage_clo", "merge_group", "validate_canonical_course"]


def __getattr__(name: str):
    """Lazy import để stage độc lập không phải nạp dependency của stage merge."""
    if name in {"clean_extracted_document", "is_garbage_clo"}:
        from .merge.cleaning import clean_extracted_document, is_garbage_clo

        return {"clean_extracted_document": clean_extracted_document, "is_garbage_clo": is_garbage_clo}[name]
    if name in {"merge_group", "validate_canonical_course"}:
        from .merge.__main__ import merge_group, validate_canonical_course

        return {"merge_group": merge_group, "validate_canonical_course": validate_canonical_course}[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
