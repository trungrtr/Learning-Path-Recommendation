MATCH (c:Course {code: "IT6207"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/27ed854c-15b8-4ba2-90e9-ae888a219703"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.7385,
    r.evidence_ids = ["MAIN", "MT1", "MT2", "L1", "L2", "L3", "L08", "L09", "L10"],
    r.method = "escoxlmr_skill+escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6207"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/03b9b491-fc9b-4868-914a-bf7cd47b5041"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.7374,
    r.evidence_ids = ["MAIN", "MT2", "L1", "L2", "L3", "L08", "L09", "L10"],
    r.method = "escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6207"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/0e1fe34b-f4e7-4642-8c8b-5a05ac3438e5"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.7293,
    r.evidence_ids = ["MAIN", "L1", "L3", "L08", "L09"],
    r.method = "escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6207"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/1fcce318-3212-487a-ac07-4941bc85060d"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.7268,
    r.evidence_ids = ["MAIN", "MT2", "L1", "L08", "L09", "L10"],
    r.method = "escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6207"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/7e1f9657-ab4e-407c-842f-b846197060e3"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.7216,
    r.evidence_ids = ["MT1", "MT2", "L1", "L2", "L3", "L08", "L09"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6207"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/1b3fc0e0-c6f9-45fc-9c6e-14bbba662979"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.7207,
    r.evidence_ids = ["MAIN", "MT1", "MT2", "L2", "L3", "L07"],
    r.method = "escoxlmr_skill+escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6207"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/e207163b-7963-4c3e-9494-7a4bb000211b"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.7199,
    r.evidence_ids = ["MT2", "L1", "L07", "L08", "L09"],
    r.method = "escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6207"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/a47d194d-0ffd-4aaa-b695-fbbe0255000e"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.7179,
    r.evidence_ids = ["MT1", "MT2", "L2", "L07"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6207"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/b9bf9e17-ae47-417b-bbb1-e8b7c263ccac"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.7175,
    r.evidence_ids = ["MT2", "L2", "L3", "L07", "L08", "L09"],
    r.method = "escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6207"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/574257ea-7b64-4100-b7b6-e27c233fe143"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.7108,
    r.evidence_ids = ["MAIN", "MT1", "MT2", "L1", "L3"],
    r.method = "escoxlmr_skill+escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";
