"""Auto-detect raw CTDT files that are new/changed and re-run CTDT extraction only.

Usage:
    python scripts/detect_and_rerun_ctdt_new.py
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pipeline.m2.m2b_ctdt_extraction import parse_ctdt_markdown
from pipeline.m3.materialize_ctdt import materialize_ctdt_batch
from shared.file_io import read_json, write_json


REPO_ROOT = Path(__file__).resolve().parents[1]
RAW_CTDT_DIR = (REPO_ROOT / "../../data/raw/4_ctdt").resolve()
EXTRACTED_DIR = (REPO_ROOT / "data/2_extracted_json/ctdt").resolve()
CANON_DIR = (REPO_ROOT / "data/8_canonical/ctdt").resolve()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def existing_hash_for(path: Path) -> str | None:
    try:
        data = read_json(path)
    except Exception:
        return None
    if isinstance(data, dict):
        return data.get("_content_hash")
    return None


def detect_new_or_changed_ctdt() -> list[Path]:
    if not RAW_CTDT_DIR.exists():
        raise FileNotFoundError(f"Không tìm thấy thư mục CTDT gốc: {RAW_CTDT_DIR}")

    changed: list[Path] = []
    for raw_file in sorted(RAW_CTDT_DIR.glob("*.md")):
        ma_guess = raw_file.stem
        if "CTDT_" in raw_file.name:
            try:
                ma_guess = raw_file.name.split("CTDT_")[-1].split(".")[0]
            except Exception:
                pass

        out_file = EXTRACTED_DIR / f"CTDT_{ma_guess}.json"
        content = raw_file.read_text(encoding="utf-8")
        content_hash = sha256_text(content)

        if not out_file.exists() or existing_hash_for(out_file) != content_hash:
            changed.append(raw_file)

    return changed


def re_extract_ctdt(raw_file: Path) -> bool:
    text = raw_file.read_text(encoding="utf-8")
    parsed = parse_ctdt_markdown(text, raw_file.name)
    if not parsed:
        print(f"[FAIL] {raw_file.name}: parser không đọc được")
        return False

    out_name = f"CTDT_{parsed.ma_ctdt}.json"
    out_path = EXTRACTED_DIR / out_name
    payload = parsed.model_dump()
    payload["_content_hash"] = sha256_text(text)
    write_json(out_path, payload)

    print(f"[OK] {raw_file.name} -> {out_name} | groups={len(parsed.nhom_hoc_phan)} | courses={sum(len(g.hoc_phan) for g in parsed.nhom_hoc_phan)}")
    return True


def main() -> None:
    EXTRACTED_DIR.mkdir(parents=True, exist_ok=True)
    CANON_DIR.mkdir(parents=True, exist_ok=True)

    pending = detect_new_or_changed_ctdt()
    if not pending:
        print(f"[INFO] Không có CTDT mới hoặc đã thay đổi trong {RAW_CTDT_DIR}")
        return

    print(f"[INFO] Phát hiện {len(pending)} CTDT mới/thay đổi:")
    for p in pending:
        print(f"  - {p.name}")

    for file in pending:
        re_extract_ctdt(file)

    print("[INFO] Rebuild materialized CTDT only...")
    materialize_ctdt_batch()
    print("[INFO] Hoàn tất. Output: ")
    for p in sorted(EXTRACTED_DIR.glob("*.json")):
        print(f"  {p.name}")


if __name__ == "__main__":
    main()
