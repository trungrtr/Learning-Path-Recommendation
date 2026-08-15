import argparse
import logging
from pathlib import Path

from pipeline.neo4j_importer.config import load_neo4j_config, get_neo4j_credentials
from pipeline.neo4j_importer.loader import Neo4jLoader

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")

def main():
    parser = argparse.ArgumentParser(description="Import KG CSVs to Neo4j")
    parser.add_argument("--csv-dir", type=Path, default="data/06_kg_ready", help="Directory containing CSV files")
    parser.add_argument("--config-file", type=Path, default="Neo4j-e3022131-Created-2026-08-13.txt", help="Neo4j config file")
    args = parser.parse_args()

    load_neo4j_config(args.config_file)
    uri, username, password, database = get_neo4j_credentials()
    
    if not uri:
        logging.error("Missing Neo4j connection details. Check config file.")
        return

    loader = Neo4jLoader(uri, username, password, database)
    try:
        logging.info("Creating constraints...")
        loader.create_constraints()
        
        # Load nodes first
        node_files = ["courses.csv", "esco_skills.csv", "occupations.csv", "chapters.csv", "lessons.csv", "clos.csv", "ctdt_programs.csv", "ctdt_groups.csv"]
        for f in node_files:
            p = args.csv_dir / f
            if p.exists():
                loader.load_csv(p)
                
        # Load relationships
        rel_files = ["course_skill_relationships.csv", "occupation_skill_relationships.csv", "ctdt_course_relationships.csv", "ctdt_course_dependency_relationships.csv", "ctdt_program_group_relationships.csv", "ctdt_group_relationships.csv", "entity_relationships.csv"]
        for f in rel_files:
            p = args.csv_dir / f
            if p.exists():
                loader.load_csv(p)
    finally:
        loader.close()

if __name__ == "__main__":
    main()
