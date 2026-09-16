import sys
import logging
from pathlib import Path

# Thêm thư mục 'src' vào sys.path để import teaches_skill_pipeline_B như một package
src_dir = Path(__file__).parent.parent
sys.path.insert(0, str(src_dir))

from teaches_skill_pipeline_B.configs.pipeline_config import PipelineConfig
from teaches_skill_pipeline_B.pipeline import TeachesSkillPipeline

def main():
    logging.basicConfig(level=logging.INFO)
    
    config = PipelineConfig()
    
    # Path mappings for execution
    base_dir = Path(r"d:\NCKH_2026\src\pipeline-data\src\esco-skill-mapping")
    
    # Set paths in config
    config.contract_dir = r"d:\NCKH_2026\src\pipeline-data\contract"
    config.output.output_dir = r"d:\NCKH_2026\src\pipeline-data\src\esco-skill-mapping\data\data_teaches_B"
    
    # Cập nhật đường dẫn tuyệt đối cho index
    config.retrieval.faiss_index_path = str(base_dir / "data" / "esco_filtered" / "v1" / "faiss" / "esco_full.index")
    config.retrieval.faiss_metadata_path = str(base_dir / "data" / "esco_filtered" / "v1" / "faiss" / "esco_metadata.json")
    config.retrieval.bm25_index_path = str(base_dir / "data" / "esco_filtered" / "v1" / "bm25" / "bm25_corpus.pkl")
    
    pipeline = TeachesSkillPipeline(config)
    
    print("Starting pipeline for ALL courses...")
    pipeline.run_all()

if __name__ == "__main__":
    main()
