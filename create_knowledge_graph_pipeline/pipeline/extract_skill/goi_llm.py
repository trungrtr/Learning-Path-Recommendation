import json
import os
import logging
from typing import Any

LOGGER = logging.getLogger(__name__)

PROMPT_TEMPLATE = """Bạn là chuyên gia thiết kế chương trình đào tạo đại học và chuẩn hóa năng lực nghề nghiệp.
Nhiệm vụ là SKILL-HÓA đề cương học phần: trích xuất các cụm kỹ năng/chuyên môn có thể đối sánh với taxonomy nghề nghiệp ở bước sau.

Nguồn dữ liệu học phần:
{course_data}

Quy tắc bắt buộc:
1. Chỉ tạo skill phrase có bằng chứng rõ ràng trong mô tả, CLO, chapter hoặc lesson. Không suy diễn kiến thức không xuất hiện.
2. Mỗi phần tử là một cụm kỹ năng/chủ đề chuyên môn ngắn gọn bằng tiếng Việt, không phải câu mô tả, không ghi ESCO URI và không tự đặt tên taxonomy.
3. Giữ nguyên thuật ngữ chuyên ngành; không thay bằng khái niệm rộng hơn. Ví dụ: giữ "Chuẩn hóa quan hệ" thay vì chỉ "Cơ sở dữ liệu" khi nội dung nói về chuẩn hóa.
4. Tách các kỹ năng độc lập, gộp các biến thể trùng nghĩa. Không lặp lại tên học phần trừ khi chính nó là một năng lực/chủ đề kỹ thuật có thể đối sánh.
5. Không đưa vào các kỹ năng chung chung như "tư duy", "học tập", "giao tiếp" nếu không có bằng chứng trực tiếp trong CLO/mô tả.
6. Danh sách cần ưu tiên độ chính xác hơn số lượng; thường 3–15 cụm tùy mức độ chi tiết của đề cương.

Trả về DUY NHẤT một JSON array các string, không Markdown, không giải thích.
"""

def extract_skills_with_llm(
    course_data: dict[str, Any],
    model_name: str | None = None,
    temperature: float = 0.0,
) -> list[str]:
    """Skill-hóa một course Layer 2 thành các cụm skill phrase có bằng chứng nguồn."""
    # Chỉ chuyển các trường ngữ nghĩa sang prompt; ID nội bộ không giúp mô hình suy luận kỹ năng.
    # Đưa toàn bộ nội dung merge (name, description, clos, chapters, lessons) để LLM trích xuất skill đầy đủ.
    lessons_raw = course_data.get("lessons", [])
    lessons_titles: list[str] = []
    seen: set[str] = set()
    for item in lessons_raw:
        title = item.get("title") or "" if isinstance(item, dict) else str(item) if item else ""
        if title and title.casefold() not in seen:
            lessons_titles.append(title)
            seen.add(title.casefold())
    text_input = json.dumps({
        "name_vi": course_data.get("course", {}).get("name_vi"),
        "name_en": course_data.get("course", {}).get("name_en"),
        "description": course_data.get("description", {}).get("text"),
        "clos": [{"id": c.get("clo_id"), "content": c.get("content")} for c in course_data.get("clos", [])],
        "chapters": [{"id": ch.get("chapter_id"), "title": ch.get("title")} for ch in course_data.get("chapters", [])],
        "lessons": lessons_titles,
    }, ensure_ascii=False, indent=2)
    
    # Dùng JSON đã serialize để giữ nguyên tiếng Việt và cấu trúc CLO/chương trong prompt.
    prompt = PROMPT_TEMPLATE.replace("{course_data}", text_input)
    
    from pipeline import key_manager
    import time
    
    max_attempts = key_manager.get_total_keys() * 2
    for attempt in range(max_attempts):
        api_key = key_manager.get_api_key()
        try:
            from google import genai
            from google.genai import types
            from google.genai.errors import APIError
            
            resolved_model = model_name or os.getenv("SKILLIZATION_MODEL") or os.getenv("EXTRACTOR_MODEL", "gemini-3.1-flash-lite")
            if attempt == 0:
                LOGGER.info(f"Đang gọi Gemini AI API ({resolved_model})...")
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model=resolved_model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=temperature,
                ),
            )
            
            # response_mime_type yêu cầu JSON, nhưng vẫn kiểm tra kiểu để tránh làm hỏng contract Layer 3.
            data = json.loads(response.text)
            values = data if isinstance(data, list) else [data]
            # Chuẩn hóa nhẹ để giữ contract list[str], đồng thời bỏ kỹ năng rỗng/trùng lặp từ LLM.
            unique_skills: list[str] = []
            seen: set[str] = set()
            for value in values:
                if not isinstance(value, str) or not value.strip():
                    continue
                normalized = value.strip()
                key = normalized.casefold()
                if key not in seen:
                    unique_skills.append(normalized)
                    seen.add(key)
            return unique_skills
        except APIError as e:
            if e.code in (429, 503, 500) or "RESOURCE_EXHAUSTED" in str(e):
                key_manager.rotate_key(api_key)
                if attempt < max_attempts - 1:
                    time.sleep(2)
                    continue
            LOGGER.error(f"Lỗi API khi gọi LLM: {e}")
            return []
        except Exception as e:
            LOGGER.error(f"Lỗi hệ thống khi gọi LLM: {e}")
            return []
    return []
