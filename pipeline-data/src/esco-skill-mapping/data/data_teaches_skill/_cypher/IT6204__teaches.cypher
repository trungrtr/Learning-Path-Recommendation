MATCH (c:Course {code: "IT6204"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/8ff015a0-98ea-4d80-a23e-1f68110a919e"})
MERGE (c)-[r:TEACHES_KNOWLEDGE]->(s)
SET r.confidence = 0.7650,
    r.evidence_ids = ["MAIN", "MT1", "G1", "G2", "G3", "L1", "L3", "L12", "L14", "L16", "L18", "L19", "L20"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6204"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/84f58e3d-8669-4d83-8c1d-5dd1e73a654f"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.7548,
    r.evidence_ids = ["MAIN", "MT1", "G1", "G2", "L3", "L14", "L15", "L16", "L17", "L18", "L19"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6204"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/2857540c-180b-4208-9127-e94a01871966"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.7536,
    r.evidence_ids = ["MAIN", "MT1", "G1", "G2", "G3", "L1", "L3", "L12", "L14", "L15", "L16", "L20"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6204"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/12274664-b642-4945-b88f-d7787dc3c9dd"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.7495,
    r.evidence_ids = ["MAIN", "MT1", "G1", "G2", "G3", "L2", "L3", "L12", "L15", "L17", "L19", "L20"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6204"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/de0be6e8-644c-4cc9-9c8d-925dd98dda56"})
MERGE (c)-[r:TEACHES_KNOWLEDGE]->(s)
SET r.confidence = 0.7470,
    r.evidence_ids = ["MAIN", "MT1", "G1", "G2", "G3", "L3", "L12", "L17", "L20"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6204"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/a47d194d-0ffd-4aaa-b695-fbbe0255000e"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.7457,
    r.evidence_ids = ["MAIN", "MT1", "G1", "G2", "G3", "L1", "L3", "L12", "L14", "L15", "L16", "L19", "L20"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6204"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/ed8de897-adbe-4f0e-b4d2-534953e64c72"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.7440,
    r.evidence_ids = ["MAIN", "G1", "G2", "G3", "L1", "L3", "L12", "L14", "L16", "L17", "L20"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6204"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/7364cc39-b9c0-449f-9416-57723e2fd9c4"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.7429,
    r.evidence_ids = ["MAIN", "MT1", "G1", "G2", "G3", "L3", "L14", "L19", "L20"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6204"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/fae27053-8924-4bfd-b565-c9fe502044c9"})
MERGE (c)-[r:TEACHES_KNOWLEDGE]->(s)
SET r.confidence = 0.7419,
    r.evidence_ids = ["MAIN", "MT1", "G1", "G2", "G3", "L1", "L3", "L12", "L14", "L15", "L16", "L18", "L19", "L20"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6204"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/c544a9f3-5945-4b54-afed-de0697852817"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.7393,
    r.evidence_ids = ["MAIN", "MT1", "G1", "G2", "G3", "L12", "L14", "L16", "L17", "L18"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6204"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/1019423b-3368-4f83-b24f-19e5fa23e816"})
MERGE (c)-[r:TEACHES_KNOWLEDGE]->(s)
SET r.confidence = 0.7389,
    r.evidence_ids = ["MAIN", "MT1", "G1", "G2", "G3", "L3", "L12", "L14", "L19", "L20"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6204"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/2b7a79e5-84d8-4880-be66-3d9bb05bea17"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.7327,
    r.evidence_ids = ["MAIN", "MT1", "G1", "G2", "G3", "L3", "L12", "L14", "L19", "L20"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6204"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/b0096dc5-2e2d-4bc1-8172-05bf486c3968"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.7254,
    r.evidence_ids = ["MAIN", "MT1", "G1", "G2", "G3", "L3", "L12", "L14", "L16", "L17", "L18", "L19", "L20"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6204"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/a8797f21-1af0-4c5e-98ca-bf1442929363"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.7228,
    r.evidence_ids = ["MAIN", "MT1", "G1", "G3", "L1", "L2", "L12", "L14", "L15", "L16", "L17", "L18", "L20"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6204"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/fd33c66c-70c4-40e6-b87c-5495bd3bf26e"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.7222,
    r.evidence_ids = ["MAIN", "MT1", "G1", "G2", "G3", "L3", "L12", "L17", "L20"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6204"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/ce354460-500e-4eaa-8e95-8f243fcea3db"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.7222,
    r.evidence_ids = ["MAIN", "G1", "G2", "G3", "L1", "L3", "L12", "L14", "L15", "L16", "L20"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6204"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/48db96bf-3314-45c6-bad8-fdb6e20e5639"})
MERGE (c)-[r:TEACHES_KNOWLEDGE]->(s)
SET r.confidence = 0.7216,
    r.evidence_ids = ["MAIN", "MT1", "G1", "G2", "G3", "L12", "L14", "L16", "L17", "L18", "L19"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6204"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/2d6d4784-0992-48e7-b100-22d7229b3f0a"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.7188,
    r.evidence_ids = ["MAIN", "MT1", "G1", "G2", "G3", "L1", "L3", "L12", "L14", "L15", "L16", "L17", "L18", "L19", "L20"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6204"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/3bddfd7c-ab6d-40c2-883d-5e97fb7640ba"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.7171,
    r.evidence_ids = ["MAIN", "MT1", "G1", "G2", "G3", "L1", "L3", "L12", "L17", "L19", "L20"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6204"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/c4b1f326-224a-420a-b8b3-814a8f13b6cb"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.7161,
    r.evidence_ids = ["MAIN", "MT1", "G1", "G2", "G3", "L3", "L12", "L19", "L20"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6204"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/b011c8b4-76e1-4bbc-8bb9-1d205e7b618a"})
MERGE (c)-[r:TEACHES_KNOWLEDGE]->(s)
SET r.confidence = 0.7147,
    r.evidence_ids = ["MAIN", "MT1", "G1", "G2", "G3", "L12", "L14", "L16", "L17", "L18"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6204"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/78a74fd1-efc6-49dc-adb1-1b0fbe35c22c"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.7110,
    r.evidence_ids = ["MAIN", "MT1", "G1", "G2", "G3", "L3", "L12", "L14", "L16", "L17", "L18"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6204"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/b105ec9b-0857-41d6-8d07-a83e58b73d90"})
MERGE (c)-[r:TEACHES_KNOWLEDGE]->(s)
SET r.confidence = 0.7082,
    r.evidence_ids = ["MAIN", "G1", "G2", "G3", "L1", "L3", "L12", "L14", "L15", "L16", "L19", "L20"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6204"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/6360a934-cc87-4954-9656-b32db20592e3"})
MERGE (c)-[r:TEACHES_KNOWLEDGE]->(s)
SET r.confidence = 0.7000,
    r.evidence_ids = ["MAIN", "MT1", "G1", "G2", "G3", "L12", "L14", "L16", "L17", "L18"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6204"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/c3e36d05-8ae8-447f-bb2b-6f9409f85389"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.6990,
    r.evidence_ids = ["MAIN", "G1", "G2", "L14", "L15", "L16", "L17", "L18", "L19"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";
