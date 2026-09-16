"""Module xử lý I/O: đọc ghi file và mã băm. Đảm bảo Idempotency."""

import json
import yaml
import hashlib
from pathlib import Path
from typing import Any


def read_yaml_config(path: str | Path) -> dict[str, Any]:
    """Đọc file YAML config."""
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def read_json(path: str | Path) -> dict[str, Any] | list[Any]:
    """Đọc file JSON."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: str | Path, data: dict[str, Any] | list[Any]) -> None:
    """Ghi dữ liệu ra file JSON, format dễ đọc."""
    path_obj = Path(path)
    path_obj.parent.mkdir(parents=True, exist_ok=True)
    with open(path_obj, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def append_jsonl(path: str | Path, data: dict[str, Any]) -> None:
    """Ghi thêm một dòng JSON vào file JSONL."""
    path_obj = Path(path)
    path_obj.parent.mkdir(parents=True, exist_ok=True)
    with open(path_obj, "a", encoding="utf-8") as f:
        f.write(json.dumps(data, ensure_ascii=False) + "\n")


def get_content_hash(content: str | dict[str, Any] | list) -> str:
    """Tạo mã MD5 hash để kiểm tra thay đổi nội dung (Idempotent)."""
    if not isinstance(content, str):
        content = json.dumps(content, sort_keys=True, ensure_ascii=False)
    return hashlib.md5(content.encode("utf-8")).hexdigest()
