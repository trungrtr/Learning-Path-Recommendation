"""Structured JSONL logger: {ts, module, level, msg, meta}. Mỗi module ghi
vào file riêng dưới logs/. Gộp luôn hằng số threshold-key/label chung
(trước đây constants.py riêng) vì danh sách rất ngắn."""

import logging
import json
from datetime import datetime
from pathlib import Path

NODE_LABELS = ["ChuongTrinhDaoTao", "NhomHocPhan", "HocPhan", "MucTieuHocPhan",
               "CLO", "Bai", "KyNangESCO", "NgheNghiepESCO"]
EDGE_LABELS = ["CO_HOC_PHAN", "THUOC_NHOM", "CO_CLO", "CO_MUC_TIEU", "CO_BAI",
               "TIEN_QUYET", "HOC_TRUOC", "TEACHES_SKILL", "SUPPORTS_SKILL",
               "REQUIRES_SKILL"]


class JsonlFormatter(logging.Formatter):
    """Định dạng log thành JSON."""
    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "ts": datetime.fromtimestamp(record.created).isoformat(),
            "module": record.name,
            "level": record.levelname,
            "msg": record.getMessage(),
        }
        if hasattr(record, "meta"):
            log_obj["meta"] = record.meta
        return json.dumps(log_obj, ensure_ascii=False)


def get_logger(module_name: str) -> logging.Logger:
    """Trả về logger ghi JSONL vào logs/{module_name}.jsonl. Không dùng
    print() ở bất kỳ module nào (AGENT.md mục 5)."""
    logger = logging.getLogger(module_name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        log_dir = Path("logs")
        log_dir.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_dir / f"{module_name}.jsonl", encoding="utf-8")
        file_handler.setFormatter(JsonlFormatter())
        logger.addHandler(file_handler)
    
    return logger
