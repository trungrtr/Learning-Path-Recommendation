import logging
from pathlib import Path
import pandas as pd
from neo4j import GraphDatabase

from pipeline.neo4j_importer.cypher_queries import CONSTRAINTS, QUERIES

LOGGER = logging.getLogger(__name__)

class Neo4jLoader:
    def __init__(self, uri, username, password, database="neo4j"):
        self.uri = uri
        self.username = username
        self.password = password
        self.database = database
        self.driver = GraphDatabase.driver(self.uri, auth=(self.username, self.password))

    def close(self):
        self.driver.close()

    def create_constraints(self):
        with self.driver.session(database=self.database) as session:
            for constraint in CONSTRAINTS:
                LOGGER.info(f"Running constraint: {constraint}")
                try:
                    session.run(constraint)
                except Exception as e:
                    LOGGER.warning(f"Constraint failed (might already exist): {e}")

    def load_csv(self, file_path: Path, batch_size=1000):
        filename = file_path.name
        if filename not in QUERIES:
            LOGGER.warning(f"No cypher query found for {filename}, skipping.")
            return

        query = QUERIES[filename]
        LOGGER.info(f"Loading {filename} into Neo4j...")
        
        try:
            df = pd.read_csv(file_path)
            # Replace NaNs with None for Neo4j
            df = df.where(pd.notnull(df), None)
            records = df.to_dict('records')
            
            with self.driver.session(database=self.database) as session:
                for i in range(0, len(records), batch_size):
                    batch = records[i:i+batch_size]
                    
                    # For APOC dynamic relationships, we might need a workaround if APOC is not installed
                    # AuraDB usually has APOC core.
                    if filename == "entity_relationships.csv":
                        # We must group by relationship type and run separate queries because we can't parameterize rel type natively without APOC
                        # But APOC is used in the query. We will just pass the batch.
                        pass
                        
                    session.run(query, batch=batch)
            LOGGER.info(f"Successfully loaded {len(records)} records from {filename}")
        except Exception as e:
            LOGGER.error(f"Failed to load {filename}: {e}")
