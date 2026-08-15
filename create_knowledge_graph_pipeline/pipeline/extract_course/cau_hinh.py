"""Đọc cấu hình và xác định đường dẫn cho bước trích xuất."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = ROOT_DIR / "config.yaml"

# Nạp một lần ở biên hệ thống để mọi module pipeline dùng chung biến môi trường.
# ``override=False`` bảo đảm giá trị do hệ điều hành/CI truyền vào luôn được ưu tiên.
load_dotenv(ROOT_DIR / ".env", override=False)


def load_settings(config_path: Path) -> dict[str, Any]:
    """Đọc toàn bộ cấu hình YAML."""
    return yaml.safe_load(config_path.read_text(encoding="utf-8"))


def load_course_keys(path: Path | None) -> dict[str, str]:
    """Đọc map filename -> crawl_course_key nếu người dùng cung cấp."""
    if path is None:
        return {}
    loaded = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict) or not all(
        isinstance(key, str) and isinstance(value, str)
        for key, value in loaded.items()
    ):
        raise ValueError("course-key-map phải có dạng {\"filename.md\": \"course_key\"}.")
    return loaded


def infer_course_key(markdown_path: Path, course_keys: dict[str, str]) -> str:
    """Lấy khóa từ map; fallback theo tên file và bỏ hậu tố bản sao ``(n)``."""
    if markdown_path.name in course_keys:
        return course_keys[markdown_path.name]
    return re.sub(r"\s*\(\d+\)$", "", markdown_path.stem).strip().upper()


def extraction_settings(settings: dict[str, Any]) -> dict[str, Any]:
    """Lấy config trích xuất và áp dụng override không bí mật từ ``.env``."""
    result = dict(settings["extraction_llm"])
    if model_id := os.getenv("EXTRACTOR_MODEL"):
        result["extractor_model"] = model_id
    return result


def extraction_validation_settings(settings: dict[str, Any]) -> dict[str, Any]:
    """Return deterministic Layer 1 validation settings with safe defaults."""
    configured = settings.get("extraction_validation") or {}
    return {
        "enabled": bool(configured.get("enabled", True)),
        "report_ambiguous": bool(configured.get("report_ambiguous", True)),
    }
