MATCH (c:Course {code: "IT6205"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/a47d194d-0ffd-4aaa-b695-fbbe0255000e"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.7062,
    r.evidence_ids = ["G2", "L1", "L2"],
    r.method = "escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6205"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/d15ba5cb-9212-4a90-85af-2c560da59925"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.7049,
    r.evidence_ids = ["L1", "L2"],
    r.method = "escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6205"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/2c28fc20-8a60-4311-8899-5ef8729c05b3"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.7037,
    r.evidence_ids = ["L1"],
    r.method = "escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6205"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/7364cc39-b9c0-449f-9416-57723e2fd9c4"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.7037,
    r.evidence_ids = ["L1"],
    r.method = "escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6205"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/a8d24a95-47b3-4f88-92e7-06600bcd3612"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.7036,
    r.evidence_ids = ["L2"],
    r.method = "escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6205"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/4d85b881-e490-4b4c-897a-2faa4ef53956"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.7030,
    r.evidence_ids = ["G2", "L2"],
    r.method = "escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6205"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/3d3ee5c3-4286-457f-9f76-1704011f7e11"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.7019,
    r.evidence_ids = ["L2"],
    r.method = "escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6205"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/1b3fc0e0-c6f9-45fc-9c6e-14bbba662979"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.7004,
    r.evidence_ids = ["G2", "L2"],
    r.method = "escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6205"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/71c2f41e-14de-4b23-82ad-5dbcd54ba5b0"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.7000,
    r.evidence_ids = ["G2"],
    r.method = "escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6205"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/b9bf9e17-ae47-417b-bbb1-e8b7c263ccac"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.6987,
    r.evidence_ids = ["L2"],
    r.method = "escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";
