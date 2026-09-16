"""Pipeline Orchestrator — điều phối Tầng 0 → Tầng 10.

Entry point chính cho teaches-skill pipeline v3 (Layered Architecture).
Chạy end-to-end cho 1 hoặc nhiều học phần.
"""

from __future__ import annotations

import logging
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parents[4] / ".env")

from .configs.pipeline_config import PipelineConfig
from .models.schemas import SkillTeacherRecord, CourseType

# Layer imports
from .layers.layer_00_ingestion import load_single_course, validate_course, discover_and_load_all
from .layers.layer_005_evidence_builder import build_evidence, compute_course_sparse_flag
from .layers.layer_01_extraction import LLMExtractor
from .layers.layer_02_retrieval import RetrievalLayer
from .layers.layer_04_reranking import RerankDecisionLayer
from .layers.layer_05_llm_verification import LLMVerificationLayer
from .layers.layer_06_to_10 import PostProcessingLayer

logger = logging.getLogger(__name__)

class TeachesSkillPipeline:
    """Pipeline chính: Layer 00 → Layer 10 cho teaches-skill v3."""

    def __init__(self, config: PipelineConfig):
        self.config = config

        # Lazy-init components
        self._layer_01: LLMExtractor | None = None
        self._layer_02: RetrievalLayer | None = None
        self._layer_04: RerankDecisionLayer | None = None
        self._layer_05: LLMVerificationLayer | None = None
        self._layer_06: PostProcessingLayer | None = None

    def _init_components(self) -> None:
        """Lazy-init tất cả layers."""
        if self._layer_01 is None:
            self._layer_01 = LLMExtractor(self.config)
        if self._layer_02 is None:
            self._layer_02 = RetrievalLayer(self.config)
        if self._layer_04 is None:
            self._layer_04 = RerankDecisionLayer(self.config)
        if self._layer_05 is None:
            self._layer_05 = LLMVerificationLayer(self.config)
        if self._layer_06 is None:
            self._layer_06 = PostProcessingLayer(self.config)

    def run_course(
        self,
        course_code: str,
        contract_dir: str | Path | None = None,
        course_type: CourseType = "SPECIALIZED",
    ) -> list[SkillTeacherRecord]:
        self._init_components()
        contract = Path(contract_dir or self.config.contract_dir)

        logger.info("=" * 60)
        logger.info("Pipeline START: %s (type=%s)", course_code, course_type)
        logger.info("=" * 60)

        # Layer 00: Ingestion
        try:
            course_data = load_single_course(course_code, contract)
        except Exception as e:
            logger.error("Course %s load failed: %s", course_code, e)
            return []
            
        validation = validate_course(course_data, self.config)
        if not validation.is_valid:
            logger.error("Course %s invalid or blocked: %s", course_code, validation.errors)
            return []
            
        course_title = course_data.hoc_phan.ten_en or course_data.hoc_phan.ten_vi or course_code

        # Layer 005: Evidence Builder
        evidence_units = build_evidence(course_data)
        if not evidence_units:
            logger.warning("Course %s: no evidence — skipping.", course_code)
            return []

        # Layer 01: Extraction
        mentions = self._layer_01.run(evidence_units)
        direct_candidates = []
        
        # Layer 02+03: Retrieval (BM25 + FAISS + RRF)
        fused_candidates = self._layer_02.run(mentions, direct_candidates)
        if not fused_candidates:
            logger.warning("Course %s: no candidates after retrieval.", course_code)
            return []

        # Layer 04: Reranking & Decision
        accepted, rejected = self._layer_04.run(fused_candidates, course_code, course_title, evidence_units, course_type)

        # Layer 05: LLM Verification
        accepted = self._layer_05.run(accepted, course_title, evidence_units)

        # Layer 06-10: Post-Processing & Export
        valid_records = self._layer_06.run(accepted, course_code, course_title, course_type, evidence_units, mentions)

        logger.info(
            "Pipeline DONE: %s — %d records (%d skill, %d knowledge)",
            course_code,
            len(valid_records),
            sum(1 for r in valid_records if r.relation_type == "TEACHES_SKILL"),
            sum(1 for r in valid_records if r.relation_type == "TEACHES_KNOWLEDGE"),
        )
        return valid_records

    def run_all(
        self,
        contract_dir: str | Path | None = None,
        course_type: CourseType = "SPECIALIZED",
    ) -> dict[str, list[SkillTeacherRecord]]:
        contract = Path(contract_dir or self.config.contract_dir)
        courses = discover_and_load_all(contract)
        
        self._init_components()

        results: dict[str, list[SkillTeacherRecord]] = {}
        for course in courses:
            course_code = course.ma_hoc_phan
            try:
                records = self.run_course(
                    course_code=course_code,
                    contract_dir=contract,
                    course_type=course_type,
                )
                results[course_code] = records
            except Exception:
                logger.exception("Pipeline failed for %s", course_code)
                results[course_code] = []

        logger.info(
            "Pipeline completed: %d courses, %d total records",
            len(results),
            sum(len(r) for r in results.values()),
        )
        return results

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    config = PipelineConfig()
    pipeline = TeachesSkillPipeline(config)
    pipeline.run_all()
