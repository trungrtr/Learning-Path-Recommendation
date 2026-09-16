MATCH (c:Course {code: "IT6208"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/a47d194d-0ffd-4aaa-b695-fbbe0255000e"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.7311,
    r.evidence_ids = ["G1", "MT2", "L2", "L3", "L11", "L12"],
    r.method = "escoxlmr_skill+escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6208"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/1b3fc0e0-c6f9-45fc-9c6e-14bbba662979"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.7284,
    r.evidence_ids = ["G1", "MT2", "MT3", "L2", "L3", "L11"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6208"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/7e5147d1-60b1-4a68-804b-1f5cb0396b91"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.7279,
    r.evidence_ids = ["MT2", "MT3", "L2", "L11", "L12", "L13", "L14"],
    r.method = "escoxlmr_skill+escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6208"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/20c920d4-7ff7-4676-ba61-3f04490d9416"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.7226,
    r.evidence_ids = ["G1", "MT2", "L2", "L3"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6208"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/4d85b881-e490-4b4c-897a-2faa4ef53956"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.7202,
    r.evidence_ids = ["G1", "MT2", "MT3", "L2", "L3"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6208"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/3579208e-49b3-4ce4-98e7-20e41b1ce8d4"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.7185,
    r.evidence_ids = ["G1", "MT2", "MT3", "L2", "L3"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6208"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/7369f779-4b71-4aab-8836-48b69c676eec"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.7174,
    r.evidence_ids = ["G1", "MT2", "L2", "L3"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6208"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/7adb8473-bcc6-4ff8-9850-76d945d40092"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.7173,
    r.evidence_ids = ["G1", "MT2", "L2", "L3", "L11"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6208"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/0868eef3-2213-4572-9343-74931345a7d3"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.7166,
    r.evidence_ids = ["G1", "MT2", "MT3", "L2", "L3", "L11"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6208"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/17c9a790-5664-4673-8237-c4cf3c5a8da5"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.7130,
    r.evidence_ids = ["G1", "MT2", "L2", "L3", "L13", "L14"],
    r.method = "escoxlmr_skill+escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";
