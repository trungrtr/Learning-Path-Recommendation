import sys
import logging
from pathlib import Path

# Thêm thư mục 'src' vào sys.path để import
src_dir = Path(__file__).parent.parent
sys.path.insert(0, str(src_dir))

from supports_skill_pipeline.configs.pipeline_config import PipelineConfig
from supports_skill_pipeline.pipeline import SupportsSkillPipeline

def main():
    logging.basicConfig(level=logging.INFO)
    
    config = PipelineConfig()
    
    # Path mappings for execution
    base_dir = Path(r"d:\NCKH_2026\src\pipeline-data\src\esco-skill-mapping")
    
    # Set paths in config
    config.contract_dir = r"d:\NCKH_2026\src\pipeline-data\contract\hoc_phan"
    config.output.output_dir = r"d:\NCKH_2026\src\pipeline-data\src\esco-skill-mapping\data\data_support_skill"
    config.output.review_dir = r"d:\NCKH_2026\src\pipeline-data\src\esco-skill-mapping\data\data_support_skill\_review"
    
    # Cập nhật đường dẫn tuyệt đối cho index
    config.retrieval.faiss_index_path = str(base_dir / "data" / "esco_filtered" / "v1" / "faiss" / "esco_full.index")
    config.retrieval.faiss_metadata_path = str(base_dir / "data" / "esco_filtered" / "v1" / "faiss" / "esco_metadata.json")
    config.retrieval.bm25_index_path = str(base_dir / "data" / "esco_filtered" / "v1" / "bm25" / "bm25_corpus.pkl")
    
    # Sửa đường dẫn prompt
    config.llm.prompt_template_path = str(Path(__file__).parent / "prompts" / "support_concept_extraction.txt")

    pipeline = SupportsSkillPipeline(config)
    
    print("Starting supports_skill_pipeline for ALL courses...")
    pipeline.run_all(contract_dir=config.contract_dir)

if __name__ == "__main__":
    main()
