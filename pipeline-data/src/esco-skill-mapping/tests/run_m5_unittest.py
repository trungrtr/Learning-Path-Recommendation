"""Standard unittest script cho M5 Supports Pipeline."""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pipeline.course_evidence_builder.objective_evidence import build_objective_evidence
from pipeline.esco_concept_provider.concept_metadata_lookup import ConceptMetadataLookup
from pipeline.m5_supports_pipeline import (
    M5Candidate,
    M5PipelineConfig,
    M5SupportRecord,
    M5SupportsPipeline,
)
from pipeline.m5_supports_pipeline.rrf_combiner import combine_channels
from pipeline.m5_supports_pipeline.tiering_router import route_m5_tiers
from pipeline.relation_dedup.overlap_resolver import resolve_m4_m5_overlap


class TestM5Pipeline(unittest.TestCase):

    def test_build_objective_evidence(self):
        evidence = build_objective_evidence(
            course_code="SC6014",
            muc_tieu_texts=["Hiểu kiến thức lập trình cơ bản."],
            mo_ta_tom_tat_en="Basic programming course description.",
        )
        self.assertEqual(len(evidence), 1)
        self.assertEqual(evidence[0].course_code, "SC6014")
        self.assertIn("Hiểu kiến thức", evidence[0].text)
        self.assertIn("Basic programming", evidence[0].text)

    def test_rrf_combiner(self):
        retrieval = [
            M5Candidate("http://esco/s1", "S1", "desc", "skill", score_retrieval=0.9),
            M5Candidate("http://esco/s2", "S2", "desc", "skill", score_retrieval=0.8),
        ]
        llm = [
            M5Candidate("http://esco/s2", "S2", "desc", "skill", score_llm=0.95),
            M5Candidate("http://esco/s3", "S3", "desc", "skill", score_llm=0.7),
        ]

        merged = combine_channels(retrieval, llm, concept_type="skill", rrf_k=60)
        self.assertEqual(len(merged), 3)
        self.assertEqual(merged[0].skill_uri, "http://esco/s2")
        self.assertGreater(merged[0].score_final, merged[1].score_final)

    def test_tiering_router_hard_caps(self):
        candidates = [
            M5Candidate(f"http://esco/s{i}", f"Skill {i}", "desc", "skill", score_final=0.03 - 0.001 * i)
            for i in range(20)
        ]
        config = M5PipelineConfig(course_type="FOUNDATIONAL")
        accepted, rejected = route_m5_tiers(candidates, config, concept_type="skill")

        self.assertEqual(len(accepted), 7)
        self.assertEqual(len(rejected), 13)
        self.assertEqual(rejected[0].reject_reason, "exceeds_hard_cap_7")

    def test_overlap_resolver(self):
        m4_records = ["http://esco/s1", "http://esco/s2"]
        m5_candidates = [
            M5Candidate("http://esco/s1", "S1", "desc", "skill"),
            M5Candidate("http://esco/s3", "S3", "desc", "skill"),
        ]

        deduped, removed = resolve_m4_m5_overlap(m4_records, m5_candidates, concept_type="skill")
        self.assertEqual(len(deduped), 1)
        self.assertEqual(deduped[0].skill_uri, "http://esco/s3")
        self.assertEqual(len(removed), 1)
        self.assertEqual(removed[0].skill_uri, "http://esco/s1")

    def test_m5_supports_pipeline_end_to_end(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            skill_pool = [
                {
                    "skill_uri": "http://data.europa.eu/esco/skill/s1",
                    "preferred_label": "Python programming",
                    "description": "Write Python code",
                    "skill_type": "skill/competence",
                },
            ]
            knowledge_pool = [
                {
                    "skill_uri": "http://data.europa.eu/esco/skill/k1",
                    "preferred_label": "Computer science principles",
                    "description": "Fundamental CS knowledge",
                    "skill_type": "knowledge",
                },
            ]
            (tmp_path / "skill_pool.json").write_text(json.dumps(skill_pool), encoding="utf-8")
            (tmp_path / "knowledge_pool.json").write_text(json.dumps(knowledge_pool), encoding="utf-8")

            config = M5PipelineConfig(
                pool_dir=tmp_path,
                output_dir=tmp_path / "supports",
                course_type="SPECIALIZED",
                llm_enabled=False,
            )
            lookup = ConceptMetadataLookup(tmp_path)
            pipeline = M5SupportsPipeline(config=config, metadata_lookup=lookup)

            records, accepted, rejected = pipeline.run_course(
                course_code="TEST101",
                course_title="Test Course",
                muc_tieu=["Understand database concepts."],
                mo_ta_tom_tat_en="Course covering databases and Python.",
            )

            out_dir = tmp_path / "supports" / "TEST101"
            self.assertTrue(out_dir.exists() or (tmp_path / "supports" / "_candidate_logs").exists())


if __name__ == "__main__":
    unittest.main()
