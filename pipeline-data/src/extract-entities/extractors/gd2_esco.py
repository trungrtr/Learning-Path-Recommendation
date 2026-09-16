import sys
import logging
from typing import Dict, List, Any
import pandas as pd

from core.models import KyNangESCONode, NgheNghiepESCONode, Relationship
from .base import BaseExtractor
from core.config import ESCO_ZIP_PATH, ESCO_ROLES_CSV, BASE_DIR

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

try:
    from esco_extractor import ESCOExtractor
except ImportError:
    ESCOExtractor = None

logger = logging.getLogger(__name__)

class GD2EscoExtractor(BaseExtractor):
    def __init__(self):
        self.nodes = {
            "KyNangESCO": [],
            "NgheNghiepESCO": []
        }
        self.relationships = {
            "REQUIRES_SKILL": []
        }
        
    def extract_nodes(self) -> Dict[str, List[Any]]:
        return self.nodes

    def extract_relationships(self) -> Dict[str, List[Relationship]]:
        return self.relationships

    def run(self):
        from core.config import ESCO_SKILLS_CSV
        import pandas as pd
        
        if not ESCO_SKILLS_CSV.exists():
            logger.error(f"ESCO skills CSV not found: {ESCO_SKILLS_CSV}")
            return
            
        df = pd.read_csv(ESCO_SKILLS_CSV, dtype=str)
        df = df.fillna("")
        
        for _, row in df.iterrows():
            def parse_list(val):
                if not val:
                    return []
                return [v.strip() for v in str(val).split('\n') if v.strip()]
            
            def parse_scheme(val):
                if not val:
                    return []
                return [v.strip().rstrip(',') for v in str(val).split('\n') if v.strip()]
                
            self.nodes["KyNangESCO"].append(
                KyNangESCONode(
                    skill_uri=str(row.get("conceptUri", "")),
                    concept_type=str(row.get("conceptType", "")),
                    skill_type=str(row.get("skillType", "")),
                    reuse_level=str(row.get("reuseLevel", "")),
                    preferred_label=str(row.get("preferredLabel", "")),
                    alternative_labels=parse_list(row.get("altLabels", "")),
                    hidden_labels=parse_list(row.get("hiddenLabels", "")),
                    status=str(row.get("status", "")),
                    modified_date=str(row.get("modifiedDate", "")),
                    scope_note=str(row.get("scopeNote", "")),
                    definition=str(row.get("definition", "")),
                    in_scheme=parse_scheme(row.get("inScheme", "")),
                    description=str(row.get("description", "")),
                    uniskill_domain=str(row.get("uniskill_domain", "")),
                    domain_reason=str(row.get("domain_reason", ""))
                )
            )
        logger.info(f"Loaded {len(self.nodes['KyNangESCO'])} ESCO skills from CSV.")
