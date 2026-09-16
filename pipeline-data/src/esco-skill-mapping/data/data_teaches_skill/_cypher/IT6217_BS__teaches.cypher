MATCH (c:Course {code: "IT6217_BS"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/c3687b34-fe53-4db2-ad1b-5055a6c5b6fd"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.7003,
    r.evidence_ids = ["MAIN", "L17", "L19"],
    r.method = "escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6217_BS"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/89f6560b-2194-45c9-9ece-d33049a73eef"})
MERGE (c)-[r:TEACHES_KNOWLEDGE]->(s)
SET r.confidence = 0.6965,
    r.evidence_ids = ["MAIN", "L15"],
    r.method = "escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6217_BS"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/1b3fc0e0-c6f9-45fc-9c6e-14bbba662979"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.6907,
    r.evidence_ids = ["MAIN", "L15", "L17"],
    r.method = "escoxlmr_skill+escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6217_BS"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/c55caed2-de9e-4a25-819e-a0b0e83fba1b"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.6905,
    r.evidence_ids = ["MAIN", "L15", "L17"],
    r.method = "escoxlmr_skill+escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6217_BS"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/65e58886-bd1e-4c5b-8ca5-8d9b353c8aa1"})
MERGE (c)-[r:TEACHES_KNOWLEDGE]->(s)
SET r.confidence = 0.6877,
    r.evidence_ids = ["L15", "L17"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "SECONDARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6217_BS"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/78a74fd1-efc6-49dc-adb1-1b0fbe35c22c"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.6833,
    r.evidence_ids = ["MAIN", "L17"],
    r.method = "escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6217_BS"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/385479b7-5da5-4367-9763-0d15b41bb65b"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.6807,
    r.evidence_ids = ["MAIN", "L15", "L17"],
    r.method = "escoxlmr_skill+escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6217_BS"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/a47d194d-0ffd-4aaa-b695-fbbe0255000e"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.6806,
    r.evidence_ids = ["MAIN", "L15"],
    r.method = "escoxlmr_skill+escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6217_BS"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/c3e36d05-8ae8-447f-bb2b-6f9409f85389"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.6719,
    r.evidence_ids = ["MAIN", "L15", "L17"],
    r.method = "escoxlmr_skill+escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6217_BS"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/64db87c7-2360-4e20-88d3-d222402e477c"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.6561,
    r.evidence_ids = ["MAIN", "L15", "L17"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6217_BS"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/696e3b5b-8b61-45af-ae4c-3ab700f197ec"})
MERGE (c)-[r:TEACHES_KNOWLEDGE]->(s)
SET r.confidence = 0.6462,
    r.evidence_ids = ["MAIN", "L15"],
    r.method = "escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6217_BS"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/b105ec9b-0857-41d6-8d07-a83e58b73d90"})
MERGE (c)-[r:TEACHES_KNOWLEDGE]->(s)
SET r.confidence = 0.6395,
    r.evidence_ids = ["MAIN", "L13", "L15", "L17"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6217_BS"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/d54a1355-05c8-45eb-9c42-267d2cfcdf44"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.6310,
    r.evidence_ids = ["MAIN", "L17", "L19"],
    r.method = "escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6217_BS"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/234aeb8d-56c3-4531-9193-1c5e6a8d16cb"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.6197,
    r.evidence_ids = ["MAIN", "L17"],
    r.method = "escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6217_BS"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/f9670490-8aa4-4540-b121-d440a8294aab"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.6112,
    r.evidence_ids = ["MAIN", "L13", "L15"],
    r.method = "escoxlmr_skill+escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6217_BS"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/6e4f75b4-c60f-4623-a9ba-760c8245753b"})
MERGE (c)-[r:TEACHES_KNOWLEDGE]->(s)
SET r.confidence = 0.6027,
    r.evidence_ids = ["MAIN", "L15"],
    r.method = "escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6217_BS"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/2d6d4784-0992-48e7-b100-22d7229b3f0a"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.5857,
    r.evidence_ids = ["MAIN", "L15", "L17"],
    r.method = "escoxlmr_skill+escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "SECONDARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6217_BS"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/7b0d5000-00da-4864-b776-6de49a87a669"})
MERGE (c)-[r:TEACHES_KNOWLEDGE]->(s)
SET r.confidence = 0.5549,
    r.evidence_ids = ["MAIN", "L15"],
    r.method = "escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "SECONDARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6217_BS"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/1bba98a7-92b9-450b-9235-e0c905f8f3c4"})
MERGE (c)-[r:TEACHES_KNOWLEDGE]->(s)
SET r.confidence = 0.4696,
    r.evidence_ids = ["MAIN", "L15"],
    r.method = "escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "OPTIONAL",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6217_BS"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/c32ad607-0c4d-4e34-b73f-668298f7bf13"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.4633,
    r.evidence_ids = ["MAIN", "L15", "L17", "L19"],
    r.method = "escoxlmr_skill+escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "OPTIONAL",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6217_BS"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/21d2f96d-35f7-4e3f-9745-c533d2dd6e97"})
MERGE (c)-[r:TEACHES_KNOWLEDGE]->(s)
SET r.confidence = 0.4523,
    r.evidence_ids = ["MAIN", "L13"],
    r.method = "escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "OPTIONAL",
    r.schema_version = "3.0";
