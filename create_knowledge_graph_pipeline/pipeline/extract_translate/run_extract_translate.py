"""CLI chạy trích xuất text unit và dịch mock cho một file hoặc thư mục Layer 3."""

from __future__ import annotations

import argparse
import json
import logging
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from pipeline.extract_course.cau_hinh import DEFAULT_CONFIG, ROOT_DIR, load_settings
from pipeline.extract_translate.course_units import (
    DEFAULT_PROMPT_VERSION,
    TranslateFunction,
    extract_units,
    mock_translate_fn,
    translate_units,
)
from pipeline.extract_translate.gemini_backend import build_gemini_translate_fn

LOGGER = logging.getLogger(__name__)
CACHE_FILENAME = "vi_en.json"


def _json_files(input_path: Path) -> Iterable[Path]:
    """Trả về một file JSON hoặc các file JSON trực tiếp trong thư mục đầu vào."""
    if input_path.is_file():
        return [input_path] if input_path.suffix.lower() == ".json" else []
    if input_path.is_dir():
        return sorted(input_path.glob("*.json"))
    return []


def _empty_translation_cache(prompt_version: str) -> dict[str, Any]:
    return {
        "schema_version": "2.0",
        "prompt_version": prompt_version,
        "entries": {},
        "legacy_entries": {},
    }


def load_translation_cache(
    cache_path: Path,
    prompt_version: str = DEFAULT_PROMPT_VERSION,
) -> dict[str, Any]:
    """Load cache v2 and migrate the legacy plain mapping without overwriting it."""
    if not cache_path.exists():
        return _empty_translation_cache(prompt_version)
    try:
        data = json.loads(cache_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        LOGGER.warning("Không đọc được translation cache %s: %s. Dùng cache rỗng.", cache_path, exc)
        return _empty_translation_cache(prompt_version)
    if isinstance(data, dict) and data.get("schema_version") == "2.0":
        entries = data.get("entries")
        legacy_entries = data.get("legacy_entries", {})
        if isinstance(entries, dict) and isinstance(legacy_entries, dict):
            data["prompt_version"] = prompt_version
            data["legacy_entries"] = legacy_entries
            return data
        LOGGER.warning("Translation cache v2 %s thiếu entries hợp lệ. Dùng cache rỗng.", cache_path)
        return _empty_translation_cache(prompt_version)
    if isinstance(data, dict) and all(isinstance(key, str) and isinstance(value, str) for key, value in data.items()):
        migrated = _empty_translation_cache(prompt_version)
        migrated["legacy_entries"] = dict(data)
        LOGGER.info("Migrated legacy translation cache in memory: %s", cache_path)
        return migrated
    LOGGER.warning("Translation cache %s không đúng contract. Dùng cache rỗng.", cache_path)
    return _empty_translation_cache(prompt_version)


def save_json(path: Path, data: Any) -> None:
    """Ghi JSON UTF-8 có format và tự tạo thư mục đích."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _output_filename(course: dict[str, Any], source_path: Path) -> str:
    """Tạo tên tệp theo mã học phần, với fallback là tên tệp đầu vào."""
    course_info = course.get("course")
    source = course_info if isinstance(course_info, dict) else course
    for key in ("internal_course_code", "course_code", "course_id"):
        value = source.get(key)
        if isinstance(value, str) and value.strip():
            return f"{value.strip()}.json"
    return source_path.name


def run(
    input_path: Path,
    output_dir: Path,
    cache_path: Path,
    translate_fn: TranslateFunction,
    *,
    prompt_version: str = DEFAULT_PROMPT_VERSION,
) -> tuple[int, int, int]:
    """Dịch batch chung, rồi lưu từng danh sách unit đã dịch theo từng học phần."""
    cache = load_translation_cache(cache_path, prompt_version)
    course_units: list[tuple[Path, dict[str, Any], list[dict[str, str]]]] = []
    all_units: list[dict[str, str]] = []
    processed_courses = 0

    for json_path in _json_files(input_path):
        try:
            course = json.loads(json_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            LOGGER.warning("Bỏ qua JSON không hợp lệ %s: %s", json_path, exc)
            continue
        if not isinstance(course, dict):
            LOGGER.warning("Bỏ qua %s vì course JSON phải là object.", json_path)
            continue
        units = extract_units(course)
        if not units:
            LOGGER.warning("Bỏ qua %s vì không tách được unit có course_id hợp lệ.", json_path)
            continue
        course_units.append((json_path, course, units))
        all_units.extend(units)
        processed_courses += 1

    cache_size_before = len(cache["entries"])
    translated_units = translate_units(
        all_units,
        translate_fn,
        translation_cache=cache,
        prompt_version=prompt_version,
    )

    offset = 0
    for source_path, course, units in course_units:
        # Cắt theo số unit đã tách để mỗi tệp chỉ chứa dữ liệu của đúng một học phần.
        translated_course_units = translated_units[offset : offset + len(units)]
        offset += len(units)
        save_json(output_dir / _output_filename(course, source_path), translated_course_units)

    # Cache là metadata vận hành nên nằm ngoài thư mục output chỉ chứa các unit đã dịch.
    save_json(cache_path, cache)
    return processed_courses, len(translated_units), len(cache["entries"]) - cache_size_before


def main() -> None:
    """Đọc đối số CLI, resolve đường dẫn từ config và in thống kê batch."""
    parser = argparse.ArgumentParser(description="Tách text unit và dịch Việt-Anh bằng Gemini từ course JSON Layer 3.")
    parser.add_argument("input", nargs="?", type=Path, help="Một file JSON hoặc thư mục course JSON.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG, help="Tệp config.yaml của pipeline.")
    parser.add_argument("--output", type=Path, help="Thư mục output; ghi đè translated_units_dir trong config.")
    parser.add_argument("--cache", type=Path, help="Tệp translation cache; mặc định lấy từ config.")
    parser.add_argument("--mock", action="store_true", help="Chỉ dùng để test; không tạo bản dịch tiếng Anh thật.")
    args = parser.parse_args()

    settings = load_settings(args.config)
    paths = settings["paths"]
    input_path = args.input or ROOT_DIR / paths["canonical_dir"]
    output_dir = args.output or ROOT_DIR / paths["translated_units_dir"]
    cache_path = args.cache or ROOT_DIR / paths["translation_cache_dir"] / CACHE_FILENAME
    translate_fn = mock_translate_fn if args.mock else build_gemini_translate_fn(settings["translation"]["model"])

    courses, units, translated = run(
        input_path,
        output_dir,
        cache_path,
        translate_fn,
        prompt_version=str(settings["translation"]["prompt_version"]),
    )
    # Dùng ASCII để CLI vẫn chạy được khi Windows console chưa hỗ trợ UTF-8.
    print(f"Processed courses: {courses}")
    print(f"Total units: {units}")
    print(f"Unique texts translated: {translated}")
    print(f"Saved one translated-unit file per course in: {output_dir}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
    main()
