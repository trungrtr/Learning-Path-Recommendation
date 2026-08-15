import os
from pathlib import Path

def load_neo4j_config(filepath: str | Path):
    """Load Neo4j config from the provided txt file into environment variables."""
    path = Path(filepath)
    if not path.exists():
        return
        
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ[key.strip()] = value.strip()

def get_neo4j_credentials():
    uri = os.getenv("NEO4J_URI", "")
    username = os.getenv("NEO4J_USERNAME", "")
    password = os.getenv("NEO4J_PASSWORD", "")
    database = os.getenv("NEO4J_DATABASE", "neo4j")
    return uri, username, password, database
