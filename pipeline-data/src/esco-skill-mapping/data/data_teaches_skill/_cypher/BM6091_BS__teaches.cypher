MATCH (c:Course {code: "BM6091_BS"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/fafe0b9d-dbd9-46bd-b770-26299539ce66"})
MERGE (c)-[r:TEACHES_KNOWLEDGE]->(s)
SET r.confidence = 0.6286,
    r.evidence_ids = ["MAIN", null, "L27", "L32", "L36", "L37"],
    r.method = "escoxlmr_skill+escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "SECONDARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "BM6091_BS"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/f5dd06b8-5d17-4932-9d03-957d0c4f5051"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.6161,
    r.evidence_ids = ["MAIN", null, "L22", "L23", "L24", "L27", "L30", "L32", "L35", "L36", "L37", "L38"],
    r.method = "escoxlmr_skill+escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "OPTIONAL",
    r.schema_version = "3.0";

MATCH (c:Course {code: "BM6091_BS"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/7f0b1a66-ebaf-4c8a-b606-4c1844eb692e"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.5425,
    r.evidence_ids = ["MAIN", null, "L22", "L24", "L32", "L36", "L37", "L38"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "OPTIONAL",
    r.schema_version = "3.0";
