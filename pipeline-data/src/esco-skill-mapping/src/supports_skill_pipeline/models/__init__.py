"""Models — data classes cho supports_skill_pipeline."""

from .candidate import SupportCandidate, FusedCandidate, ScoredCandidate
from .record import SupportSkillRecord, EvidenceRef

__all__ = [
    "SupportCandidate",
    "FusedCandidate",
    "ScoredCandidate",
    "SupportSkillRecord",
    "EvidenceRef",
]
