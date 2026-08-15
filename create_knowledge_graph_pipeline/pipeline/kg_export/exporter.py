"""Build and serialize a deterministic KG export from strict stage outputs."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from pipeline.extract_translate.models import TranslatedUnit
from pipeline.merge.models import CanonicalDocument
from pipeline.skill_matching.models import CourseSkillResult

from .models import (
    ChapterNode,
    CloNode,
    CourseNode,
    CourseSkillRelationship,
    DescriptionNode,
    EntityRelationship,
    EscoSkillNode,
    KGExport,
    LessonNode,
    OccupationNode,
    OccupationSkillRelationship,
)
from .validation import validate_kg_export


def _json_files(path: Path) -> list[Path]:
    if path.is_file():
        return [path]
    return sorted(path.glob("*.json")) if path.is_dir() else []


def _load_translations(path: Path) -> dict[str, str]:
    translations: dict[str, str] = {}
    for source in _json_files(path):
        payload = json.loads(source.read_text(encoding="utf-8"))
        if not isinstance(payload, list):
            raise ValueError(f"Translated-unit file must contain a list: {source}")
        for raw in payload:
            unit = TranslatedUnit.model_validate(raw)
            previous = translations.get(unit.unit_id)
            if previous is not None and previous != unit.text_en:
                raise ValueError(f"Conflicting English translations for unit_id {unit.unit_id}")
            translations[unit.unit_id] = unit.text_en
    return translations


def _load_occupation_data(
    occupations_path: Path,
    relations_path: Path,
) -> tuple[dict[str, dict], dict[str, list[dict]]]:
    """Load ESCO occupation metadata and occupation-skill relations from CSV.

    Returns:
        occupations_by_id: mapping occupation_id -> occupation row dict
        skill_uris_by_occupation: mapping occupation_uri -> list of relation row dicts
    """
    import csv

    occupations_by_id: dict[str, dict] = {}
    if occupations_path.is_file():
        with occupations_path.open(encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                occupations_by_id[row["occupation_id"]] = row

    skill_uris_by_occupation: dict[str, list[dict]] = {}
    if relations_path.is_file():
        with relations_path.open(encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                occ_uri = row["occupation_uri"]
                skill_uris_by_occupation.setdefault(occ_uri, []).append(row)

    return occupations_by_id, skill_uris_by_occupation


def build_kg_export(
    canonical_path: Path,
    translated_path: Path,
    skill_matches_path: Path,
    esco_occupations_path: Path | None = None,
    esco_relations_path: Path | None = None,
) -> KGExport:
    """Build the full in-memory graph and validate every reference before export."""
    translations = _load_translations(translated_path)
    courses: list[CourseNode] = []
    descriptions: list[DescriptionNode] = []
    clos: list[CloNode] = []
    chapters: list[ChapterNode] = []
    lessons: list[LessonNode] = []
    entity_relationships: list[EntityRelationship] = []

    for source in _json_files(canonical_path):
        document = CanonicalDocument.model_validate_json(source.read_text(encoding="utf-8"))
        course = document.course
        courses.append(CourseNode(
            course_id=course.course_id,
            course_code=course.course_code,
            internal_course_code=course.internal_course_code,
            name_vi=course.name_vi,
            name_en=translations.get(course.course_id) or course.name_en,
        ))
        descriptions.append(DescriptionNode(
            description_id=document.description.description_id,
            text_vi=document.description.text,
            text_en=translations.get(document.description.description_id),
        ))
        entity_relationships.append(EntityRelationship(
            source_id=course.course_id,
            target_id=document.description.description_id,
            relationship_type="HAS_DESCRIPTION",
        ))
        for clo in document.clos:
            clos.append(CloNode(
                clo_id=clo.clo_id,
                clo_code=clo.clo_code,
                content_vi=clo.content,
                content_en=translations.get(clo.clo_id),
            ))
            entity_relationships.append(EntityRelationship(
                source_id=course.course_id, target_id=clo.clo_id, relationship_type="HAS_CLO"
            ))
        for chapter in document.chapters:
            chapters.append(ChapterNode(
                chapter_id=chapter.chapter_id,
                chapter_code=chapter.chapter_code,
                title_vi=chapter.title,
                title_en=translations.get(chapter.chapter_id),
            ))
            entity_relationships.append(EntityRelationship(
                source_id=course.course_id, target_id=chapter.chapter_id, relationship_type="HAS_CHAPTER"
            ))
        for lesson in document.lessons:
            lessons.append(LessonNode(
                lesson_id=lesson.lesson_id,
                course_code=course.course_code,
                internal_course_code=course.internal_course_code,
                title_vi=lesson.title,
                title_en=translations.get(lesson.lesson_id),
            ))
            entity_relationships.append(EntityRelationship(
                source_id=lesson.chapter_ref_id or course.course_id,
                target_id=lesson.lesson_id,
                relationship_type="HAS_LESSON",
            ))

    skills_by_uri: dict[str, EscoSkillNode] = {}
    course_skill_relationships: list[CourseSkillRelationship] = []
    for source in _json_files(skill_matches_path):
        result = CourseSkillResult.model_validate_json(source.read_text(encoding="utf-8"))
        for skill in result.matched_skills:
            node = EscoSkillNode(
                skill_uri=skill.skill_uri,
                skill_id=skill.skill_id,
                skill_label=skill.skill_label,
                skill_description=skill.skill_description,
            )
            previous = skills_by_uri.get(skill.skill_uri)
            if previous is not None and previous != node:
                raise ValueError(f"Conflicting ESCO metadata for skill_uri {skill.skill_uri}")
            skills_by_uri[skill.skill_uri] = node
            course_skill_relationships.append(CourseSkillRelationship(
                course_id=result.course_id,
                skill_uri=skill.skill_uri,
                relationship_type=("TEACHES_SKILL" if skill.relation_type == "teaches" else "SUPPORTS_SKILL"),
                retrieval_score=skill.retrieval_score,
                rerank_score=skill.rerank_score,
                validation_confidence=skill.validation_confidence,
                evidence_unit_ids=[item.unit_id for item in skill.evidence],
                evidence_quotes=[item.quote for item in skill.evidence],
            ))

    # ── Occupation nodes & occupation-skill relationships ──────────────────
    occupations: list[OccupationNode] = []
    occupation_skill_relationships: list[OccupationSkillRelationship] = []
    if esco_occupations_path is not None and esco_relations_path is not None:
        matched_skill_uris = set(skills_by_uri.keys())
        occupations_by_id, skill_rows_by_occ_uri = _load_occupation_data(
            esco_occupations_path, esco_relations_path
        )
        # Index occupations by URI for reverse lookup
        occ_uri_to_row = {row["occupation_uri"]: row for row in occupations_by_id.values()}
        seen_occ_uris: set[str] = set()
        for occ_uri, skill_rows in skill_rows_by_occ_uri.items():
            # Only include occupations that have at least one matched skill
            relevant = [r for r in skill_rows if r["skillUri"] in matched_skill_uris]
            if not relevant:
                continue
            if occ_uri not in seen_occ_uris:
                occ_row = occ_uri_to_row.get(occ_uri)
                if occ_row is None:
                    continue
                occupations.append(OccupationNode(
                    occupation_uri=occ_uri,
                    occupation_id=occ_row["occupation_id"],
                    occupation_label=occ_row["occupation_label"],
                    occupation_description=occ_row.get("occupation_description") or None,
                ))
                seen_occ_uris.add(occ_uri)
            for rel_row in relevant:
                rel_type_raw = rel_row.get("relationType", "essential").strip().lower()
                relation_type = rel_type_raw if rel_type_raw in ("essential", "optional") else "essential"
                kg_rel = "REQUIRES_SKILL" if relation_type == "essential" else "OPTIONAL_SKILL"
                occupation_skill_relationships.append(OccupationSkillRelationship(
                    occupation_uri=occ_uri,
                    skill_uri=rel_row["skillUri"],
                    relation_type=relation_type,
                    kg_relationship=kg_rel,
                ))

    export = KGExport(
        courses=sorted(courses, key=lambda item: item.course_id),
        descriptions=sorted(descriptions, key=lambda item: item.description_id),
        clos=sorted(clos, key=lambda item: item.clo_id),
        chapters=sorted(chapters, key=lambda item: item.chapter_id),
        lessons=sorted(lessons, key=lambda item: item.lesson_id),
        esco_skills=sorted(skills_by_uri.values(), key=lambda item: item.skill_uri),
        occupations=sorted(occupations, key=lambda item: item.occupation_uri),
        entity_relationships=sorted(entity_relationships, key=lambda item: (item.source_id, item.relationship_type, item.target_id)),
        course_skill_relationships=sorted(course_skill_relationships, key=lambda item: (item.course_id, item.skill_uri)),
        occupation_skill_relationships=sorted(occupation_skill_relationships, key=lambda item: (item.occupation_uri, item.skill_uri)),
    )
    validate_kg_export(export)
    return export


def _write_csv(path: Path, records: list[dict[str, Any]], headers: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers, extrasaction="raise")
        writer.writeheader()
        writer.writerows(records)


def write_kg_export(export: KGExport, output_dir: Path) -> None:
    """Write validated graph records as deterministic UTF-8 Neo4j import CSV files."""
    validate_kg_export(export)
    output_dir.mkdir(parents=True, exist_ok=True)
    groups = {
        "courses.csv": (export.courses, CourseNode),
        "descriptions.csv": (export.descriptions, DescriptionNode),
        "clos.csv": (export.clos, CloNode),
        "chapters.csv": (export.chapters, ChapterNode),
        "lessons.csv": (export.lessons, LessonNode),
        "esco_skills.csv": (export.esco_skills, EscoSkillNode),
        "occupations.csv": (export.occupations, OccupationNode),
        "entity_relationships.csv": (export.entity_relationships, EntityRelationship),
        "course_skill_relationships.csv": (export.course_skill_relationships, CourseSkillRelationship),
        "occupation_skill_relationships.csv": (export.occupation_skill_relationships, OccupationSkillRelationship),
    }
    for filename, (models, model_type) in groups.items():
        records = [model.model_dump(mode="json", exclude_none=False) for model in models]
        for record in records:
            for key, value in list(record.items()):
                if isinstance(value, list):
                    record[key] = json.dumps(value, ensure_ascii=False)
        _write_csv(output_dir / filename, records, list(model_type.model_fields))
    (output_dir / "kg_export.json").write_text(
        export.model_dump_json(indent=2, exclude_none=True), encoding="utf-8"
    )


def export_kg(
    canonical_path: Path,
    translated_path: Path,
    skill_matches_path: Path,
    output_dir: Path,
    esco_occupations_path: Path | None = None,
    esco_relations_path: Path | None = None,
) -> KGExport:
    export = build_kg_export(
        canonical_path,
        translated_path,
        skill_matches_path,
        esco_occupations_path=esco_occupations_path,
        esco_relations_path=esco_relations_path,
    )
    write_kg_export(export, output_dir)
    return export
