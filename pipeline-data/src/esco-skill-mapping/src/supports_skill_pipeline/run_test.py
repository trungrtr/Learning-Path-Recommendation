import sys
import logging
from pathlib import Path
import asyncio

# Thêm thư mục 'src' vào sys.path để import
src_dir = Path(__file__).parent.parent
sys.path.insert(0, str(src_dir))

from supports_skill_pipeline.configs.pipeline_config import PipelineConfig
from supports_skill_pipeline.pipeline import SupportsSkillPipeline

async def main():
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
    
    import random
    hoc_phan_dir = Path(config.contract_dir)
    all_course_dirs = [d.name for d in hoc_phan_dir.iterdir() if d.is_dir() and not d.name.startswith("_")]
    
    if not all_course_dirs:
        print("No courses found to test.")
        return
        
    courses_to_test = random.sample(all_course_dirs, min(5, len(all_course_dirs)))
    print(f"Testing supports_skill_pipeline for 5 random courses: {courses_to_test}...")
    
    for course_code in courses_to_test:
        print(f"\n--- Testing course: {course_code} ---")
        await pipeline.run_course(course_code=course_code, contract_dir=config.contract_dir)

if __name__ == "__main__":
    asyncio.run(main())
