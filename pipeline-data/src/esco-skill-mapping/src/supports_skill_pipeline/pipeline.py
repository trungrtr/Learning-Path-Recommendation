"""Pipeline Orchestrator — điều phối Bước 1 → Bước 7.

Entry point chính cho supports-skill pipeline M5.
Chạy end-to-end cho 1 hoặc nhiều học phần.

Luồng:
    S1 (Preprocessing)        → Build course context
    S2 (Concept Extraction)   → LLM trích xuất support concepts
    S3 (Retrieval)             → BM25 ∥ FAISS ∥ ESCOXLM-R
    S4 (RRF Fusion)            → Hợp nhất 3 kênh
    S5 (Multi-signal Ranking)  → α·RRF + β·ESCOXLMR + γ·Evidence
    S6 (Human Review)          → Export CSV/JSON cho reviewer
    S7 (Export)                → JSON output + Cypher/Neo4j

Ràng buộc cứng (từ spec):
    - LLM chỉ trích concept thô, không gán nhãn SUPPORTS_SKILL
    - Không tự động convert score thành relation (phải qua Human Review)
    - Pipeline độc lập với M4 (TEACHES_SKILL)
    - Mọi candidate phải thuộc Filtered ESCO Pool
"""

from __future__ import annotations

import logging
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parents[4] / ".env")

from .configs.pipeline_config import PipelineConfig
from .models.record import SupportSkillRecord, EvidenceRef

# Step imports
from .s1_preprocessing import build_course_context
from .s2_concept_extraction import extract_support_concepts
from .s3_retrieval import bm25_search, faiss_search, escoxlmr_search
from .s4_fusion import rrf_fusion
from .s5_ranking import rank_candidates
from .s6_review import export_for_review, import_review_results
from .s7_export import write_records, write_summary, generate_cypher, write_cypher_file
from .s55_llm_verification import verify_support_candidates
from .s65_concept_tag_builder import build_concept_tags

logger = logging.getLogger(__name__)


import asyncio

class SupportsSkillPipeline:
    """Pipeline chính: Bước 1 → Bước 7 cho supports-skill M5."""

    def __init__(self, config: PipelineConfig):
        self.config = config
        self._output_dir = Path(config.output.output_dir)

    async def run_course(
        self,
        course_code: str,
        contract_dir: str | Path | None = None,
    ) -> None:
        """Chạy pipeline Bước 1→5, export cho Human Review (Bước 6).

        Bước 7 (Neo4j) chỉ chạy SAU KHI có kết quả review (finalize_course).

        Args:
            course_code: Mã học phần.
            contract_dir: Thư mục chứa data contract.
        """
        contract = Path(contract_dir or self.config.contract_dir)

        logger.info("=" * 60)
        logger.info("M5 Pipeline START: %s", course_code)
        logger.info("=" * 60)

        # === Bước 1: Preprocessing ===
        logger.info("Bước 1: Building course context...")
        course_name, course_context = build_course_context(course_code, contract)

        if not course_context.strip():
            logger.error("Course %s: empty context — aborting.", course_code)
            return

        # Course Filter
        if self.config.course_filter and self.config.course_filter.enabled:
            ten_vi = course_name.lower()
            for kw in self.config.course_filter.ignored_keywords:
                if kw in ten_vi:
                    logger.warning("Course %s bị loại bỏ do chứa từ khóa cấm: '%s'", course_code, kw)
                    return

        # === Bước 2: LLM Support-Concept Extraction ===
        logger.info("Bước 2: Extracting support concepts via LLM...")
        support_concepts = await extract_support_concepts(course_context, self.config.llm)

        if not support_concepts:
            logger.warning("Course %s: no support concepts extracted — aborting.", course_code)
            return

        logger.info("  → %d concepts: %s", len(support_concepts), support_concepts)

        # === Bước 3: Candidate Retrieval (3 kênh song song) ===
        logger.info("Bước 3: Retrieving candidates (BM25 ∥ FAISS ∥ ESCOXLM-R)...")

        retrieval_cfg = self.config.retrieval
        top_k = retrieval_cfg.top_k_per_channel

        bm25_results = bm25_search(
            concepts=support_concepts,
            bm25_index_path=retrieval_cfg.bm25_index_path,
            metadata_path=retrieval_cfg.faiss_metadata_path,
            top_k=top_k,
        )

        faiss_results = faiss_search(
            concepts=support_concepts,
            course_context=course_context,
            faiss_index_path=retrieval_cfg.faiss_index_path,
            metadata_path=retrieval_cfg.faiss_metadata_path,
            embedding_model=retrieval_cfg.embedding_model,
            top_k=top_k,
        )

        escoxlmr_results = escoxlmr_search(
            concepts=support_concepts,
            course_context=course_context,
            metadata_path=retrieval_cfg.faiss_metadata_path,
            model_name=retrieval_cfg.escoxlmr_model,
            top_k=top_k,
        )

        logger.info(
            "  → BM25: %d, FAISS: %d, ESCOXLMR: %d",
            len(bm25_results), len(faiss_results), len(escoxlmr_results),
        )

        # === Bước 4: RRF Fusion ===
        logger.info("Bước 4: RRF Fusion...")
        fused_candidates = rrf_fusion(
            bm25_results=bm25_results,
            faiss_results=faiss_results,
            escoxlmr_results=escoxlmr_results,
            k=self.config.fusion.rrf_k,
            top_n=self.config.fusion.top_n,
        )

        if not fused_candidates:
            logger.warning("Course %s: no candidates after fusion — aborting.", course_code)
            return

        # === Bước 5: Multi-signal Ranking ===
        logger.info("Bước 5: Multi-signal Ranking...")
        ranking_cfg = self.config.ranking

        scored_candidates = rank_candidates(
            candidates=fused_candidates,
            support_concepts=support_concepts,
            course_context=course_context,
            alpha=ranking_cfg.alpha,
            beta=ranking_cfg.beta,
            gamma=ranking_cfg.gamma,
            top_k=ranking_cfg.top_k,
            embedding_model=retrieval_cfg.embedding_model,
        )

        logger.info("  → Top %d candidates ranked.", len(scored_candidates))

        # === Bước 5.5: LLM Verification (Support Check) ===
        logger.info("Bước 5.5: LLM Verification (support check)...")
        scored_candidates = await verify_support_candidates(
            scored_candidates, course_context, course_name, self.config.llm
        )

        if not scored_candidates:
            logger.warning("Course %s: no candidates after LLM verification — aborting.", course_code)
            return

        # === Bước 6: Auto-accept and Export JSON ===
        logger.info("Bước 6: Bỏ qua Human Review, lưu thẳng JSON...")
        
        records: list[SupportSkillRecord] = []
        for cand in scored_candidates:
            record = SupportSkillRecord(
                course_code=course_code,
                course_title=course_name,
                relation_type="SUPPORTS_SKILL",
                esco_uri=cand.skill_uri,
                preferred_label=cand.skill_label,
                skill_type=cand.skill_type,
                support_concept_origin="; ".join(cand.concept_origins),
                final_score=cand.final_score,
                evidence_text=cand.evidence_text,
                review_status="accepted",
                llm_reasoning=cand.llm_reasoning,
                schema_version=self.config.schema_version,
            )
            records.append(record)

        write_records(records, self._output_dir)
        write_summary(course_code, course_name, records, self._output_dir)

        # === Bước 6.5: Concept Tag Builder (side-output cho KG) ===
        logger.info("Bước 6.5: Building ConceptTag nodes & edges...")
        build_concept_tags(
            course_code=course_code,
            support_concepts=support_concepts,
            scored_candidates=scored_candidates,
            output_dir=self._output_dir,
        )

        if self.config.output.write_cypher:
            write_cypher_file(records, self._output_dir, course_code)

        logger.info(
            "M5 Pipeline DONE: %s — %d candidates exported directly to %s/%s.",
            course_code, len(scored_candidates), self._output_dir, course_code
        )

    def finalize_course(
        self,
        course_code: str,
        review_path: str | Path | None = None,
    ) -> list[SupportSkillRecord]:
        """Đọc kết quả Human Review → Ghi SUPPORTS_SKILL (Bước 7).

        Chỉ gọi SAU KHI reviewer đã hoàn thành review.

        Args:
            course_code: Mã học phần.
            review_path: Đường dẫn tới file review đã hoàn thành.
                None = tự tìm trong {output_dir}/_review/{course_code}_review.json

        Returns:
            Danh sách SupportSkillRecord đã accepted và ghi output.
        """
        if review_path is None:
            review_path = self._output_dir / "_review" / f"{course_code}_review.json"

        review_path = Path(review_path)
        if not review_path.exists():
            logger.error("Review file not found: %s", review_path)
            return []

        logger.info("Bước 7: Importing review results from %s...", review_path)
        reviewed = import_review_results(review_path)

        # Filter accepted only
        accepted = [r for r in reviewed if r.review_status == "accepted"]

        if not accepted:
            logger.warning("Course %s: no accepted candidates after review.", course_code)
            return []

        # Build SupportSkillRecord
        records: list[SupportSkillRecord] = []

        for cand in accepted:
            record = SupportSkillRecord(
                course_code=cand.course_code,
                course_title="",  # Sẽ được fill từ review data
                relation_type="SUPPORTS_SKILL",
                esco_uri=cand.skill_uri,
                preferred_label=cand.preferred_label,
                skill_type=cand.skill_type,
                support_concept_origin="; ".join(cand.support_concept_origin),
                final_score=cand.final_score,
                evidence_text=cand.evidence_text,
                review_status="accepted",
                schema_version=self.config.schema_version,
            )
            records.append(record)

        # === Ghi JSON output ===
        write_records(records, self._output_dir)
        write_summary(course_code, "", records, self._output_dir)

        # === Ghi Cypher ===
        if self.config.output.write_cypher:
            write_cypher_file(records, self._output_dir, course_code)

        logger.info(
            "M5 Pipeline DONE: %s — %d SUPPORTS_SKILL relations finalized.",
            course_code, len(records),
        )

        return records

    def run_all(
        self,
        contract_dir: str | Path | None = None,
    ) -> None:
        """Chạy pipeline Bước 1→6 cho tất cả courses trong contract directory.

        Bước 7 phải gọi riêng qua finalize_course() sau khi review xong.
        """
        asyncio.run(self.run_all_async(contract_dir))

    async def run_all_async(
        self,
        contract_dir: str | Path | None = None,
    ) -> None:
        contract = Path(contract_dir or self.config.contract_dir)

        if not contract.is_dir():
            logger.error("Contract directory not found: %s", contract)
            return

        course_codes = [
            d.name for d in sorted(contract.iterdir())
            if d.is_dir() and not d.name.startswith("_")
        ]

        logger.info("Running M5 pipeline for %d courses...", len(course_codes))
        
        # Chạy đồng thời với giới hạn số lượng batch (tránh timeout HTTP)
        sem = asyncio.Semaphore(10)
        
        async def run_course_with_sem(code, contract):
            async with sem:
                return await self.run_course(code, contract)
                
        tasks = [run_course_with_sem(code, contract) for code in course_codes]
        await asyncio.gather(*tasks)
        logger.info(
            "M5 Pipeline batch completed: %d courses processed.",
            len(course_codes),
        )

if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.INFO)
    config = PipelineConfig()
    pipeline = SupportsSkillPipeline(config)
    pipeline.run_all()
