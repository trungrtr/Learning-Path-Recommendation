"""CLI for exporting ``extract_ctdt`` output to Neo4j-ready CSV files."""

from __future__ import annotations

import argparse
from pathlib import Path

from pipeline.extract_course.cau_hinh import DEFAULT_CONFIG, ROOT_DIR, load_settings

from .ctdt_exporter import export_ctdt_kg


def main() -> None:
    parser = argparse.ArgumentParser(description="Export extracted CTDT data for Neo4j.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--ctdt", type=Path, help="Override ctdt_extracted_dir from config.")
    parser.add_argument("--output", type=Path, help="Override neo4j_import_dir from config.")
    args = parser.parse_args()

    paths = load_settings(args.config)["paths"]
    ctdt = args.ctdt or ROOT_DIR / paths["ctdt_extracted_dir"]
    output = args.output or ROOT_DIR / paths["neo4j_import_dir"]
    export = export_ctdt_kg(ctdt, output)
    print(f"Exported CTDT programs: {len(export.programs)}")
    print(f"Exported CTDT groups: {len(export.groups)}")
    print(f"Exported CTDT course links: {len(export.course_relationships)}")
    print(f"Exported CTDT dependency links: {len(export.course_dependency_relationships)}")
    print(f"Saved CTDT KG files in: {output}")


if __name__ == "__main__":
    main()

