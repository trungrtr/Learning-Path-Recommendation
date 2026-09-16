import json
import logging
from typing import Dict, List, Any
from core.models import Relationship
from .base import BaseExtractor
from core.config import M4_DIR, M5_DIR

logger = logging.getLogger(__name__)

class GD3MappingExtractor(BaseExtractor):
    def __init__(self):
        self.nodes = {
            "ConceptTag": []
        }
        self.relationships = {
            "TEACHES_SKILL": [],
            "TEACHES_KNOWLEDGE": [],
            "SUPPORTS_SKILL": [],
            "SUPPORTS_KNOWLEDGE": [],
            "HAS_CONCEPT": [],
            "EVIDENCE_FOR": []
        }
        self.concept_set = set() # To avoid duplicates
        
    def extract_nodes(self) -> Dict[str, List[Any]]:
        return self.nodes

    def extract_relationships(self) -> Dict[str, List[Relationship]]:
        return self.relationships

    def run(self):
        # We need to import ConceptTagNode here if we didn't already
        from core.models import ConceptTagNode
        self.ConceptTagNode = ConceptTagNode
        
        self._parse_mappings(M4_DIR, "TEACHES")
        self._parse_mappings(M5_DIR, "SUPPORTS")

    def _parse_mappings(self, data_dir, rel_prefix):
        if not data_dir.exists():
            logger.warning(f"Mapping dir not found: {data_dir}")
            return
            
        for hp_dir in data_dir.iterdir():
            if not hp_dir.is_dir() or hp_dir.name.startswith("_"):
                continue
                
            ma_hp = hp_dir.name
            if ma_hp.endswith("_BS"):
                ma_hp = ma_hp[:-3]
                
            summary_file = hp_dir / "_summary.json"
            if not summary_file.exists():
                # Fallback to old format if _summary.json is missing
                for json_file in hp_dir.glob("skill__*.json"):
                    try:
                        data = json.loads(json_file.read_text(encoding="utf-8"))
                        decision_obj = data.get("decision", {})
                        decision_status = str(decision_obj.get("decision_status", "")).lower()
                        if "accept" not in decision_status:
                            continue
                            
                        esco_concept = data.get("esco_concept", {})
                        esco_skill_type = str(esco_concept.get("skill_type", "")).lower()
                        skill_uri = esco_concept.get("uri", "")
                        if not skill_uri:
                            continue
                            
                        rel_type = f"{rel_prefix}_SKILL" if "skill" in esco_skill_type or "competence" in esco_skill_type else f"{rel_prefix}_KNOWLEDGE"
                        
                        evidence_ids = []
                        evidence_sources = []
                        matched_mentions = []
                        for ev in data.get("evidence", []):
                            source_id = ev.get("source_id")
                            if source_id:
                                evidence_ids.append(str(source_id))
                                evidence_sources.append(str(source_id))
                            if ev.get("meta") and ev["meta"].get("matched_mention"):
                                matched_mentions.append(str(ev["meta"]["matched_mention"]))
                                
                        llm_reasoning = str(decision_obj.get("llm_reasoning", ""))
                        
                        self.relationships[rel_type].append(
                            Relationship(
                                source_id=ma_hp,
                                target_id=skill_uri,
                                type=rel_type,
                                properties={
                                    "retrieval_score": str(decision_obj.get("cross_encoder_score", "")),
                                    "validation_confidence": str(decision_obj.get("confidence", "")),
                                    "evidence_ids": evidence_ids,
                                    "evidence_sources": evidence_sources,
                                    "matched_mentions": matched_mentions,
                                    "llm_reasoning": llm_reasoning
                                }
                            )
                        )
                    except Exception as e:
                        logger.error(f"Error parsing old JSON in {hp_dir.name}: {e}")
                
                # Also try to parse _concept_tags.json if it exists alongside old format
                self._parse_concept_tags(hp_dir, ma_hp, rel_prefix)
                continue

            try:
                data = json.loads(summary_file.read_text(encoding="utf-8"))
                
                # Hàm helper để xử lý từng danh sách
                def process_list(items, is_knowledge=False):
                    for item in items:
                        status = str(item.get("decision_status", item.get("review_status", ""))).lower()
                        if "accept" not in status:
                            continue
                            
                        skill_uri = item.get("esco_uri", "")
                        if not skill_uri:
                            continue
                            
                        rel_type = f"{rel_prefix}_KNOWLEDGE" if is_knowledge else f"{rel_prefix}_SKILL"
                        
                        reasoning = str(item.get("llm_reasoning", ""))
                        matched = []
                        if not reasoning and "support_concept_origin" in item:
                            origin_str = str(item.get("support_concept_origin", ""))
                            reasoning = f"Derived from concept tags: {origin_str}"
                            matched = [c.strip() for c in origin_str.split(";") if c.strip()]
                            
                        self.relationships[rel_type].append(
                            Relationship(
                                source_id=ma_hp,
                                target_id=skill_uri,
                                type=rel_type,
                                properties={
                                    "retrieval_score": str(item.get("cross_encoder_score", item.get("final_score", ""))),
                                    "validation_confidence": str(item.get("confidence", "")),
                                    "evidence_ids": [],
                                    "evidence_sources": [],
                                    "matched_mentions": matched,
                                    "llm_reasoning": reasoning
                                }
                            )
                        )
                
                # Hỗ trợ cả 2 tên trường: 'knowledge' và 'knowledges'
                process_list(data.get("skills", []), is_knowledge=False)
                process_list(data.get("knowledge", data.get("knowledges", [])), is_knowledge=True)
                
                self._parse_concept_tags(hp_dir, ma_hp, rel_prefix)
                
            except Exception as e:
                logger.error(f"Error parsing _summary.json in {hp_dir.name}: {e}")

    def _parse_concept_tags(self, hp_dir, ma_hp, rel_prefix):
        concept_file = hp_dir / "_concept_tags.json"
        if not concept_file.exists():
            return
            
        try:
            data = json.loads(concept_file.read_text(encoding="utf-8"))
            
            # Extract ConceptTag nodes
            for tag in data.get("concept_tags", []):
                normalized = tag.get("normalized", "")
                if normalized and normalized not in self.concept_set:
                    self.concept_set.add(normalized)
                    
                    loai = tag.get("loai")
                    if not loai or loai == "unknown":
                        loai = "direct_extraction" if rel_prefix == "TEACHES" else "reasoned"
                        
                    self.nodes["ConceptTag"].append(
                        self.ConceptTagNode(
                            normalized=normalized,
                            text=tag.get("text", ""),
                            loai=loai
                        )
                    )
                    
            # Extract HAS_CONCEPT relationships
            for edge in data.get("has_concept_edges", []):
                concept_tag = edge.get("concept_tag")
                if concept_tag:
                    self.relationships["HAS_CONCEPT"].append(
                        Relationship(
                            source_id=ma_hp,
                            target_id=concept_tag,
                            type="HAS_CONCEPT",
                            properties={"role": str(edge.get("role", "unknown"))}
                        )
                    )
                    
            # Extract EVIDENCE_FOR relationships
            for edge in data.get("evidence_for_edges", []):
                concept_tag = edge.get("concept_tag")
                esco_uri = edge.get("esco_uri")
                if concept_tag and esco_uri:
                    self.relationships["EVIDENCE_FOR"].append(
                        Relationship(
                            source_id=concept_tag,
                            target_id=esco_uri,
                            type="EVIDENCE_FOR",
                            properties={
                                "confidence": str(edge.get("confidence", "")),
                                "pipeline_source": str(edge.get("pipeline_source", f"{rel_prefix.lower()}_pipeline"))
                            }
                        )
                    )
        except Exception as e:
            logger.error(f"Error parsing _concept_tags.json in {hp_dir.name}: {e}")
