"""Liên kết text unit đã dịch với skill ESCO IT-30 qua retrieval và UniSkill reranking."""

from .aggregate import aggregate_by_course

__all__ = ["aggregate_by_course", "run_skill_matching"]


def __getattr__(name: str):
    """Lazy-export orchestrator để ``python -m pipeline.skill_matching.pipeline`` không import hai lần."""
    if name == "run_skill_matching":
        from .pipeline import run_skill_matching

        return run_skill_matching
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
