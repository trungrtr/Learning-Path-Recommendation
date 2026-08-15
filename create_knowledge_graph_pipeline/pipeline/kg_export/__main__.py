"""CLI for strict Neo4j-ready KG export."""

from __future__ import annotations

import argparse
from pathlib import Path

from pipeline.extract_course.cau_hinh import DEFAULT_CONFIG, ROOT_DIR, load_settings

from .exporter import export_kg


def main() -> None:
    parser = argparse.ArgumentParser(description="Export validated HaUI course-skill data for Neo4j.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--canonical", type=Path)
    parser.add_argument("--translated", type=Path)
    parser.add_argument("--matches", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    paths = load_settings(args.config)["paths"]
    skill_matching_cfg = load_settings(args.config).get("skill_matching", {})
    canonical = args.canonical or ROOT_DIR / paths["canonical_dir"]
    translated = args.translated or ROOT_DIR / paths["translated_units_dir"]
    matches = args.matches or ROOT_DIR / paths["skill_matches_dir"]
    output = args.output or ROOT_DIR / paths["neo4j_import_dir"]
    esco_occupations_path = ROOT_DIR / skill_matching_cfg["esco_occupations_csv"]
    esco_relations_path = ROOT_DIR / skill_matching_cfg["esco_relations_csv"]
    export = export_kg(
        canonical,
        translated,
        matches,
        output,
        esco_occupations_path=esco_occupations_path,
        esco_relations_path=esco_relations_path,
    )
    print(f"Exported courses: {len(export.courses)}")
    print(f"Exported ESCO skills: {len(export.esco_skills)}")
    print(f"Exported occupations: {len(export.occupations)}")
    print(f"Exported course-skill relationships: {len(export.course_skill_relationships)}")
    print(f"Exported occupation-skill relationships: {len(export.occupation_skill_relationships)}")
    print(f"Saved KG files in: {output}")


if __name__ == "__main__":
    main()
