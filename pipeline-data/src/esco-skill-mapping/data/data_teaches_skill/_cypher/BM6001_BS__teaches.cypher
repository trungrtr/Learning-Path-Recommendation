MATCH (c:Course {code: "BM6001_BS"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/e5609f89-0daf-40bb-bd6b-94f5d7498131"})
MERGE (c)-[r:TEACHES_KNOWLEDGE]->(s)
SET r.confidence = 0.6991,
    r.evidence_ids = ["MAIN", null, "L33", "L34", "L20", "L35"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "BM6001_BS"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/2b92a5b2-6758-4ee3-9fb4-b6387a55cc8f"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.6886,
    r.evidence_ids = ["MAIN", null, "L31", "L35"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "BM6001_BS"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/27ed854c-15b8-4ba2-90e9-ae888a219703"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.6761,
    r.evidence_ids = ["MAIN", null, "L33", "L34", "L20", "L35"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "BM6001_BS"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/be727774-46d7-43d7-aee9-1a51b5cd8c71"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.6561,
    r.evidence_ids = ["MAIN", null, "L31", "L33", "L34"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "BM6001_BS"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/cdd8b6b2-2fd9-453c-8d62-8a1dc6efcd49"})
MERGE (c)-[r:TEACHES_KNOWLEDGE]->(s)
SET r.confidence = 0.6449,
    r.evidence_ids = ["MAIN", "L33", "L34"],
    r.method = "escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "BM6001_BS"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/628664ec-a63b-4486-8d65-02aba81c82a0"})
MERGE (c)-[r:TEACHES_KNOWLEDGE]->(s)
SET r.confidence = 0.6179,
    r.evidence_ids = ["MAIN", "L33", "L34", "L20", "L35"],
    r.method = "escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "SECONDARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "BM6001_BS"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/98a1dec3-8138-4f46-a596-5e2a83b884b9"})
MERGE (c)-[r:TEACHES_KNOWLEDGE]->(s)
SET r.confidence = 0.5840,
    r.evidence_ids = ["MAIN", null, "L34", "L20", "L35"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "SECONDARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "BM6001_BS"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/6360a934-cc87-4954-9656-b32db20592e3"})
MERGE (c)-[r:TEACHES_KNOWLEDGE]->(s)
SET r.confidence = 0.5832,
    r.evidence_ids = ["MAIN", null, "L33", "L34", "L20"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "SECONDARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "BM6001_BS"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/a846cb9e-c152-41e7-bd34-45e7ff941e3b"})
MERGE (c)-[r:TEACHES_KNOWLEDGE]->(s)
SET r.confidence = 0.5745,
    r.evidence_ids = ["MAIN", "L33", "L34", "L20", "L35"],
    r.method = "escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "SECONDARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "BM6001_BS"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/cbe2c304-1e7d-489a-97d9-a7d3e37a9db6"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.4877,
    r.evidence_ids = ["MAIN", null, "L33", "L34"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "OPTIONAL",
    r.schema_version = "3.0";

MATCH (c:Course {code: "BM6001_BS"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/ba1b0441-a6b8-4e57-8ccc-871012f63e42"})
MERGE (c)-[r:TEACHES_KNOWLEDGE]->(s)
SET r.confidence = 0.4108,
    r.evidence_ids = ["MAIN", null, "L34", "L20", "L35"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "OPTIONAL",
    r.schema_version = "3.0";

MATCH (c:Course {code: "BM6001_BS"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/d38871eb-b988-495e-8fca-345677b597a8"})
MERGE (c)-[r:TEACHES_KNOWLEDGE]->(s)
SET r.confidence = 0.3980,
    r.evidence_ids = ["MAIN", null, "L33", "L34", "L20"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "OPTIONAL",
    r.schema_version = "3.0";

MATCH (c:Course {code: "BM6001_BS"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/11c56452-fcec-4b00-9695-cca4728e5048"})
MERGE (c)-[r:TEACHES_KNOWLEDGE]->(s)
SET r.confidence = 0.3577,
    r.evidence_ids = ["MAIN", null, "L33", "L34", "L20", "L35"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "OPTIONAL",
    r.schema_version = "3.0";
