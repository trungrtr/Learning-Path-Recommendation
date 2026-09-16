"""Pipeline configuration — load YAML config cho supports_skill_pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class LLMConfig:
    """Cấu hình LLM cho Bước 2 (Concept Extraction)."""
    model: str = "gemini-3.1-flash-lite"
    temperature: float = 0.0
    max_concepts: int = 15
    prompt_template_path: str = "prompts/support_concept_extraction.txt"


@dataclass
class RetrievalConfig:
    """Cấu hình Retrieval cho Bước 3."""
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
    faiss_index_path: str = "data/esco_filtered/v1/faiss/esco_full.index"
    faiss_metadata_path: str = "data/esco_filtered/v1/faiss/esco_metadata.json"
    bm25_index_path: str = "data/esco_filtered/v1/bm25/bm25_corpus.pkl"
    escoxlmr_model: str = "jjzha/escoxlmr_skill_extraction"
    top_k_per_channel: int = 50


@dataclass
class FusionConfig:
    """Cấu hình RRF Fusion cho Bước 4."""
    rrf_k: int = 60
    top_n: int = 30


@dataclass
class RankingConfig:
    """Cấu hình Multi-signal Ranking cho Bước 5."""
    alpha: float = 1 / 3  # Weight cho RRF score
    beta: float = 1 / 3   # Weight cho ESCOXLM-R score
    gamma: float = 1 / 3  # Weight cho Evidence score
    top_k: int = 10


@dataclass
class OutputConfig:
    """Cấu hình output."""
    output_dir: str = "data/data_support_skill"
    review_dir: str = "data_support_skill/_review"
    write_cypher: bool = True


@dataclass
class CourseFilterConfig:
    """Lọc các học phần không mang kỹ năng chuyên ngành."""
    enabled: bool = True
    ignored_keywords: list[str] = field(default_factory=lambda: [
        "triết học", "chính trị", "mác - lênin", "mác-lênin", 
        "tư tưởng hồ chí minh", "đảng cộng sản", "chủ nghĩa xã hội", 
        "pháp luật đại cương", "kinh tế", "âm nhạc", 
        "giáo dục thể chất", "quốc phòng", "ngoại ngữ", "mỹ thuật", "mĩ thuật"
    ])


@dataclass
class PipelineConfig:
    """Cấu hình tổng thể cho supports_skill_pipeline."""
    contract_dir: str = "../../contract/hoc_phan"
    llm: LLMConfig = field(default_factory=LLMConfig)
    retrieval: RetrievalConfig = field(default_factory=RetrievalConfig)
    fusion: FusionConfig = field(default_factory=FusionConfig)
    ranking: RankingConfig = field(default_factory=RankingConfig)
    output: OutputConfig = field(default_factory=OutputConfig)
    course_filter: CourseFilterConfig = field(default_factory=CourseFilterConfig)
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_database: str = "neo4j"
    schema_version: str = "1.0"

    @classmethod
    def from_yaml(cls, yaml_path: str | Path) -> PipelineConfig:
        """Load config từ file YAML."""
        path = Path(yaml_path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")

        with open(path, "r", encoding="utf-8") as f:
            raw: dict[str, Any] = yaml.safe_load(f)

        config = cls()
        config.contract_dir = raw.get("contract_dir", config.contract_dir)
        config.neo4j_uri = raw.get("neo4j_uri", config.neo4j_uri)
        config.neo4j_database = raw.get("neo4j_database", config.neo4j_database)
        config.schema_version = raw.get("schema_version", config.schema_version)

        # LLM config
        if "llm" in raw:
            llm = raw["llm"]
            config.llm = LLMConfig(
                model=llm.get("model", config.llm.model),
                temperature=llm.get("temperature", config.llm.temperature),
                max_concepts=llm.get("max_concepts", config.llm.max_concepts),
                prompt_template_path=llm.get("prompt_template_path", config.llm.prompt_template_path),
            )

        # Retrieval config
        if "retrieval" in raw:
            ret = raw["retrieval"]
            config.retrieval = RetrievalConfig(
                embedding_model=ret.get("embedding_model", config.retrieval.embedding_model),
                faiss_index_path=ret.get("faiss_index_path", config.retrieval.faiss_index_path),
                faiss_metadata_path=ret.get("faiss_metadata_path", config.retrieval.faiss_metadata_path),
                bm25_index_path=ret.get("bm25_index_path", config.retrieval.bm25_index_path),
                escoxlmr_model=ret.get("escoxlmr_model", config.retrieval.escoxlmr_model),
                top_k_per_channel=ret.get("top_k_per_channel", config.retrieval.top_k_per_channel),
            )

        # Fusion config
        if "fusion" in raw:
            fus = raw["fusion"]
            config.fusion = FusionConfig(
                rrf_k=fus.get("rrf_k", config.fusion.rrf_k),
                top_n=fus.get("top_n", config.fusion.top_n),
            )

        # Ranking config
        if "ranking" in raw:
            rnk = raw["ranking"]
            config.ranking = RankingConfig(
                alpha=rnk.get("alpha", config.ranking.alpha),
                beta=rnk.get("beta", config.ranking.beta),
                gamma=rnk.get("gamma", config.ranking.gamma),
                top_k=rnk.get("top_k", config.ranking.top_k),
            )

        # Output config
        if "output" in raw:
            out = raw["output"]
            config.output = OutputConfig(
                output_dir=out.get("output_dir", config.output.output_dir),
                review_dir=out.get("review_dir", config.output.review_dir),
                write_cypher=out.get("write_cypher", config.output.write_cypher),
            )

        return config
