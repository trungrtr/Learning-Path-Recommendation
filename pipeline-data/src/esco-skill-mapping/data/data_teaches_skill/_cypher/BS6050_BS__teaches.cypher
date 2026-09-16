MATCH (c:Course {code: "BS6050_BS"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/a584a638-a2c0-4b3c-bdf3-a64f87225be9"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.7128,
    r.evidence_ids = ["MAIN", null],
    r.method = "escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "BS6050_BS"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/4d30ad07-9e39-4899-81dd-02b280f162f9"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.7125,
    r.evidence_ids = ["MAIN", null],
    r.method = "escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "BS6050_BS"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/af607e5e-4ba1-4e5f-a2a6-dc05806567c7"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.7103,
    r.evidence_ids = ["MAIN", null, "L16"],
    r.method = "escoxlmr_skill+escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "BS6050_BS"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/7a17d7ce-01a2-4746-bbcc-22ffe22fa16e"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.7035,
    r.evidence_ids = ["MAIN", null, "L12", "L16"],
    r.method = "escoxlmr_skill+escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "BS6050_BS"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/7af6e9e8-1e11-4c0b-b7c6-ac96bbbbc674"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.7016,
    r.evidence_ids = ["MAIN", null],
    r.method = "escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "BS6050_BS"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/12274664-b642-4945-b88f-d7787dc3c9dd"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.6982,
    r.evidence_ids = ["MAIN", null, "L16"],
    r.method = "escoxlmr_skill+escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "BS6050_BS"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/03b9b491-fc9b-4868-914a-bf7cd47b5041"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.6968,
    r.evidence_ids = ["MAIN", null, "L16"],
    r.method = "escoxlmr_skill+escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "BS6050_BS"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/574257ea-7b64-4100-b7b6-e27c233fe143"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.6821,
    r.evidence_ids = ["MAIN", null, "L12"],
    r.method = "escoxlmr_skill+escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "BS6050_BS"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/c32ad607-0c4d-4e34-b73f-668298f7bf13"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.6768,
    r.evidence_ids = ["MAIN", null],
    r.method = "escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "BS6050_BS"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/f715be1d-5fc4-49d3-82a5-0b8090d12849"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.6654,
    r.evidence_ids = ["MAIN", null, "L12", "L16"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "BS6050_BS"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/8696aff0-18c0-4ba6-a4d0-9a21861b3e5e"})
MERGE (c)-[r:TEACHES_KNOWLEDGE]->(s)
SET r.confidence = 0.6625,
    r.evidence_ids = ["MAIN", "L12"],
    r.method = "escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "BS6050_BS"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/7a8fb784-67fa-41e9-a75c-6b491d91f800"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.6587,
    r.evidence_ids = ["MAIN", null, "L16"],
    r.method = "escoxlmr_skill+escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "BS6050_BS"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/cdd8b6b2-2fd9-453c-8d62-8a1dc6efcd49"})
MERGE (c)-[r:TEACHES_KNOWLEDGE]->(s)
SET r.confidence = 0.6506,
    r.evidence_ids = ["MAIN", null, "L12", "L16"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "BS6050_BS"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/b216d9a2-7d4e-4312-8d05-e375f4ab44d8"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.6200,
    r.evidence_ids = ["MAIN", null],
    r.method = "escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "BS6050_BS"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/cd50d616-1f8b-481e-983f-68d2674ff82d"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.5980,
    r.evidence_ids = ["MAIN", null],
    r.method = "escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "SECONDARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "BS6050_BS"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/0cc9c234-f817-4f4c-908a-4d28fe3b0f4a"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.5721,
    r.evidence_ids = ["MAIN", null],
    r.method = "escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "SECONDARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "BS6050_BS"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/3f4dab51-572b-4e2c-85ef-3b4c3f7094e1"})
MERGE (c)-[r:TEACHES_KNOWLEDGE]->(s)
SET r.confidence = 0.5542,
    r.evidence_ids = ["MAIN", "L12"],
    r.method = "escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "SECONDARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "BS6050_BS"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/5da8018b-ae85-4cde-ad93-0394369018f3"})
MERGE (c)-[r:TEACHES_KNOWLEDGE]->(s)
SET r.confidence = 0.5501,
    r.evidence_ids = ["MAIN", "L12"],
    r.method = "escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "SECONDARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "BS6050_BS"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/fc4fcb4b-993f-4f2c-b158-c2171ec18ed8"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.5481,
    r.evidence_ids = ["MAIN", null, "L16"],
    r.method = "escoxlmr_skill+escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "SECONDARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "BS6050_BS"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/9a58cd26-58eb-4a1c-b1b6-64037fe9cfa1"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.5021,
    r.evidence_ids = ["MAIN", null, "L16"],
    r.method = "escoxlmr_skill+escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "OPTIONAL",
    r.schema_version = "3.0";

MATCH (c:Course {code: "BS6050_BS"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/e54ff029-1ce9-447d-a5b2-eb7283a23e6e"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.4540,
    r.evidence_ids = ["MAIN", null],
    r.method = "escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "OPTIONAL",
    r.schema_version = "3.0";
