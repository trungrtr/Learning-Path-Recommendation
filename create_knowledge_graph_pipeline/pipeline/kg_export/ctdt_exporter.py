"""Build and serialize Neo4j-ready CSVs for programme-level CTDT data."""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any, Type

from pipeline.extract_ctdt.mo_hinh import CtdtDocument

from .models import (
    CtdtCourseDependencyRelationship,
    CtdtCourseRelationship,
    CtdtGroupNode,
    CtdtGroupRelationship,
    CtdtKGExport,
    CtdtProgramGroupRelationship,
    CtdtProgramNode,
)


def _json_files(path: Path) -> list[Path]:
    if path.is_file():
        return [path]
    return sorted(path.glob("*.json")) if path.is_dir() else []


def _slugify(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", value).strip("_").upper() or "UNKNOWN"


def _program_id(document: CtdtDocument, source: Path) -> str:
    return f"CTDT_{_slugify(document.ma_ctdt or source.stem)}"


def _group_id(program_id: str, nhom_id: str | None, ten_nhom: str | None, index: int) -> str:
    key = nhom_id or ten_nhom or f"GROUP_{index}"
    return f"{program_id}_GROUP_{_slugify(key)}"


def _put_unique(mapping: dict[str, Any], key: str, value: Any, label: str) -> None:
    previous = mapping.get(key)
    if previous is not None and previous != value:
        raise ValueError(f"Conflicting {label} for identifier {key}")
    mapping[key] = value


def _ensure_unassigned_group(
    program_id: str,
    groups: dict[str, CtdtGroupNode],
    program_group_relationships: dict[tuple[str, str], CtdtProgramGroupRelationship],
) -> str:
    group_id = f"{program_id}_GROUP_UNASSIGNED"
    _put_unique(
        groups,
        group_id,
        CtdtGroupNode(
            group_id=group_id,
            program_id=program_id,
            nhom_id="UNASSIGNED",
            ten_nhom="Chua xac dinh nhom",
            tong_so_tin=0,
        ),
        "CTDT group",
    )
    program_group_relationships[(program_id, group_id)] = CtdtProgramGroupRelationship(
        program_id=program_id,
        group_id=group_id,
    )
    return group_id


def build_ctdt_kg_export(ctdt_path: Path) -> CtdtKGExport:
    """Build programme/group/course graph records from ``extract_ctdt`` JSON."""
    programs: dict[str, CtdtProgramNode] = {}
    groups: dict[str, CtdtGroupNode] = {}
    program_group_relationships: dict[tuple[str, str], CtdtProgramGroupRelationship] = {}
    group_relationships: dict[tuple[str, str], CtdtGroupRelationship] = {}
    course_relationships: dict[tuple[str, str, str], CtdtCourseRelationship] = {}
    dependency_relationships: dict[
        tuple[str, str, str], CtdtCourseDependencyRelationship
    ] = {}

    for source in _json_files(ctdt_path):
        document = CtdtDocument.model_validate_json(source.read_text(encoding="utf-8"))
        program_id = _program_id(document, source)
        _put_unique(
            programs,
            program_id,
            CtdtProgramNode(
                program_id=program_id,
                ma_ctdt=document.ma_ctdt or None,
                ten_nganh=document.ten_nganh or None,
            ),
            "CTDT program",
        )

        group_ids_by_nhom_id: dict[str, str] = {}
        for index, group in enumerate(document.nhom_mon, start=1):
            group_id = _group_id(program_id, group.nhom_id, group.ten_nhom, index)
            _put_unique(
                groups,
                group_id,
                CtdtGroupNode(
                    group_id=group_id,
                    program_id=program_id,
                    nhom_id=group.nhom_id or None,
                    ten_nhom=group.ten_nhom or None,
                    nhom_cha_id=group.nhom_cha_id,
                    tong_so_tin=group.tong_so_tin,
                ),
                "CTDT group",
            )
            if group.nhom_id:
                group_ids_by_nhom_id[group.nhom_id] = group_id
            program_group_relationships[(program_id, group_id)] = CtdtProgramGroupRelationship(
                program_id=program_id,
                group_id=group_id,
            )

        for group in document.nhom_mon:
            if not group.nhom_id or not group.nhom_cha_id:
                continue
            child_id = group_ids_by_nhom_id.get(group.nhom_id)
            parent_id = group_ids_by_nhom_id.get(group.nhom_cha_id)
            if child_id and parent_id:
                group_relationships[(parent_id, child_id)] = CtdtGroupRelationship(
                    parent_group_id=parent_id,
                    child_group_id=child_id,
                )

        for course in document.hoc_phan:
            if not course.ma_hp:
                continue
            group_id = group_ids_by_nhom_id.get(course.nhom_id)
            if group_id is None:
                group_id = _ensure_unassigned_group(program_id, groups, program_group_relationships)
            course_relationships[(program_id, group_id, course.ma_hp)] = CtdtCourseRelationship(
                program_id=program_id,
                group_id=group_id,
                ma_hp=course.ma_hp,
                hoc_ky=course.hoc_ky,
            )
            for dependency in course.tien_quyet:
                dependency_relationships[(course.ma_hp, dependency, "TIEN_QUYET")] = (
                    CtdtCourseDependencyRelationship(
                        ma_hp=course.ma_hp,
                        dependency_ma_hp=dependency,
                        dependency_type="TIEN_QUYET",
                        relationship_type="REQUIRES_COURSE",
                    )
                )
            for dependency in course.hoc_truoc:
                dependency_relationships[(course.ma_hp, dependency, "HOC_TRUOC")] = (
                    CtdtCourseDependencyRelationship(
                        ma_hp=course.ma_hp,
                        dependency_ma_hp=dependency,
                        dependency_type="HOC_TRUOC",
                        relationship_type="RECOMMENDS_PRIOR_COURSE",
                    )
                )

    export = CtdtKGExport(
        programs=sorted(programs.values(), key=lambda item: item.program_id),
        groups=sorted(groups.values(), key=lambda item: item.group_id),
        program_group_relationships=sorted(
            program_group_relationships.values(), key=lambda item: (item.program_id, item.group_id)
        ),
        group_relationships=sorted(
            group_relationships.values(), key=lambda item: (item.parent_group_id, item.child_group_id)
        ),
        course_relationships=sorted(
            course_relationships.values(), key=lambda item: (item.program_id, item.group_id, item.ma_hp)
        ),
        course_dependency_relationships=sorted(
            dependency_relationships.values(),
            key=lambda item: (item.ma_hp, item.dependency_type, item.dependency_ma_hp),
        ),
    )
    validate_ctdt_kg_export(export)
    return export


def validate_ctdt_kg_export(export: CtdtKGExport) -> None:
    program_ids = [item.program_id for item in export.programs]
    if len(program_ids) != len(set(program_ids)):
        raise ValueError("Duplicate CTDT program_id.")
    program_id_set = set(program_ids)

    group_ids = [item.group_id for item in export.groups]
    if len(group_ids) != len(set(group_ids)):
        raise ValueError("Duplicate CTDT group_id.")
    group_id_set = set(group_ids)

    for group in export.groups:
        if group.program_id not in program_id_set:
            raise ValueError(f"Unknown program_id in CTDT group: {group.program_id}")

    seen_program_group: set[tuple[str, str]] = set()
    for relationship in export.program_group_relationships:
        if relationship.program_id not in program_id_set:
            raise ValueError(f"Unknown program_id in CTDT program-group relationship: {relationship.program_id}")
        if relationship.group_id not in group_id_set:
            raise ValueError(f"Unknown group_id in CTDT program-group relationship: {relationship.group_id}")
        key = (relationship.program_id, relationship.group_id)
        if key in seen_program_group:
            raise ValueError(f"Duplicate CTDT program-group relationship: {key}")
        seen_program_group.add(key)

    seen_group_rel: set[tuple[str, str]] = set()
    for relationship in export.group_relationships:
        if relationship.parent_group_id not in group_id_set or relationship.child_group_id not in group_id_set:
            raise ValueError(f"Broken CTDT group relationship: {relationship.model_dump()}")
        key = (relationship.parent_group_id, relationship.child_group_id)
        if key in seen_group_rel:
            raise ValueError(f"Duplicate CTDT group relationship: {key}")
        seen_group_rel.add(key)

    seen_course_rel: set[tuple[str, str, str]] = set()
    for relationship in export.course_relationships:
        if relationship.program_id not in program_id_set:
            raise ValueError(f"Unknown program_id in CTDT course relationship: {relationship.program_id}")
        if relationship.group_id not in group_id_set:
            raise ValueError(f"Unknown group_id in CTDT course relationship: {relationship.group_id}")
        key = (relationship.program_id, relationship.group_id, relationship.ma_hp)
        if key in seen_course_rel:
            raise ValueError(f"Duplicate CTDT course relationship: {key}")
        seen_course_rel.add(key)

    seen_dependency_rel: set[tuple[str, str, str]] = set()
    for relationship in export.course_dependency_relationships:
        key = (relationship.ma_hp, relationship.dependency_ma_hp, relationship.dependency_type)
        if key in seen_dependency_rel:
            raise ValueError(f"Duplicate CTDT course dependency relationship: {key}")
        seen_dependency_rel.add(key)


def _write_csv(path: Path, records: list[dict[str, Any]], headers: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers, extrasaction="raise")
        writer.writeheader()
        writer.writerows(records)


def _dump_records(models: list[Any]) -> list[dict[str, Any]]:
    return [model.model_dump(mode="json", exclude_none=False) for model in models]


def write_ctdt_kg_export(export: CtdtKGExport, output_dir: Path) -> None:
    """Write CTDT graph records as deterministic CSV files inside kg_ready."""
    validate_ctdt_kg_export(export)
    output_dir.mkdir(parents=True, exist_ok=True)
    groups: dict[str, tuple[list[Any], Type[Any]]] = {
        "ctdt_programs.csv": (export.programs, CtdtProgramNode),
        "ctdt_groups.csv": (export.groups, CtdtGroupNode),
        "ctdt_program_group_relationships.csv": (
            export.program_group_relationships,
            CtdtProgramGroupRelationship,
        ),
        "ctdt_group_relationships.csv": (export.group_relationships, CtdtGroupRelationship),
        "ctdt_course_relationships.csv": (export.course_relationships, CtdtCourseRelationship),
        "ctdt_course_dependency_relationships.csv": (
            export.course_dependency_relationships,
            CtdtCourseDependencyRelationship,
        ),
    }
    for filename, (models, model_type) in groups.items():
        _write_csv(output_dir / filename, _dump_records(models), list(model_type.model_fields))
    (output_dir / "ctdt_kg_export.json").write_text(
        export.model_dump_json(indent=2, exclude_none=True), encoding="utf-8"
    )


def export_ctdt_kg(ctdt_path: Path, output_dir: Path) -> CtdtKGExport:
    export = build_ctdt_kg_export(ctdt_path)
    write_ctdt_kg_export(export, output_dir)
    return export

