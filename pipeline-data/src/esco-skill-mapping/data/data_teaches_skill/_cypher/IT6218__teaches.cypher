MATCH (c:Course {code: "IT6218"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/7369f779-4b71-4aab-8836-48b69c676eec"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.8289,
    r.evidence_ids = ["MAIN", "MT1", "MT2", "L1", "L2", "L3", "L10", "L11", "L12", "L13", "L14", "L15", "L16", "L17", "L18"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6218"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/ab1e97ed-2319-4293-a8b7-072d2648822f"})
MERGE (c)-[r:TEACHES_KNOWLEDGE]->(s)
SET r.confidence = 0.7965,
    r.evidence_ids = ["MAIN", "MT1", "MT2", "L1", "L2", "L3", "L10", "L11", "L12", "L13", "L14", "L15", "L16", "L17", "L18"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6218"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/84f58e3d-8669-4d83-8c1d-5dd1e73a654f"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.7655,
    r.evidence_ids = ["MAIN", "MT1", "MT2", "L1", "L2", "L3", "L10", "L11", "L12", "L13", "L14", "L15", "L16", "L17", "L18"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6218"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/4463a721-69f3-413d-8321-43e3af13a4f1"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.7554,
    r.evidence_ids = ["MAIN", "MT1", "MT2", "L1", "L2", "L3", "L10", "L11", "L12", "L13", "L14", "L15", "L16", "L17", "L18"],
    r.method = "escoxlmr_skill+escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6218"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/29fb0fb5-dfc4-4098-ac9b-3a712000f48f"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.7551,
    r.evidence_ids = ["MAIN", "MT1", "MT2", "L1", "L2", "L3", "L10", "L11", "L12", "L13", "L14", "L15", "L16", "L17", "L18"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6218"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/75f839c2-fd9a-4ad3-8921-6e734608568d"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.7465,
    r.evidence_ids = ["MAIN", "MT1", "MT2", "L1", "L2", "L3", "L10", "L11", "L12", "L13", "L14", "L15", "L16", "L17", "L18"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6218"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/ec85cc63-4e24-4631-bf92-8789db2605c0"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.7406,
    r.evidence_ids = ["MAIN", "MT1", "MT2", "L1", "L2", "L3", "L10", "L11", "L12", "L13", "L14", "L15", "L16", "L17", "L18"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6218"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/64db87c7-2360-4e20-88d3-d222402e477c"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.7333,
    r.evidence_ids = ["MAIN", "MT1", "MT2", "L1", "L2", "L3", "L10", "L11", "L12", "L13", "L14", "L15", "L16", "L17", "L18"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6218"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/76ef6ed3-1658-4a1a-9593-204d799c6d0c"})
MERGE (c)-[r:TEACHES_KNOWLEDGE]->(s)
SET r.confidence = 0.7332,
    r.evidence_ids = ["MAIN", "MT1", "MT2", "L1", "L2", "L3", "L10", "L11", "L12", "L13", "L14", "L15", "L16", "L17", "L18"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6218"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/9ef0f3a0-9ce2-4ef1-a987-0366b5cb2dbe"})
MERGE (c)-[r:TEACHES_KNOWLEDGE]->(s)
SET r.confidence = 0.7325,
    r.evidence_ids = ["MAIN", "MT1", "MT2", "L1", "L2", "L3", "L10", "L11", "L12", "L13", "L14", "L15", "L16", "L17", "L18"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6218"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/9ba8fd27-275d-4bad-8c48-f668aa99a578"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.7305,
    r.evidence_ids = ["MAIN", "MT1", "MT2", "L1", "L2", "L3", "L10", "L11", "L12", "L13", "L14", "L15", "L16", "L17", "L18"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6218"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/6c08403c-a5bb-4868-b8c2-b7d039c0e511"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.7280,
    r.evidence_ids = ["MAIN", "MT1", "MT2", "L1", "L2", "L3", "L10", "L11", "L12", "L13", "L14", "L15", "L16", "L17", "L18"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6218"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/d6cdef49-b669-4507-91d1-3f959cf98e47"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.7271,
    r.evidence_ids = ["MAIN", "MT1", "MT2", "L1", "L2", "L3", "L10", "L11", "L12", "L13", "L14", "L15", "L16", "L17", "L18"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6218"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/43ae58b9-5e56-4524-b45a-b422777a0576"})
MERGE (c)-[r:TEACHES_KNOWLEDGE]->(s)
SET r.confidence = 0.7253,
    r.evidence_ids = ["MAIN", "MT1", "MT2", "L1", "L2", "L3", "L10", "L11", "L12", "L13", "L14", "L15", "L16", "L17", "L18"],
    r.method = "escoxlmr_skill+escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6218"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/ab67fbfb-0ca7-4345-8bf6-af8f59480212"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.7215,
    r.evidence_ids = ["MAIN", "MT1", "MT2", "L1", "L2", "L3", "L10", "L11", "L12", "L13", "L14", "L15", "L16", "L17", "L18"],
    r.method = "escoxlmr_skill+escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6218"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/7e796b51-49d7-4e73-95af-2e7323763f15"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.7110,
    r.evidence_ids = ["MAIN", "MT1", "MT2", "L1", "L2", "L3", "L10", "L11", "L12", "L13", "L14", "L15", "L16", "L17", "L18"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6218"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/9cf681c7-89ec-470c-b651-7fe03786f586"})
MERGE (c)-[r:TEACHES_KNOWLEDGE]->(s)
SET r.confidence = 0.6964,
    r.evidence_ids = ["MAIN", "MT1", "MT2", "L1", "L2", "L3", "L10", "L11", "L12", "L13", "L14", "L15", "L16", "L17", "L18"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6218"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/e819cc1e-09d9-47f2-b418-93972852daef"})
MERGE (c)-[r:TEACHES_KNOWLEDGE]->(s)
SET r.confidence = 0.6497,
    r.evidence_ids = ["MAIN", "MT1", "MT2", "L1", "L2", "L3", "L10", "L11", "L12", "L13", "L14", "L15", "L16", "L17", "L18"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "SECONDARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6218"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/022dc430-872a-473a-9cf4-fed4895e58ad"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.6212,
    r.evidence_ids = ["MAIN", "MT1", "MT2", "L1", "L2", "L3", "L10", "L11", "L12", "L13", "L14", "L15", "L16", "L17", "L18"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "SECONDARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6218"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/70de94f5-9575-4edd-bca7-c797b023b9d6"})
MERGE (c)-[r:TEACHES_KNOWLEDGE]->(s)
SET r.confidence = 0.5931,
    r.evidence_ids = ["MAIN", "MT2", "L1", "L2", "L3", "L10", "L11", "L12", "L13", "L14", "L15", "L16", "L17", "L18"],
    r.method = "escoxlmr_skill+escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "OPTIONAL",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6218"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/f5ac9226-0ace-4d34-a1c3-7b3845834a98"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.4080,
    r.evidence_ids = ["MT2", "L3", "L10", "L11", "L12", "L13", "L14", "L15", "L16", "L17", "L18"],
    r.method = "escoxlmr_skill+escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "OPTIONAL",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6218"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/a4e31589-3632-4926-91d0-15b889c90b9b"})
MERGE (c)-[r:TEACHES_KNOWLEDGE]->(s)
SET r.confidence = 0.3461,
    r.evidence_ids = ["L10", "L11", "L12", "L13", "L14", "L15", "L16", "L17", "L18"],
    r.method = "escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "OPTIONAL",
    r.schema_version = "3.0";
