"""Bước A: nạp ESCO IT-30 và cache embedding của vocabulary skill đóng."""

from __future__ import annotations

import csv
import hashlib
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from .config import SkillMatchingConfig

LOGGER = logging.getLogger(__name__)
EMBEDDING_CACHE_FILENAME = "esco_it30_embeddings.npy"
METADATA_CACHE_FILENAME = "esco_it30_pool.json"


@dataclass(frozen=True)
class EscoSkill:
    """Thông tin skill ESCO cần cho retrieval, reranking và ghi output."""

    skill_id: str
    skill_uri: str
    skill_label: str
    skill_type: str
    skill_description: str


@dataclass
class SkillPool:
    """Vocabulary ESCO IT-30 và embedding song song với thứ tự danh sách skills."""

    skills: list[EscoSkill]
    embeddings: np.ndarray
    model: Any

    def __post_init__(self) -> None:
        self.by_uri = {skill.skill_uri: skill for skill in self.skills}
        self.index_by_uri = {skill.skill_uri: index for index, skill in enumerate(self.skills)}

    def score_candidates(self, texts: list[str], candidate_uris: list[list[str]], batch_size: int) -> list[dict[str, float]]:
        """Tính cosine score cho mỗi URI ứng viên để lưu evidence retrieval có thể audit."""
        if not texts:
            return []
        query_embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )
        scores: list[dict[str, float]] = []
        for embedding, uris in zip(query_embeddings, candidate_uris):
            scores.append(
                {
                    uri: float(np.dot(embedding, self.embeddings[self.index_by_uri[uri]]))
                    for uri in uris
                    if uri in self.index_by_uri
                }
            )
        return scores


def _source_fingerprint(skills_csv: Path, embedding_model: str) -> str:
    """Fingerprint cache theo bytes CSV và model để không dùng nhầm embedding cũ."""
    digest = hashlib.sha256()
    digest.update(skills_csv.read_bytes())
    digest.update(embedding_model.encode("utf-8"))
    return digest.hexdigest()


def _load_skills(skills_csv: Path) -> list[EscoSkill]:
    """Đọc file ``esco_it_30/skills.csv`` được xuất bởi repo ESCO IT-30."""
    if not skills_csv.exists():
        raise FileNotFoundError(f"Không tìm thấy ESCO IT-30 skills.csv: {skills_csv}")
    with skills_csv.open(encoding="utf-8-sig", newline="") as source:
        rows = csv.DictReader(source)
        skills = [
            EscoSkill(
                skill_id=row["skill_id"],
                skill_uri=row["skill_uri"],
                skill_label=row["skill_label"],
                skill_type=row.get("skill_type") or "",
                skill_description=row.get("skill_description") or "",
            )
            for row in rows
            if row.get("skill_id") and row.get("skill_uri") and row.get("skill_label")
        ]
    if not skills:
        raise ValueError(f"ESCO skills.csv không có skill hợp lệ: {skills_csv}")
    return skills


def _load_embedding_model(config: SkillMatchingConfig) -> Any:
    """Lazy-load SentenceTransformer vì import package không nên tải model lớn."""
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise RuntimeError("Thiếu sentence-transformers để build ESCO skill pool.") from exc
    if not config.embedding_model_dir.exists():
        raise FileNotFoundError(f"Không tìm thấy embedding model nội bộ: {config.embedding_model_dir}")
    return SentenceTransformer(str(config.embedding_model_dir), device=config.device)


def build_skill_pool(config: SkillMatchingConfig) -> SkillPool:
    """Xây hoặc nạp cache embedding cho toàn bộ skill ESCO trong tập 30 nghề."""
    skills = _load_skills(config.esco_skills_csv)
    cache_dir = config.pool_cache_dir
    cache_dir.mkdir(parents=True, exist_ok=True)
    metadata_path = cache_dir / METADATA_CACHE_FILENAME
    embeddings_path = cache_dir / EMBEDDING_CACHE_FILENAME
    fingerprint = _source_fingerprint(config.esco_skills_csv, str(config.embedding_model_dir))
    model = _load_embedding_model(config)

    embeddings: np.ndarray | None = None
    if metadata_path.exists() and embeddings_path.exists():
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            cached = np.load(embeddings_path)
            if metadata.get("fingerprint") == fingerprint and cached.shape[0] == len(skills):
                embeddings = cached
                LOGGER.info("Loaded cached ESCO IT-30 embeddings for %d skills.", len(skills))
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            LOGGER.warning("Không đọc được ESCO embedding cache: %s. Sẽ tạo lại.", exc)

    if embeddings is None:
        corpus = [f"{skill.skill_label} {skill.skill_description}".strip() for skill in skills]
        embeddings = model.encode(
            corpus,
            batch_size=config.embedding_batch_size,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=True,
        )
        np.save(embeddings_path, embeddings)
        metadata_path.write_text(
            json.dumps({"fingerprint": fingerprint, "skill_count": len(skills)}, indent=2),
            encoding="utf-8",
        )
        LOGGER.info("Built ESCO IT-30 embeddings for %d skills.", len(skills))
    return SkillPool(skills=skills, embeddings=embeddings, model=model)
