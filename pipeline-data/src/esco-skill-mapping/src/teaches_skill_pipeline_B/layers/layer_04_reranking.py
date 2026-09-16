"""Layer 04 — Reranking & Decision.

Áp dụng mô hình Cross-encoder để rerank các FusedCandidate từ Layer 02.
Sau đó áp dụng các ngưỡng Threshold (từ Layer 05 cũ) để phân loại quyết định (ACCEPT/REVIEW/REJECT).
Bao gồm các cơ chế Guardrails chống False Positive.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from statistics import mean
from typing import Any

from ..models.schemas import FusedCandidate, SkillTeacherRecord
from ..models.schemas import TierLevel, ConfidenceLevel, ConceptType, CourseType, DecisionStatus

logger = logging.getLogger(__name__)

# ==============================================================================
# Reranker (Từ Tầng 4 cũ)
# ==============================================================================

class CrossEncoderReranker:
    """UniSkill-compatible cross-encoder reranker."""

    def __init__(self, config: Any):
        self._config = getattr(config, "rerank", None)
        if not self._config:
            # Fallback config if not provided
            class DummyConfig:
                model = "cross-encoder/ms-marco-MiniLM-L6-v2"
                rerank_top_k = 50
                rerank_weight = 0.5
                rrf_weight = 0.5
            self._config = DummyConfig()
            
        self._model: Any = None
        self._tokenizer: Any = None

    def _load(self) -> None:
        if self._model is not None:
            return

        from transformers import AutoModelForSequenceClassification, AutoTokenizer

        logger.info("Loading cross-encoder: %s", self._config.model)
        self._tokenizer = AutoTokenizer.from_pretrained(self._config.model)
        self._model = AutoModelForSequenceClassification.from_pretrained(self._config.model)
        self._model.eval()
        logger.info("Cross-encoder loaded.")

    def rerank(self, candidates: list[FusedCandidate], course_title: str) -> list[FusedCandidate]:
        if not candidates:
            return []

        rerank_slice = candidates[: self._config.rerank_top_k]
        rest = candidates[self._config.rerank_top_k:]

        self._load()

        pairs: list[tuple[str, str]] = []
        for cand in rerank_slice:
            if cand.mention_texts:
                mention_str = cand.mention_texts[0]
                context_str = f"{course_title}. {mention_str}".strip()
            else:
                source_text = cand.source_texts[0] if cand.source_texts else ""
                context_str = f"{course_title}. {source_text}".strip()
                
            candidate_str = f"{cand.skill_label}. {cand.skill_description}".strip()
            pairs.append((context_str, candidate_str))

        scores = self._score_batch(pairs)

        for cand, score in zip(rerank_slice, scores):
            cand.score_rerank = score
            if score is not None:
                cand.combined_score = (
                    self._config.rerank_weight * score
                    + self._config.rrf_weight * cand.score_rrf
                )
            else:
                cand.combined_score = cand.score_rrf

        for cand in rest:
            cand.combined_score = cand.score_rrf

        all_candidates = rerank_slice + rest
        all_candidates.sort(key=lambda c: c.combined_score, reverse=True)

        logger.info("Reranked %d candidates", len(all_candidates))
        return all_candidates

    def _score_batch(self, pairs: list[tuple[str, str]]) -> list[float | None]:
        if not pairs:
            return []

        import torch

        scores: list[float | None] = []
        for text_a, text_b in pairs:
            try:
                encoded = self._tokenizer(
                    text_a, text_b,
                    return_tensors="pt",
                    truncation=True,
                    max_length=512,
                )
                with torch.no_grad():
                    logits = self._model(**encoded).logits

                if logits.shape[-1] == 1:
                    value = float(torch.sigmoid(logits[0, 0]).item())
                else:
                    value = float(torch.softmax(logits, dim=-1)[0, -1].item())
                scores.append(value)
            except Exception:
                logger.exception("Reranker scoring failed for 1 input")
                scores.append(None)

        return scores


# ==============================================================================
# Threshold & Guardrails (Từ Tầng 5 cũ)
# ==============================================================================

@dataclass
class TieredCandidate:
    candidate: FusedCandidate
    tier: TierLevel
    confidence_level: ConfidenceLevel
    decision: DecisionStatus
    reject_reason: str | None = None
    over_soft_cap: bool = False
    llm_reasoning: str | None = None

DOMAIN_BLOCKED_URIS: set[str] = {
    "http://data.europa.eu/esco/skill/e8f80ec5-c423-4eb2-9f0f-805d22f844ae",
    "http://data.europa.eu/esco/skill/118efbcd-8fc5-4668-81d1-c383a0d16070",
    "http://data.europa.eu/esco/skill/a3ce2bf7-5562-4639-9b52-fdb4850a3904",
    "http://data.europa.eu/esco/skill/946c1229-1171-40d4-82cc-fe3f483ca100",
    "http://data.europa.eu/esco/skill/114c9698-c999-4369-8498-81bf641fe871",
    "http://data.europa.eu/esco/skill/f2c63b7a-ed6c-4890-9f8c-7685d172624c",
    "http://data.europa.eu/esco/skill/ccdbd9bb-4faf-403c-a968-e8bf487f8a53",
}

DOMAIN_BLOCK_KEYWORD_GROUPS: list[list[str]] = [
    ["accident", "occupational safety", "workplace injury"],
    ["patient", "nursing", "clinical", "medical treatment"],
    ["livestock", "agricultural", "crop", "harvest"],
]

def is_domain_blocked_by_uri(esco_uri: str, blocked_uris: set[str] | list[str] | None = None) -> bool:
    uris = set(blocked_uris) if blocked_uris is not None else DOMAIN_BLOCKED_URIS
    return esco_uri in uris

def is_domain_blocked_by_keyword(esco_concept: dict[str, Any], course_evidence: list[Any]) -> bool:
    concept_text = (esco_concept.get("preferred_label", "") + " " + " ".join(esco_concept.get("alt_labels", []))).lower()
    for keyword_group in DOMAIN_BLOCK_KEYWORD_GROUPS:
        concept_has_keywords = any(k in concept_text for k in keyword_group)
        if not concept_has_keywords:
            continue
        course_has_signal = any(
            any(k in getattr(e, "text", "").lower() for k in keyword_group)
            for e in course_evidence
            if getattr(e, "source_type", "") in ("CLO", "BAI_HOC") and not getattr(e, "is_boilerplate", False)
        )
        if not course_has_signal:
            return True
    return False

OFFENSIVE_SECURITY_URIS: set[str] = {
    "http://data.europa.eu/esco/skill/af313ba1-a39e-49ac-99ec-94630fbe4f7f",
}

OFFENSIVE_SECURITY_KEYWORDS: list[str] = [
    "exploit", "penetration test", "intrusion", "malware",
    "reverse engineer", "vulnerability exploit", "ethical hack",
]

def is_security_drift(esco_uri: str, concept_label: str, course_evidence: list[Any]) -> bool:
    if esco_uri not in OFFENSIVE_SECURITY_URIS:
        label_lower = concept_label.lower()
        if not any(k in label_lower for k in OFFENSIVE_SECURITY_KEYWORDS):
            return False
    explicit_offensive_evidence = [
        e for e in course_evidence
        if any(k in getattr(e, "text", "").lower() for k in OFFENSIVE_SECURITY_KEYWORDS)
        and getattr(e, "source_type", "") in ("CLO", "BAI_HOC")
        and getattr(e, "meta", {}).get("content_richness") != "title_only"
        and not getattr(e, "is_boilerplate", False)
    ]
    return len(explicit_offensive_evidence) == 0

IT_GOVERNANCE_FRAMEWORKS: dict[str, list[str]] = {
    "control objectives for information and related technology": ["cobit"],
    "information technology infrastructure library":            ["itil"],
    "iso/iec 27001":                                            ["iso 27001", "iso27001", "isms"],
    "information security management system":                    ["isms", "iso 27001", "iso27001"],
    "the open group architecture framework":                    ["togaf"],
    "capability maturity model integration":                    ["cmmi"],
    "project management body of knowledge":                     ["pmbok"],
    "prince2":                                                  ["prince2"],
}

def requires_explicit_framework_evidence(concept_label: str, course_evidence: list[Any]) -> bool:
    label_lower = concept_label.lower()
    for framework_label, aliases in IT_GOVERNANCE_FRAMEWORKS.items():
        if framework_label not in label_lower and not any(a in label_lower for a in aliases):
            continue
        explicit_mentions = [
            e for e in course_evidence
            if any(a in getattr(e, "text", "").lower() for a in aliases + [framework_label])
            and getattr(e, "source_type", "") in ("CLO", "BAI_HOC")
            and not getattr(e, "is_boilerplate", False)
        ]
        return len(explicit_mentions) == 0
    return False

def is_capstone_course(course_code: str, course_title: str, config: Any = None) -> bool:
    if config is not None:
        cfg = getattr(config, "capstone_courses", None)
        if isinstance(cfg, dict):
            if not cfg.get("enabled", True):
                return False
            if course_code in cfg.get("course_codes", []):
                return True
            title_lower = course_title.lower()
            return any(k in title_lower for k in cfg.get("detection_keywords", []))
        elif hasattr(cfg, "enabled"):
            if not cfg.enabled:
                return False
            if course_code in cfg.course_codes:
                return True
            title_lower = course_title.lower()
            return any(k in title_lower for k in cfg.detection_keywords)

    capstone_codes = {"IT6205", "IT6206", "IT6207", "IT6208"}
    if course_code in capstone_codes:
        return True
    title_lower = course_title.lower()
    capstone_keywords = ["internship", "graduation thesis", "graduation project", "final project"]
    return any(k in title_lower for k in capstone_keywords)

def route_to_tiers(
    candidates: list[FusedCandidate],
    concept_type: ConceptType,
    course_type: CourseType,
    threshold_config: Any,
    hard_cap_config: Any,
    course_code: str = "",
    course_title: str = "",
    evidence_units: list[Any] | None = None,
    is_sparse_course: bool = False,
    config: Any = None,
) -> tuple[list[TieredCandidate], list[TieredCandidate]]:
    accepted: list[TieredCandidate] = []
    rejected: list[TieredCandidate] = []
    evidence = evidence_units or []
    eu_lookup = {getattr(eu, "evidence_id", ""): eu for eu in evidence}

    base_thresholds = _get_thresholds(concept_type, threshold_config)
    is_capstone = is_capstone_course(course_code, course_title, config)
    base_hard_cap = _get_hard_cap(course_type, concept_type, hard_cap_config)
    effective_hard_cap = base_hard_cap
    if is_capstone:
        effective_hard_cap = 20
        if config is not None and hasattr(config, "capstone_courses"):
            effective_hard_cap = getattr(config.capstone_courses, "hard_cap_override", 20)

    if is_capstone:
        capstone_th = 0.740
        if config is not None and hasattr(config, "capstone_courses"):
            capstone_th = getattr(config.capstone_courses, "confidence_threshold_override", 0.740)
        thresholds = {
            "primary": capstone_th,
            "secondary": capstone_th,
            "optional": capstone_th,
            "overflow": capstone_th,
        }
    else:
        thresholds = dict(base_thresholds)

    qualified: list[tuple[TieredCandidate, float]] = []

    for cand in candidates:
        cand_evidence = [eu_lookup[eid] for eid in cand.evidence_ids if eid in eu_lookup]
        
        if cand_evidence:
            avg_weight = mean([getattr(e, "evidence_weight", 0.30) for e in cand_evidence])
        else:
            avg_weight = 0.30
        if avg_weight < 0.35:
            cand.low_evidence_quality = True

        mismatch_flagged = getattr(cand, "mismatch_flagged", False)
        esco_type_agrees = getattr(cand, "esco_type_agrees", True)
        agreement = getattr(cand, "retrieval_agreement", "PARTIAL")

        blocked_uris = None
        if config is not None and hasattr(config, "domain_filter"):
            blocked_uris = config.domain_filter.blocked_uris
        if is_domain_blocked_by_uri(cand.skill_uri, blocked_uris):
            rejected.append(TieredCandidate(candidate=cand, tier="low_confidence", confidence_level="LOW", decision="REJECT", reject_reason="DOMAIN_BLOCK"))
            continue

        if is_domain_blocked_by_keyword({"preferred_label": cand.skill_label}, evidence):
            rejected.append(TieredCandidate(candidate=cand, tier="low_confidence", confidence_level="LOW", decision="REJECT", reject_reason="DOMAIN_BLOCK"))
            continue

        if is_security_drift(cand.skill_uri, cand.skill_label, evidence):
            rejected.append(TieredCandidate(candidate=cand, tier="low_confidence", confidence_level="LOW", decision="REJECT", reject_reason="SECURITY_DRIFT"))
            continue

        if requires_explicit_framework_evidence(cand.skill_label, evidence):
            rejected.append(TieredCandidate(candidate=cand, tier="low_confidence", confidence_level="LOW", decision="REJECT", reject_reason="FRAMEWORK_WITHOUT_EXPLICIT_TEACHING"))
            continue

        if is_capstone:
            min_weight = 0.40
            if config is not None and hasattr(config, "capstone_courses"):
                min_weight = getattr(config.capstone_courses, "require_min_avg_evidence_weight", 0.40)
            if avg_weight < min_weight:
                rejected.append(TieredCandidate(candidate=cand, tier="low_confidence", confidence_level="LOW", decision="REJECT", reject_reason="CAPSTONE_LOW_EVIDENCE_WEIGHT"))
                continue

            reject_if_sparse_and_mismatch = True
            if config is not None and hasattr(config, "capstone_courses"):
                reject_if_sparse_and_mismatch = getattr(config.capstone_courses, "reject_if_sparse_and_mismatch", True)
            if is_sparse_course and mismatch_flagged and reject_if_sparse_and_mismatch:
                rejected.append(TieredCandidate(candidate=cand, tier="low_confidence", confidence_level="LOW", decision="REJECT", reject_reason="CAPSTONE_SPARSE_MISMATCH"))
                continue

        score = cand.score_rerank if cand.score_rerank is not None else cand.combined_score
        penalty_val = 0.025
        if config is not None and hasattr(config, "mismatch_penalty"):
            penalty_val = getattr(config.mismatch_penalty, "penalty_value", 0.025)

        if mismatch_flagged:
            score -= penalty_val
            cand.combined_score = max(0.0, cand.combined_score - penalty_val)
            cand.mismatch_penalty_applied = True

        if mismatch_flagged and (not esco_type_agrees) and getattr(cand, "low_evidence_quality", False):
            rejected.append(TieredCandidate(candidate=cand, tier="low_confidence", confidence_level="LOW", decision="REJECT", reject_reason="TRIPLE_FAIL_MISMATCH"))
            continue

        if agreement == "WEAK":
            if mismatch_flagged:
                rejected.append(TieredCandidate(candidate=cand, tier="low_confidence", confidence_level="LOW", decision="REJECT", reject_reason="WEAK_RETRIEVAL_MISMATCH"))
                continue
            if is_capstone:
                rejected.append(TieredCandidate(candidate=cand, tier="low_confidence", confidence_level="LOW", decision="REJECT", reject_reason="WEAK_RETRIEVAL_CAPSTONE"))
                continue

        cand_thresholds = dict(thresholds)
        if agreement == "STRONG":
            cand_thresholds = {k: v - 0.010 for k, v in thresholds.items()}

        tier, confidence, decision = _assign_tier(score, cand_thresholds)

        if decision == "REJECT":
            rejected.append(TieredCandidate(candidate=cand, tier="low_confidence", confidence_level="LOW", decision="REJECT", reject_reason="below_overflow_threshold"))
            continue

        mismatch = _check_mismatch(cand, cand_thresholds)
        if mismatch and tier == "PRIMARY":
            tier = "SECONDARY"
            confidence = "MED"
            decision = "REJECT"

        best_retriever_rank = min(cand.bm25_rank or 999, cand.dense_rank or 999)
        rank_bonus = 0.015 if best_retriever_rank == 1 else (0.010 if best_retriever_rank == 2 else 0.0)
        priority_score = cand.combined_score + rank_bonus

        tc = TieredCandidate(candidate=cand, tier=tier, confidence_level=confidence, decision=decision)
        qualified.append((tc, priority_score))

    qualified.sort(key=lambda item: item[1], reverse=True)

    design_cluster_count = 0
    legal_cluster_count = 0

    for tc, _ in qualified:
        lbl = tc.candidate.skill_label.lower()
        if is_capstone:
            if "design" in lbl:
                if design_cluster_count >= 3:
                    tc.decision = "REJECT"
                    tc.reject_reason = f"exceeds_hard_cap_{effective_hard_cap}"
                    rejected.append(tc)
                    continue
                design_cluster_count += 1
            elif "legal" in lbl or "compliance" in lbl or "regulation" in lbl:
                if legal_cluster_count >= 2:
                    tc.decision = "REJECT"
                    tc.reject_reason = f"exceeds_hard_cap_{effective_hard_cap}"
                    rejected.append(tc)
                    continue
                legal_cluster_count += 1

        if len(accepted) < effective_hard_cap:
            accepted.append(tc)
        else:
            tc.decision = "REJECT"
            tc.reject_reason = f"exceeds_hard_cap_{effective_hard_cap}"
            rejected.append(tc)

    return accepted, rejected

def _get_thresholds(concept_type: ConceptType, config: Any) -> dict[str, float]:
    if concept_type == "knowledge":
        return {
            "primary": getattr(config, "knowledge_primary", 0.8),
            "secondary": getattr(config, "knowledge_secondary", 0.7),
            "optional": getattr(config, "knowledge_optional", 0.6),
            "overflow": getattr(config, "knowledge_overflow", 0.5),
        }
    return {
        "primary": getattr(config, "skill_primary", 0.8),
        "secondary": getattr(config, "skill_secondary", 0.7),
        "optional": getattr(config, "skill_optional", 0.6),
        "overflow": getattr(config, "skill_overflow", 0.5),
    }

def _get_hard_cap(course_type: CourseType, concept_type: ConceptType, config: Any) -> int:
    key = f"{course_type.lower()}_{concept_type}"
    return getattr(config, key, 15)

def _assign_tier(score: float, thresholds: dict[str, float]) -> tuple[TierLevel, ConfidenceLevel, DecisionStatus]:
    if score >= thresholds["primary"]:
        return "PRIMARY", "HIGH", "ACCEPT"
    elif score >= thresholds["secondary"]:
        return "SECONDARY", "MED", "ACCEPT"
    elif score >= thresholds["optional"]:
        return "OPTIONAL", "LOW", "REJECT"
    elif score >= thresholds["overflow"]:
        return "OPTIONAL", "LOW", "REJECT"
    else:
        return "low_confidence", "LOW", "REJECT"

def _check_mismatch(cand: FusedCandidate, thresholds: dict[str, float]) -> bool:
    if cand.score_rerank is None:
        return False
    if cand.score_rerank >= thresholds["primary"] and cand.score_rrf < 0.005:
        return True
    return False

# ==============================================================================
# Rerank & Decision Layer Wrapper
# ==============================================================================
class RerankDecisionLayer:
    """Gộp Reranking và Quyết định vào chung một layer."""

    def __init__(self, config: Any):
        self.config = config
        self.reranker = CrossEncoderReranker(config)

    def run(self, candidates: list[FusedCandidate], course_code: str, course_title: str, evidence_units: list[Any], course_type: CourseType = "CORE") -> tuple[list[TieredCandidate], list[TieredCandidate]]:
        logger.info("Layer 04 (Rerank & Decision): Processing %d candidates for %s", len(candidates), course_code)
        
        # 1. Rerank
        reranked = self.reranker.rerank(candidates, course_title)
        
        # 2. Decision Thresholding (sử dụng logic route_to_tiers)
        threshold_config = getattr(self.config, "threshold", None)
        hard_cap_config = getattr(self.config, "hard_cap", None)
        
        # Để đơn giản hóa trong module mới, ta giả sử mọi ứng viên đang xét ở đây được route_to_tiers xử lý chung
        # Tuỳ thuộc pipeline, có thể tách skill và knowledge. Ở đây ta merge tạm hoặc chạy 2 lần.
        # Ta sẽ chạy cho toàn bộ candidates, trong bài toán thực tế sẽ chia 2 mảng skill và knowledge.
        
        skill_cands = [c for c in reranked if c.concept_type == "skill"]
        know_cands = [c for c in reranked if c.concept_type == "knowledge"]
        
        acc_skills, rej_skills = route_to_tiers(
            skill_cands, "skill", course_type, threshold_config, hard_cap_config, 
            course_code, course_title, evidence_units, False, self.config
        )
        
        acc_know, rej_know = route_to_tiers(
            know_cands, "knowledge", course_type, threshold_config, hard_cap_config, 
            course_code, course_title, evidence_units, False, self.config
        )
        
        return acc_skills + acc_know, rej_skills + rej_know
