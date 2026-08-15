"""Cross-record validation for the Neo4j-ready KG export."""

from __future__ import annotations

from .models import KGExport


def validate_kg_export(export: KGExport) -> None:
    """Raise ``ValueError`` when identifiers, references, or ESCO keys conflict."""
    node_groups = [
        ("course_id", export.courses),
        ("description_id", export.descriptions),
        ("clo_id", export.clos),
        ("chapter_id", export.chapters),
        ("lesson_id", export.lessons),
    ]
    all_entity_ids: set[str] = set()
    for field, nodes in node_groups:
        identifiers = [getattr(node, field) for node in nodes]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError(f"Duplicate KG node identifier in {field}.")
        overlap = all_entity_ids.intersection(identifiers)
        if overlap:
            raise ValueError(f"Node identifiers collide across labels: {sorted(overlap)}")
        all_entity_ids.update(identifiers)

    skill_uris = [skill.skill_uri for skill in export.esco_skills]
    if len(skill_uris) != len(set(skill_uris)):
        raise ValueError("Duplicate ESCO skill_uri in KG export.")
    skill_uri_set = set(skill_uris)
    course_ids = {course.course_id for course in export.courses}

    entity_rel_keys: set[tuple[str, str, str]] = set()
    for relationship in export.entity_relationships:
        if relationship.source_id not in all_entity_ids or relationship.target_id not in all_entity_ids:
            raise ValueError(f"Broken entity relationship: {relationship.model_dump()}")
        key = (relationship.source_id, relationship.target_id, relationship.relationship_type)
        if key in entity_rel_keys:
            raise ValueError(f"Duplicate entity relationship: {key}")
        entity_rel_keys.add(key)

    course_skill_keys: set[tuple[str, str]] = set()
    for relationship in export.course_skill_relationships:
        if relationship.course_id not in course_ids:
            raise ValueError(f"Unknown course_id in course-skill relationship: {relationship.course_id}")
        if relationship.skill_uri not in skill_uri_set:
            raise ValueError(f"Unknown skill_uri in course-skill relationship: {relationship.skill_uri}")
        unknown_evidence = set(relationship.evidence_unit_ids) - all_entity_ids
        if unknown_evidence:
            raise ValueError(f"Unknown evidence unit identifiers: {sorted(unknown_evidence)}")
        key = (relationship.course_id, relationship.skill_uri)
        if key in course_skill_keys:
            raise ValueError(f"Duplicate course-skill relationship: {key}")
        course_skill_keys.add(key)

    # Validate occupation nodes uniqueness
    occupation_uris = [occ.occupation_uri for occ in export.occupations]
    if len(occupation_uris) != len(set(occupation_uris)):
        raise ValueError("Duplicate occupation_uri in KG export.")
    occupation_uri_set = set(occupation_uris)

    # Validate occupation-skill relationships referential integrity
    occ_skill_keys: set[tuple[str, str]] = set()
    for relationship in export.occupation_skill_relationships:
        if relationship.occupation_uri not in occupation_uri_set:
            raise ValueError(
                f"Unknown occupation_uri in occupation-skill relationship: {relationship.occupation_uri}"
            )
        if relationship.skill_uri not in skill_uri_set:
            raise ValueError(
                f"Unknown skill_uri in occupation-skill relationship: {relationship.skill_uri}"
            )
        key = (relationship.occupation_uri, relationship.skill_uri)
        if key in occ_skill_keys:
            raise ValueError(f"Duplicate occupation-skill relationship: {key}")
        occ_skill_keys.add(key)
