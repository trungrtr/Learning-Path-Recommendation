import logging
from core.config import CSV_OUTPUT_DIR
from core.csv_writer import write_nodes_csv, write_relationships_csv
from extractors.gd1_contract import GD1ContractExtractor
from extractors.gd2_esco import GD2EscoExtractor
from extractors.gd3_mapping import GD3MappingExtractor

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

def main():
    logger.info("Starting entity extraction pipeline...")
    
    extractors = [
        ("GD1 (Contract)", GD1ContractExtractor()),
        ("GD2 (ESCO)", GD2EscoExtractor()),
        ("GD3 (Mapping)", GD3MappingExtractor())
    ]
    
    all_nodes = {}
    all_relationships = {}
    
    for name, ext in extractors:
        logger.info(f"Running extractor: {name}")
        ext.run()
        
        for node_type, nodes in ext.extract_nodes().items():
            if node_type not in all_nodes:
                all_nodes[node_type] = []
            all_nodes[node_type].extend(nodes)
            
        for rel_type, rels in ext.extract_relationships().items():
            if rel_type not in all_relationships:
                all_relationships[rel_type] = []
            all_relationships[rel_type].extend(rels)
            
    logger.info("Writing output to CSV files...")
    for node_type, nodes in all_nodes.items():
        if nodes:
            out_file = CSV_OUTPUT_DIR / f"{node_type}.csv"
            write_nodes_csv(out_file, nodes)
            logger.info(f"Wrote {len(nodes)} {node_type} nodes to {out_file.name}")
            
    for rel_type, rels in all_relationships.items():
        if rels:
            out_file = CSV_OUTPUT_DIR / f"rel_{rel_type}.csv"
            write_relationships_csv(out_file, rels)
            logger.info(f"Wrote {len(rels)} {rel_type} relationships to {out_file.name}")
            
    logger.info("Pipeline completed successfully!")

if __name__ == "__main__":
    main()
