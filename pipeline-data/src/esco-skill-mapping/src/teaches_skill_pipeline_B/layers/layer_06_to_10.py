"""Layer 06 to 10 — Post-Processing & Export.

Gộp các bước cuối cùng của pipeline:
- Tầng 6: ESCO Normalization
- Tầng 7: Classification (Skill vs Knowledge)
- Tầng 8: Provenance Tracking (Gắn evidence)
- Tầng 9: Aggregation (Gom cụm theo môn học)
- Tầng 10: Export (JSON/Neo4j)
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from .layer_04_reranking import TieredCandidate
from ..models.schemas import SkillTeacherRecord, EvidenceRef, ExtractionInfo, RetrievalInfo, EvidenceUnit, RawMention

logger = logging.getLogger(__name__)

class PostProcessingLayer:
    """Xử lý các bước sau quyết định và xuất kết quả."""

    def __init__(self, config: Any):
        self.config = config
        self.output_dir = Path(getattr(config.output, "output_dir", "output"))
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Để normalization, ta cần ESCO metadata (nếu có config)
        self.metadata_path = getattr(config.retrieval, "faiss_metadata_path", "models/esco_metadata.json")
        self._lookup: dict[str, dict[str, Any]] = {}
        self._metadata_loaded = False

    def _load_metadata(self) -> None:
        if self._metadata_loaded:
            return
        path = Path(self.metadata_path)
        if not path.exists():
            logger.warning("ESCO metadata not found for normalization at %s", path)
            return
            
        with open(path, encoding="utf-8") as f:
            metadata = json.load(f)
            
        if isinstance(metadata, list):
            for item in metadata:
                uri = item.get("skill_uri", "")
                if uri:
                    self._lookup[uri] = item
        elif isinstance(metadata, dict):
            self._lookup = metadata
            
        self._metadata_loaded = True
        logger.info("Loaded metadata for %d concepts", len(self._lookup))

    def run(self, accepted: list[TieredCandidate], course_code: str, course_title: str, course_type: str, evidence_units: list[EvidenceUnit], mentions: list[RawMention] | None = None) -> list[SkillTeacherRecord]:
        """Biến đổi TieredCandidate thành SkillTeacherRecord và xuất JSON."""
        self._load_metadata()
        records: list[SkillTeacherRecord] = []
        
        eu_lookup = {eu.evidence_id: eu for eu in evidence_units}

        for tc in accepted:
            cand = tc.candidate
            
            # Layer 6: Normalization
            meta = self._lookup.get(cand.skill_uri, {})
            pref_label = meta.get("skill_label", cand.skill_label)
            skill_type = meta.get("skill_type", "skill/competence")
            
            # Layer 7: Classification (Skill vs Knowledge)
            concept_type = "knowledge" if "knowledge" in str(skill_type).lower() else "skill"
            relation_type = "TEACHES_KNOWLEDGE" if concept_type == "knowledge" else "TEACHES_SKILL"
            
            # Check mismatch head type
            head_type_signal = None
            if cand.head_types:
                skill_count = sum(1 for h in cand.head_types if h == "skill")
                knowledge_count = sum(1 for h in cand.head_types if h == "knowledge")
                head_type_signal = "skill" if skill_count >= knowledge_count else "knowledge"
                
            mismatch_flagged = (head_type_signal and head_type_signal != concept_type) or getattr(cand, "mismatch_penalty_applied", False)
            esco_type_agrees = (head_type_signal == concept_type) if head_type_signal else True

            # Layer 8: Provenance
            evidence_refs = []
            for eid in cand.evidence_ids:
                if eid in eu_lookup:
                    eu = eu_lookup[eid]
                    meta_dict = dict(eu.meta)
                    eid_mentions = cand.evidence_mentions.get(eid, [])
                    if eid_mentions:
                        meta_dict["matched_mention"] = "; ".join(eid_mentions)

                    evidence_refs.append(EvidenceRef(
                        source_type=eu.source_type,
                        source_id=eu.source_id,
                        text=eu.text,
                        meta=meta_dict,
                        evidence_weight=eu.evidence_weight,
                        is_boilerplate=eu.is_boilerplate,
                    ))

            extraction_info = ExtractionInfo(
                source=",".join(set(cand.extraction_sources)) if cand.extraction_sources else "unknown",
                matched_head_type=head_type_signal,
                esco_type_agrees=esco_type_agrees,
            )
            
            retrieval_info = RetrievalInfo(
                bm25_rank=cand.bm25_rank,
                dense_rank=cand.dense_rank,
                esco_extract_skill_rank=cand.esco_extract_rank,
                # RRF rank was implicit by its score
            )

            # Build record
            record = SkillTeacherRecord(
                course_code=course_code,
                course_title=course_title,
                course_type=course_type,
                relation_type=relation_type,
                concept_type=concept_type,
                esco_uri=cand.skill_uri,
                preferred_label=pref_label,
                skill_type=skill_type,
                confidence=cand.combined_score,
                tier=tc.tier,
                confidence_level=tc.confidence_level,
                decision_status=tc.decision,
                evidence=evidence_refs,
                extraction=extraction_info,
                retrieval=retrieval_info,
                cross_encoder_score=cand.score_rerank,
                over_soft_cap=tc.over_soft_cap,
                mismatch_flagged=mismatch_flagged,
                mismatch_penalty_applied=getattr(cand, "mismatch_penalty_applied", False),
                retrieval_agreement=cand.retrieval_agreement,
                low_evidence_quality=cand.low_evidence_quality,
                method="LLM_Extraction+FAISS_BM25_RRF+UniSkill",
                llm_reasoning=tc.llm_reasoning,
            )
            records.append(record)
            
        # Layer 10: Export JSON
        self._export_json(course_code, records)

        # Side-output: Export ConceptTag entities & edges cho KG
        if mentions:
            self._export_concept_tags(course_code, mentions, accepted)

        return records

    def _export_json(self, course_code: str, records: list[SkillTeacherRecord]) -> None:
        """Xuất records ra thư mục theo định dạng _summary và từng file skill/knowledge."""
        import re
        course_dir = self.output_dir / course_code
        course_dir.mkdir(parents=True, exist_ok=True)
        
        # 1. Xuất từng file
        skills_summary = []
        knowledges_summary = []
        tier_dist = {"PRIMARY": 0, "SECONDARY": 0, "OPTIONAL": 0, "low_confidence": 0}
        
        course_title = records[0].course_title if records else ""
        course_type = records[0].course_type if records else ""
        
        for r in records:
            tier_dist[r.tier] = tier_dist.get(r.tier, 0) + 1
            
            # Formatting file data
            r_dict = r.to_dict()
            file_data = {
                "esco_concept": {
                    "uri": r.esco_uri,
                    "preferred_label": r.preferred_label,
                    "skill_type": r.skill_type,
                    "concept_type": r.concept_type,
                    "relation_type": r.relation_type
                },
                "course": {
                    "course_code": r.course_code,
                    "course_title": r.course_title,
                    "course_type": r.course_type
                },
                "decision": {
                    "confidence": r.confidence,
                    "cross_encoder_score": r.cross_encoder_score,
                    "tier": r.tier,
                    "confidence_level": r.confidence_level,
                    "decision_status": r.decision_status,
                    "over_soft_cap": r.over_soft_cap,
                    "mismatch_flagged": r.mismatch_flagged,
                    "mismatch_penalty_applied": r.mismatch_penalty_applied,
                    "llm_reasoning": r.llm_reasoning
                },
                "evidence": r_dict["evidence"],
                "pipeline_provenance": {
                    "extraction": r_dict.get("extraction"),
                    "retrieval": r_dict.get("retrieval"),
                    "method": r.method,
                    "schema_version": r.schema_version
                }
            }
            
            safe_label = re.sub(r'[^a-z0-9]+', '_', r.preferred_label.lower()).strip('_')
            filename = f"{r.concept_type}__{safe_label}.json"
            
            with open(course_dir / filename, "w", encoding="utf-8") as f:
                json.dump(file_data, f, ensure_ascii=False, indent=2)
                
            # Formatting summary entry
            sum_entry = {
                "preferred_label": r.preferred_label,
                "esco_uri": r.esco_uri,
                "confidence": r.confidence,
                "cross_encoder_score": r.cross_encoder_score,
                "tier": r.tier,
                "confidence_level": r.confidence_level,
                "decision_status": r.decision_status,
                "evidence_count": len(r.evidence),
                "llm_reasoning": r.llm_reasoning
            }
            if r.concept_type == "skill":
                skills_summary.append(sum_entry)
            else:
                knowledges_summary.append(sum_entry)
                
        # 2. Xuất _summary.json
        summary_data = {
            "course_code": course_code,
            "course_title": course_title,
            "course_type": course_type,
            "statistics": {
                "total_records": len(records),
                "skill_count": len(skills_summary),
                "knowledge_count": len(knowledges_summary),
                "tier_distribution": tier_dist
            },
            "skills": skills_summary,
            "knowledges": knowledges_summary,
            "schema_version": "3.0"
        }
        with open(course_dir / "_summary.json", "w", encoding="utf-8") as f:
            json.dump(summary_data, f, ensure_ascii=False, indent=2)
            
        logger.info("Exported %d records to %s/", len(records), course_dir)

    def _export_concept_tags(
        self,
        course_code: str,
        mentions: list[RawMention],
        accepted: list[TieredCandidate],
    ) -> None:
        """Xuất ConceptTag entities và edges cho Knowledge Graph.

        Side-output thuần túy — không ảnh hưởng SkillTeacherRecord.
        Output: _concept_tags.json gồm:
          - concept_tags: danh sách entity (deduplicated)
          - has_concept_edges: HocPhan → ConceptTag
          - evidence_for_edges: ConceptTag → KyNangESCO
        """
        course_dir = self.output_dir / course_code
        course_dir.mkdir(parents=True, exist_ok=True)

        # 1. Gom tất cả mention thành ConceptTag (deduplicate theo normalized text)
        concept_tags: dict[str, dict] = {}
        for m in mentions:
            key = m.text.strip().lower()
            if not key or len(key) < 2:
                continue
            if key not in concept_tags:
                concept_tags[key] = {
                    "text": m.text.strip(),
                    "normalized": key,
                    "evidence_ids": [],
                }
            if m.evidence_id not in concept_tags[key]["evidence_ids"]:
                concept_tags[key]["evidence_ids"].append(m.evidence_id)

        # 2. Build EVIDENCE_FOR edges từ accepted candidates
        evidence_for_edges: list[dict] = []
        seen_pairs: set[tuple[str, str]] = set()
        for tc in accepted:
            cand = tc.candidate
            for mention_text in cand.mention_texts:
                key = mention_text.strip().lower()
                pair = (key, cand.skill_uri)
                if pair in seen_pairs:
                    continue
                seen_pairs.add(pair)
                evidence_for_edges.append({
                    "concept_tag": key,
                    "esco_uri": cand.skill_uri,
                    "esco_label": cand.skill_label,
                    "confidence": cand.combined_score,
                    "pipeline_source": "teaches_B",
                })

        # 3. Build HAS_CONCEPT edges
        has_concept_edges: list[dict] = [
            {
                "course_code": course_code,
                "concept_tag": tag["normalized"],
                "role": "teach",
                "source_evidence_ids": tag["evidence_ids"],
            }
            for tag in concept_tags.values()
        ]

        # 4. Xuất file
        output_data = {
            "course_code": course_code,
            "concept_tags": [
                {"text": t["text"], "normalized": t["normalized"]}
                for t in concept_tags.values()
            ],
            "has_concept_edges": has_concept_edges,
            "evidence_for_edges": evidence_for_edges,
            "statistics": {
                "total_concept_tags": len(concept_tags),
                "total_has_concept_edges": len(has_concept_edges),
                "total_evidence_for_edges": len(evidence_for_edges),
            },
        }

        with open(course_dir / "_concept_tags.json", "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

        logger.info(
            "Exported %d concept tags (%d EVIDENCE_FOR edges) to %s/",
            len(concept_tags), len(evidence_for_edges), course_dir,
        )
