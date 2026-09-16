MATCH (c:Course {code: "IT6206"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/a47d194d-0ffd-4aaa-b695-fbbe0255000e"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.7378,
    r.evidence_ids = ["G1", "L1", "L2", "L3", "L08", "L09", "L10"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6206"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/20c920d4-7ff7-4676-ba61-3f04490d9416"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.7244,
    r.evidence_ids = ["G1", "L1", "L2", "L3", "L08"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6206"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/ed8de897-adbe-4f0e-b4d2-534953e64c72"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.7234,
    r.evidence_ids = ["L1", "L2", "L08", "L09", "L10"],
    r.method = "escoxlmr_skill+escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6206"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/3579208e-49b3-4ce4-98e7-20e41b1ce8d4"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.7206,
    r.evidence_ids = ["G1", "L1", "L2", "L3"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6206"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/9190d87f-9792-42e0-bb7f-64294a656bcd"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.7198,
    r.evidence_ids = ["L1", "L08", "L09", "L10"],
    r.method = "escoxlmr_skill+escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6206"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/03b9b491-fc9b-4868-914a-bf7cd47b5041"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.7182,
    r.evidence_ids = ["G1", "L1", "L2", "L3"],
    r.method = "escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6206"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/07e51c60-763a-4335-b4ec-70a15f66d328"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.7163,
    r.evidence_ids = ["G1", "L1", "L2", "L3"],
    r.method = "escoxlmr_skill+escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6206"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/31c69100-b612-4a61-8db5-fd314318854c"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.7158,
    r.evidence_ids = ["G1", "L1", "L2", "L3"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6206"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/7a8fb784-67fa-41e9-a75c-6b491d91f800"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.7114,
    r.evidence_ids = ["G1", "L2", "L3", "L10"],
    r.method = "escoxlmr_skill+escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6206"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/ca73ac82-867a-4afa-9732-834aebe896ff"})
MERGE (c)-[r:TEACHES_KNOWLEDGE]->(s)
SET r.confidence = 0.6979,
    r.evidence_ids = ["L2", "L3", "L08", "L09", "L10"],
    r.method = "escoxlmr_skill+escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";
