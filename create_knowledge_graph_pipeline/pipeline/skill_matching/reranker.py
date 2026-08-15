"""Bước C: UniSkill_Bert chấm điểm cặp text unit–skill ESCO và lọc ứng viên."""

from __future__ import annotations

import logging
from typing import Any

from .config import SkillMatchingConfig

LOGGER = logging.getLogger(__name__)


class UniSkillReranker:
    """Lazy adapter cho local ``BertForSequenceClassification`` UniSkill_Bert."""

    def __init__(self, config: SkillMatchingConfig) -> None:
        self.config = config
        self._tokenizer: Any | None = None
        self._model: Any | None = None
        self._torch: Any | None = None

    def _load(self) -> None:
        """Nạp tokenizer/model một lần để xử lý cả batch course trong một run."""
        if self._model is not None:
            return
        model_dir = self.config.uniskill_model_dir
        if not model_dir.exists():
            if not self.config.allow_seed_model_fallback or not self.config.uniskill_seed_dir.exists():
                raise FileNotFoundError(f"Không tìm thấy local UniSkill IT-30: {self.config.uniskill_model_dir}")
            # Fallback giữ pipeline hoạt động nội bộ trong khi checkpoint IT-30 đang được fine-tune.
            model_dir = self.config.uniskill_seed_dir
            LOGGER.warning("Checkpoint UniSkill IT-30 chưa có; dùng seed checkpoint nội bộ: %s", model_dir)
        try:
            import torch
            from transformers import AutoModelForSequenceClassification, AutoTokenizer
        except ImportError as exc:
            raise RuntimeError("Thiếu torch hoặc transformers để chạy UniSkill_Bert.") from exc
        device = self.config.device or ("cuda" if torch.cuda.is_available() else "cpu")
        self._torch = torch
        self._tokenizer = AutoTokenizer.from_pretrained(model_dir)
        self._model = AutoModelForSequenceClassification.from_pretrained(model_dir)
        self._model.to(device)
        self._model.eval()
        self._device = device
        if not 0 <= self.config.positive_label_id < self._model.config.num_labels:
            raise ValueError("positive_label_id không hợp lệ với số label của UniSkill_Bert.")

    def rerank(self, candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Chấm điểm tất cả ứng viên theo batch và chỉ trả về các cặp vượt rerank threshold."""
        if not candidates:
            return []
        self._load()
        accepted: list[dict[str, Any]] = []
        for start in range(0, len(candidates), self.config.rerank_batch_size):
            batch = candidates[start : start + self.config.rerank_batch_size]
            encoded = self._tokenizer(
                [candidate["retrieval_text_en"] for candidate in batch],
                [candidate["skill_label"] for candidate in batch],
                padding=True,
                truncation=True,
                max_length=self.config.max_length,
                return_tensors="pt",
            )
            encoded = {key: value.to(self._device) for key, value in encoded.items()}
            with self._torch.no_grad():
                logits = self._model(**encoded).logits
                probabilities = self._torch.softmax(logits, dim=-1)[:, self.config.positive_label_id]
            for candidate, probability in zip(batch, probabilities.tolist()):
                if probability >= self.config.rerank_threshold:
                    scored = dict(candidate)
                    scored["rerank_score"] = float(probability)
                    accepted.append(scored)
        return accepted
