MATCH (c:Course {code: "SC6019"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/edebd83d-35f6-4ed5-a940-6c203d178c01"})
MERGE (c)-[r:TEACHES_KNOWLEDGE]->(s)
SET r.confidence = 0.8050,
    r.evidence_ids = ["MAIN", "MT1", "MT2", "MT4", "L1", "L2", "L3", "L4", "L14", "L15", "L18", "L19", "L20", "L21", "L23", "L24", "L25"],
    r.method = "escoxlmr_skill+escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "SC6019"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/38d49d88-9069-467b-b29e-3cae739bdd4d"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.7923,
    r.evidence_ids = ["MAIN", "MT1", "MT2", "MT4", "L1", "L2", "L3", "L4", "L14", "L15", "L16", "L18", "L19", "L20", "L21", "L22", "L24", "L25"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "SC6019"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/382c11ed-20d5-4ae7-b60e-15fec527fa6c"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.7915,
    r.evidence_ids = ["MAIN", "MT1", "MT2", "MT4", "L1", "L2", "L3", "L4", "L14", "L15", "L16", "L18", "L19", "L20", "L21", "L22", "L24", "L25"],
    r.method = "escoxlmr_skill+escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "SC6019"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/b363bb5f-2c79-40af-94da-33e06f9dee9f"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.7804,
    r.evidence_ids = ["MAIN", "MT1", "MT2", "MT4", "L1", "L2", "L3", "L4", "L14", "L18", "L19", "L20", "L23", "L24", "L25"],
    r.method = "escoxlmr_skill+escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "SC6019"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/68ef0e4d-5542-4e64-84f4-752cce5a3c22"})
MERGE (c)-[r:TEACHES_KNOWLEDGE]->(s)
SET r.confidence = 0.7675,
    r.evidence_ids = ["MAIN", "MT1", "MT2", "MT4", "L1", "L2", "L4", "L14", "L15", "L16", "L18", "L19", "L20", "L21", "L22", "L25"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "SC6019"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/25f0ea33-b4a2-4f31-b7b4-7d20e827b180"})
MERGE (c)-[r:TEACHES_KNOWLEDGE]->(s)
SET r.confidence = 0.7643,
    r.evidence_ids = ["MAIN", "MT1", "MT2", "MT4", "L1", "L2", "L3", "L4", "L14", "L15", "L18", "L19", "L20", "L21", "L23", "L24", "L25"],
    r.method = "escoxlmr_skill+escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "SC6019"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/fecf8a0d-62c4-4e71-9b03-0f4fc2ad7bf5"})
MERGE (c)-[r:TEACHES_KNOWLEDGE]->(s)
SET r.confidence = 0.7596,
    r.evidence_ids = ["MAIN", "MT1", "MT2", "MT4", "L1", "L2", "L4", "L14", "L15", "L16", "L18", "L19", "L20", "L21", "L22", "L24", "L25"],
    r.method = "escoxlmr_skill+escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "SC6019"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/98301d4a-2cc3-439d-8d7f-0b6ac76302bb"})
MERGE (c)-[r:TEACHES_KNOWLEDGE]->(s)
SET r.confidence = 0.7519,
    r.evidence_ids = ["MAIN", "MT1", "MT2", "MT3", "MT4", "L1", "L2", "L3", "L4", "L14", "L15", "L16", "L19", "L20", "L21", "L22", "L25"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "SC6019"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/ecc4552a-92c5-4222-b18d-faf5ac841080"})
MERGE (c)-[r:TEACHES_KNOWLEDGE]->(s)
SET r.confidence = 0.7455,
    r.evidence_ids = ["MAIN", "MT1", "MT2", "MT3", "MT4", "L1", "L2", "L3", "L4", "L14", "L18", "L19", "L20", "L23", "L24", "L25"],
    r.method = "escoxlmr_skill+escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "SC6019"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/1b70a55d-b8a4-49fc-96c6-15ab4cff2522"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.7448,
    r.evidence_ids = ["MAIN", "MT1", "MT2", "MT3", "MT4", "L1", "L2", "L3", "L4", "L14", "L15", "L16", "L18", "L19", "L20", "L21", "L22", "L25"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "SC6019"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/a8d24a95-47b3-4f88-92e7-06600bcd3612"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.7391,
    r.evidence_ids = ["MAIN", "MT1", "MT2", "MT4", "L1", "L2", "L3", "L4", "L14", "L18", "L19", "L20", "L23", "L24", "L25"],
    r.method = "escoxlmr_skill+escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "SC6019"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/fbafa41f-cd05-4109-a649-8b44d306d779"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.7381,
    r.evidence_ids = ["MAIN", "MT1", "MT2", "L1", "L3", "L4", "L15", "L16", "L18", "L19", "L20", "L21", "L22", "L25"],
    r.method = "escoxlmr_skill+escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "SC6019"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/5be3d306-6cf1-4b49-aa1d-01651dd4ba4c"})
MERGE (c)-[r:TEACHES_KNOWLEDGE]->(s)
SET r.confidence = 0.7380,
    r.evidence_ids = ["MAIN", "MT1", "MT2", "MT3", "MT4", "L1", "L2", "L3", "L4", "L14", "L15", "L16", "L18", "L19", "L20", "L21", "L22", "L23", "L24", "L25"],
    r.method = "escoxlmr_skill+escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "SC6019"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/0760bfac-9a03-427a-ad84-ccd33a2f2ae8"})
MERGE (c)-[r:TEACHES_KNOWLEDGE]->(s)
SET r.confidence = 0.7370,
    r.evidence_ids = ["MAIN", "MT1", "MT2", "MT4", "L1", "L2", "L3", "L4", "L14", "L15", "L18", "L19", "L20", "L21", "L22", "L23", "L25"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "SC6019"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/143769cb-b61e-47d8-a61e-eedfbec1016c"})
MERGE (c)-[r:TEACHES_KNOWLEDGE]->(s)
SET r.confidence = 0.7306,
    r.evidence_ids = ["MAIN", "MT1", "MT2", "MT4", "L1", "L2", "L3", "L4", "L14", "L18", "L19", "L20", "L23", "L24", "L25"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "SC6019"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/2b92a5b2-6758-4ee3-9fb4-b6387a55cc8f"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.7250,
    r.evidence_ids = ["MAIN", "MT1", "MT2", "MT3", "MT4", "L1", "L2", "L3", "L4", "L14", "L15", "L18", "L19", "L20", "L21", "L23", "L24", "L25"],
    r.method = "escoxlmr_skill+escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "SC6019"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/e465a154-93f7-4973-9ce1-31659fe16dd2"})
MERGE (c)-[r:TEACHES_KNOWLEDGE]->(s)
SET r.confidence = 0.7240,
    r.evidence_ids = ["MAIN", "MT1", "MT2", "MT4", "L1", "L2", "L3", "L4", "L14", "L18", "L19", "L20", "L23", "L24", "L25"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "SC6019"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/8369c2d6-c100-4cf6-bd83-9668d8678433"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.7144,
    r.evidence_ids = ["MAIN", "MT1", "MT2", "MT4", "L1", "L2", "L3", "L4", "L14", "L18", "L19", "L20", "L23", "L24", "L25"],
    r.method = "escoxlmr_skill+escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "SECONDARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "SC6019"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/418a56a2-7cfc-4b6d-8cf5-5c2add99a849"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.7119,
    r.evidence_ids = ["MAIN", "MT1", "MT2", "MT4", "L1", "L2", "L3", "L4", "L14", "L18", "L19", "L20", "L23", "L24", "L25"],
    r.method = "escoxlmr_skill+escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "SC6019"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/5608d5a0-6d5e-43b7-be37-616501729bb4"})
MERGE (c)-[r:TEACHES_KNOWLEDGE]->(s)
SET r.confidence = 0.7048,
    r.evidence_ids = ["MAIN", "MT1", "MT2", "MT4", "L1", "L2", "L3", "L4", "L14", "L15", "L16", "L18", "L19", "L20", "L21", "L24", "L25"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "SC6019"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/a80fb090-63f4-4b05-83a5-2f090deb7757"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.6982,
    r.evidence_ids = ["MAIN", "MT1", "MT2", "MT4", "L1", "L2", "L3", "L4", "L14", "L15", "L16", "L18", "L19", "L20", "L21", "L22", "L24", "L25"],
    r.method = "escoxlmr_skill+escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "SC6019"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/54924a2c-daca-40d3-9716-4b38ceb04f38"})
MERGE (c)-[r:TEACHES_KNOWLEDGE]->(s)
SET r.confidence = 0.6745,
    r.evidence_ids = ["MAIN", "MT1", "MT2", "MT4", "L1", "L2", "L3", "L4", "L14", "L18", "L19", "L20", "L24", "L25"],
    r.method = "escoxlmr_skill+escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "SC6019"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/48db96bf-3314-45c6-bad8-fdb6e20e5639"})
MERGE (c)-[r:TEACHES_KNOWLEDGE]->(s)
SET r.confidence = 0.6713,
    r.evidence_ids = ["MAIN", "MT1", "MT2", "MT4", "L1", "L2", "L3", "L4", "L14", "L15", "L18", "L19", "L20", "L21", "L24", "L25"],
    r.method = "escoxlmr_skill+escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "SC6019"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/4216e465-7baa-4884-a241-54b197bb9278"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.6476,
    r.evidence_ids = ["MAIN", "MT1", "MT2", "MT4", "L1", "L2", "L3", "L4", "L14", "L15", "L18", "L19", "L20", "L21", "L24", "L25"],
    r.method = "escoxlmr_skill+escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "SECONDARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "SC6019"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/97bd1c21-66b2-4b7e-ad0f-e3cda590e378"})
MERGE (c)-[r:TEACHES_KNOWLEDGE]->(s)
SET r.confidence = 0.5596,
    r.evidence_ids = ["MAIN", "MT1", "MT2", "MT4", "L1", "L2", "L4", "L14", "L15", "L18", "L19", "L21", "L24", "L25"],
    r.method = "escoxlmr_skill+escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "OPTIONAL",
    r.schema_version = "3.0";
