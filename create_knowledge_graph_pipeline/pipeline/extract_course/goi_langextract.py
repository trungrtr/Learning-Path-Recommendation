"""Điểm tích hợp duy nhất với LangExtract và Gemini."""

from __future__ import annotations

import os
from typing import Any

from pipeline.extract_course.schema_langextract import build_output_schema


def extract_from_markdown(
    markdown_text: str,
    prompt: str,
    settings: dict[str, Any],
) -> list[Any]:
    """Gọi LangExtract và chỉ giữ kết quả có vị trí nguồn (grounded).

    Lọc ``char_interval is None`` ngăn dữ liệu do LLM suy diễn hoặc lấy nhầm từ
    ví dụ few-shot đi vào JSON chuẩn.
    """
    try:
        import langextract as lx
    except ImportError as exc:
        raise RuntimeError("Thiếu langextract. Hãy chạy: pip install -r requirements.txt") from exc

    from pipeline import key_manager
    import time
    
    max_attempts = key_manager.get_total_keys() * 2
    for attempt in range(max_attempts):
        api_key = key_manager.get_api_key()
        try:
            # Temperature bằng 0 làm kết quả ổn định hơn, giúp dữ liệu KG có thể tái lập khi chạy lại.
            result = lx.extract(
                text_or_documents=markdown_text,
                prompt_description=prompt,
                examples=[],
                model_id=settings["extractor_model"],
                output_schema=build_output_schema(lx),
                api_key=api_key,
                temperature=0.0,
                max_char_buffer=settings["max_char_buffer"],
                extraction_passes=settings["extraction_passes"],
            )
            # Chỉ nhận mảnh có vị trí trong Markdown để loại kết quả suy diễn không có bằng chứng nguồn.
            return [item for item in (result.extractions or []) if item.char_interval is not None]
        except Exception as exc:
            err_str = str(exc)
            if "429" in err_str or "503" in err_str or "500" in err_str or "Quota exceeded" in err_str or "Too Many Requests" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                key_manager.rotate_key(api_key)
                if attempt < max_attempts - 1:
                    time.sleep(2)
                    continue
            raise
