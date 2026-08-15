from pipeline.skill_matching.aggregate import aggregate_by_course


def _validated(decision: str) -> dict:
    validation = {
        "course_id": "COURSE_1",
        "skill_uri": "https://data.europa.eu/esco/skill/S1",
        "decision": decision,
        "confidence": 0.9,
        "evidence_unit_ids": [],
        "evidence_quotes": [],
        "reason": "Decision reason",
    }
    if decision == "yes":
        validation.update({
            "relation_type": "teaches",
            "evidence_unit_ids": ["L1"],
            "evidence_quotes": ["Matrix operations"],
        })
    return {
        "candidate": {
            "course_id": "COURSE_1",
            "skill_id": "S1",
            "skill_uri": "https://data.europa.eu/esco/skill/S1",
            "skill_label": "perform matrix operations",
            "top_evidence": [{
                "unit_id": "L1", "unit_type": "lesson", "query_id": "Q1",
                "evidence_text_en": "Matrix operations", "retrieval_score": 0.7,
                "rerank_score": 0.8,
            }],
            "best_retrieval_score": 0.7,
            "best_rerank_score": 0.8,
        },
        "validation": validation,
    }


def test_aggregation_keeps_only_yes_and_preserves_evidence() -> None:
    results = aggregate_by_course([_validated("yes"), _validated("no")])
    assert len(results) == 1
    assert len(results[0]["matched_skills"]) == 1
    assert results[0]["matched_skills"][0]["evidence"][0]["unit_id"] == "L1"


def test_aggregation_emits_empty_auditable_course_result() -> None:
    results = aggregate_by_course(
        [_validated("no")],
        course_metadata={"COURSE_1": {"internal_course_code": "BS6001"}},
    )
    assert results[0]["internal_course_code"] == "BS6001"
    assert results[0]["matched_skills"] == []
