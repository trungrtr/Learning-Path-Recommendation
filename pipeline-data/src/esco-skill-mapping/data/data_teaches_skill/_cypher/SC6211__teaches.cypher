MATCH (c:Course {code: "SC6211"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/5be3d306-6cf1-4b49-aa1d-01651dd4ba4c"})
MERGE (c)-[r:TEACHES_KNOWLEDGE]->(s)
SET r.confidence = 0.8390,
    r.evidence_ids = ["MAIN", "MT1", "MT2", "MT3", "L1", "L2", "L3", "L13", "L15"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "SC6211"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/5b9cde20-f1b9-4adc-bfb3-dbf70b14138d"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.7810,
    r.evidence_ids = ["MAIN", "MT1", "MT2", "MT3", "L1", "L2", "L3", "L15"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "SC6211"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/21d2f96d-35f7-4e3f-9745-c533d2dd6e97"})
MERGE (c)-[r:TEACHES_KNOWLEDGE]->(s)
SET r.confidence = 0.7732,
    r.evidence_ids = ["MAIN", "MT1", "MT2", "MT3", "L1", "L2", "L4"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "SC6211"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/25b291b5-8245-4d9d-b391-86a8a31d7109"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.6889,
    r.evidence_ids = ["MAIN", "MT1", "MT2", "MT3", "L1", "L2", "L15"],
    r.method = "escoxlmr_skill+escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "SC6211"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/4959697d-3a24-4f46-af0c-b752318e6c54"})
MERGE (c)-[r:TEACHES_KNOWLEDGE]->(s)
SET r.confidence = 0.6390,
    r.evidence_ids = ["MAIN", "MT1", "MT2", "MT3", "L1", "L2", "L3", "L4"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "SECONDARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "SC6211"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/69bbd53f-fbb0-4476-b4b2-ef7844464e28"})
MERGE (c)-[r:TEACHES_KNOWLEDGE]->(s)
SET r.confidence = 0.6222,
    r.evidence_ids = ["MAIN", "MT1", "MT2", "MT3", "L1", "L2", "L3", "L15"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "SECONDARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "SC6211"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/ccd0a1d9-afda-43d9-b901-96344886e14d"})
MERGE (c)-[r:TEACHES_KNOWLEDGE]->(s)
SET r.confidence = 0.5066,
    r.evidence_ids = ["MAIN", "MT1", "MT2", "MT3", "L1", "L2", "L4", "L15"],
    r.method = "escoxlmr_skill+escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "OPTIONAL",
    r.schema_version = "3.0";

MATCH (c:Course {code: "SC6211"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/d31fab87-2a7d-485c-b699-2901ca294b15"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.4510,
    r.evidence_ids = ["MAIN", "MT1", "MT2", "MT3", "L1", "L2", "L3", "L4", "L15"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "OPTIONAL",
    r.schema_version = "3.0";

MATCH (c:Course {code: "SC6211"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/b0096dc5-2e2d-4bc1-8172-05bf486c3968"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.4285,
    r.evidence_ids = ["MAIN", "MT1", "MT2", "MT3", "L1", "L2", "L3", "L4", "L13", "L15"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "OPTIONAL",
    r.schema_version = "3.0";

MATCH (c:Course {code: "SC6211"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/47b9bbcf-356c-4782-83a4-7f5a1b2b51a3"})
MERGE (c)-[r:TEACHES_KNOWLEDGE]->(s)
SET r.confidence = 0.4165,
    r.evidence_ids = ["MAIN", "MT1", "MT2", "MT3", "L1", "L2", "L4"],
    r.method = "escoxlmr_skill+escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "OPTIONAL",
    r.schema_version = "3.0";

MATCH (c:Course {code: "SC6211"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/2c4e11ef-da18-4e19-816b-e6bc19e12424"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.3876,
    r.evidence_ids = ["MAIN", "MT1", "MT2", "MT3", "L1", "L2", "L3", "L15"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "OPTIONAL",
    r.schema_version = "3.0";

MATCH (c:Course {code: "SC6211"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/9973a5a2-7822-4161-99e9-95c781eb63f8"})
MERGE (c)-[r:TEACHES_KNOWLEDGE]->(s)
SET r.confidence = 0.3782,
    r.evidence_ids = ["MAIN", "MT1", "MT2", "MT3", "L1", "L2", "L3"],
    r.method = "escoxlmr_skill+escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "OPTIONAL",
    r.schema_version = "3.0";

MATCH (c:Course {code: "SC6211"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/7d10fcb2-b368-48ab-996b-7c9fafcf68ed"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.3706,
    r.evidence_ids = ["MAIN", "MT1", "MT2", "MT3", "L1", "L2", "L3", "L4"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "OPTIONAL",
    r.schema_version = "3.0";

MATCH (c:Course {code: "SC6211"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/19a8293b-8e95-4de3-983f-77484079c389"})
MERGE (c)-[r:TEACHES_KNOWLEDGE]->(s)
SET r.confidence = 0.3615,
    r.evidence_ids = ["MAIN", "MT1", "MT2", "MT3", "L1", "L2"],
    r.method = "escoxlmr_skill+escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "OPTIONAL",
    r.schema_version = "3.0";
