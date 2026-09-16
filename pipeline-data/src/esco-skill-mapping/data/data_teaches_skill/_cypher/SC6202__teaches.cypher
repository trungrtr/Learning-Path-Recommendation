MATCH (c:Course {code: "SC6202"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/03b9b491-fc9b-4868-914a-bf7cd47b5041"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.7578,
    r.evidence_ids = ["MAIN", "MT1", "MT2", "MT3", "L1", "L2", "L09", "L10", "L12"],
    r.method = "escoxlmr_skill+escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "SC6202"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/7e5147d1-60b1-4a68-804b-1f5cb0396b91"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.7549,
    r.evidence_ids = ["MAIN", "MT1", "MT2", "MT3", "L1", "L2", "L09", "L10", "L12", "L13"],
    r.method = "escoxlmr_skill+escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "SC6202"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/31c69100-b612-4a61-8db5-fd314318854c"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.7548,
    r.evidence_ids = ["MAIN", "MT1", "MT2", "MT3", "L1", "L2", "L09", "L10", "L11", "L12", "L13", "L16"],
    r.method = "escoxlmr_skill+escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "SC6202"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/118efbcd-8fc5-4668-81d1-c383a0d16070"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.7342,
    r.evidence_ids = ["MAIN", "MT1", "MT2", "MT3", "L1", "L2", "L10", "L12"],
    r.method = "escoxlmr_skill+escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "SC6202"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/3cfa46e9-b7da-44ac-b09e-9596dffe0425"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.7327,
    r.evidence_ids = ["MAIN", "MT1", "MT2", "MT3", "L2", "L09", "L10", "L16"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "SC6202"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/07e51c60-763a-4335-b4ec-70a15f66d328"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.7307,
    r.evidence_ids = ["MAIN", "MT1", "MT2", "MT3", "L1", "L2", "L12"],
    r.method = "escoxlmr_skill+escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "SC6202"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/7a8fb784-67fa-41e9-a75c-6b491d91f800"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.7285,
    r.evidence_ids = ["MAIN", "MT1", "MT2", "MT3", "L1", "L2", "L09", "L10", "L12"],
    r.method = "escoxlmr_skill+escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "SC6202"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/b9f16465-56a9-426b-a047-0f9f1f95ec92"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.7266,
    r.evidence_ids = ["MAIN", "MT1", "MT2", "MT3", "L1", "L2", "L12", "L13"],
    r.method = "escoxlmr_skill+escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "SC6202"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/d3eccb86-f02d-4950-bfbd-20b9510774a1"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.7203,
    r.evidence_ids = ["MAIN", "MT1", "MT2", "MT3", "L2", "L09", "L10", "L16"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "SC6202"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/1dd23dba-dd00-45ab-abf4-642902538317"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.7196,
    r.evidence_ids = ["MAIN", "MT1", "MT2", "MT3", "L1", "L2", "L09", "L10", "L16"],
    r.method = "escoxlmr_skill+escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "SC6202"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/744442ac-c157-4350-8be0-ce454df4f5c5"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.7059,
    r.evidence_ids = ["MAIN", "MT1", "MT2", "MT3", "L1", "L2", "L09", "L10", "L12"],
    r.method = "escoxlmr_skill+escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "SC6202"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/75b30aeb-34c0-40f4-b77d-271d75a98b14"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.7005,
    r.evidence_ids = ["MAIN", "MT1", "MT3", "L2", "L09", "L10", "L16"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "SC6202"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/98a1dec3-8138-4f46-a596-5e2a83b884b9"})
MERGE (c)-[r:TEACHES_KNOWLEDGE]->(s)
SET r.confidence = 0.6986,
    r.evidence_ids = ["MAIN", "MT1", "MT2", "MT3", "L1", "L2", "L12"],
    r.method = "escoxlmr_skill+escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "SC6202"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/2b7a79e5-84d8-4880-be66-3d9bb05bea17"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.6983,
    r.evidence_ids = ["MAIN", "MT1", "MT2", "MT3", "L2", "L10", "L11", "L12", "L13"],
    r.method = "escoxlmr_skill+escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "SC6202"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/0823ccef-813f-4f22-afef-ac0d68615e8f"})
MERGE (c)-[r:TEACHES_KNOWLEDGE]->(s)
SET r.confidence = 0.6979,
    r.evidence_ids = ["MAIN", "MT1", "L1", "L11", "L12", "L13", "L15"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "SC6202"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/0760bfac-9a03-427a-ad84-ccd33a2f2ae8"})
MERGE (c)-[r:TEACHES_KNOWLEDGE]->(s)
SET r.confidence = 0.6965,
    r.evidence_ids = ["MAIN", "MT1", "MT2", "MT3", "L1", "L09", "L10", "L11", "L12", "L13"],
    r.method = "escoxlmr_skill+escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "SC6202"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/25b291b5-8245-4d9d-b391-86a8a31d7109"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.6941,
    r.evidence_ids = ["MAIN", "MT1", "L2", "L09", "L10", "L11", "L12", "L13", "L16"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "SC6202"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/1a4cc54f-1e53-442b-a6d2-1682dc8ef8f9"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.6893,
    r.evidence_ids = ["MAIN", "MT1", "MT2", "MT3", "L1", "L2", "L09", "L10", "L12"],
    r.method = "escoxlmr_skill+escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "SC6202"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/6360a934-cc87-4954-9656-b32db20592e3"})
MERGE (c)-[r:TEACHES_KNOWLEDGE]->(s)
SET r.confidence = 0.6703,
    r.evidence_ids = ["MT1", "MT2", "MT3", "L1", "L12", "L13"],
    r.method = "escoxlmr_skill+escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "SC6202"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/7482a123-e801-48de-9733-262125671410"})
MERGE (c)-[r:TEACHES_KNOWLEDGE]->(s)
SET r.confidence = 0.6683,
    r.evidence_ids = ["MAIN", "MT1", "L1", "L2", "L09", "L10", "L11", "L12", "L13", "L16"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "SC6202"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/1d86f05e-e9cc-40ce-99d8-2b21cc71b16b"})
MERGE (c)-[r:TEACHES_KNOWLEDGE]->(s)
SET r.confidence = 0.6571,
    r.evidence_ids = ["MAIN", "MT2", "MT3", "L2", "L09", "L10", "L15"],
    r.method = "escoxlmr_skill+escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "SC6202"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/9e06bac6-6b91-48ca-8b7d-c1f48cdecd7c"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.6504,
    r.evidence_ids = ["MAIN", "MT1", "MT2", "MT3", "L1", "L2", "L09", "L10", "L12"],
    r.method = "escoxlmr_skill+escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "SC6202"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/54924a2c-daca-40d3-9716-4b38ceb04f38"})
MERGE (c)-[r:TEACHES_KNOWLEDGE]->(s)
SET r.confidence = 0.6397,
    r.evidence_ids = ["MAIN", "MT1", "MT2", "L2", "L09", "L10", "L11", "L12", "L13", "L16"],
    r.method = "escoxlmr_skill+escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "SC6202"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/21d2f96d-35f7-4e3f-9745-c533d2dd6e97"})
MERGE (c)-[r:TEACHES_KNOWLEDGE]->(s)
SET r.confidence = 0.4870,
    r.evidence_ids = ["MAIN", "L11", "L12", "L13"],
    r.method = "escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "OPTIONAL",
    r.schema_version = "3.0";

MATCH (c:Course {code: "SC6202"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/2c4e11ef-da18-4e19-816b-e6bc19e12424"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.4545,
    r.evidence_ids = ["MAIN", "MT2", "MT3", "L1", "L09", "L10", "L11", "L12", "L13"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "OPTIONAL",
    r.schema_version = "3.0";
