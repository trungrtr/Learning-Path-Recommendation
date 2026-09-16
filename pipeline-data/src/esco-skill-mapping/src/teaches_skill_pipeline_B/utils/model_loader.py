"""Model Loader.

Cung cấp các hàm tải mô hình dùng chung (FAISS, SentenceTransformer, CrossEncoder) 
để tối ưu bộ nhớ nếu chạy pipeline song song.
Các class Layer hiện tại đã tự quản lý lazy-loading trong _load().
File này được giữ lại cho khả năng mở rộng sau này.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

class ModelCache:
    """Cache models in memory to avoid reloading during batch processing."""
    
    _models: dict[str, Any] = {}
    
    @classmethod
    def get_model(cls, model_name: str, loader_func: Any) -> Any:
        if model_name not in cls._models:
            logger.info("Loading model into cache: %s", model_name)
            cls._models[model_name] = loader_func()
        return cls._models[model_name]
