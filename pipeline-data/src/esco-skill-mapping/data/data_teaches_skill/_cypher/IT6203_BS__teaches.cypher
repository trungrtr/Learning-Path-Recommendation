MATCH (c:Course {code: "IT6203_BS"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/7d35602d-bc94-4975-aa7c-f4e8e05ce8e0"})
MERGE (c)-[r:TEACHES_KNOWLEDGE]->(s)
SET r.confidence = 0.7167,
    r.evidence_ids = ["MAIN", "L09", "L12", "L13", "L14"],
    r.method = "escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6203_BS"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/ccb2e5f2-4279-48fd-9d85-a1db42ff1e13"})
MERGE (c)-[r:TEACHES_KNOWLEDGE]->(s)
SET r.confidence = 0.7152,
    r.evidence_ids = ["MAIN", "L09", "L12", "L13", "L14"],
    r.method = "escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6203_BS"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/6eff134b-e34f-4d6e-a6e8-5e47cf2228d0"})
MERGE (c)-[r:TEACHES_KNOWLEDGE]->(s)
SET r.confidence = 0.7118,
    r.evidence_ids = ["MAIN", "L09", "L12", "L14"],
    r.method = "escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6203_BS"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/bec4359e-cb92-468f-a997-8fb28e32fba9"})
MERGE (c)-[r:TEACHES_KNOWLEDGE]->(s)
SET r.confidence = 0.7106,
    r.evidence_ids = ["MAIN", "L09", "L12", "L13", "L14"],
    r.method = "escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6203_BS"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/2d140a3a-45a6-4248-80dd-b3760ebc9cc6"})
MERGE (c)-[r:TEACHES_KNOWLEDGE]->(s)
SET r.confidence = 0.7023,
    r.evidence_ids = ["MAIN", "L09", "L12", "L13", "L14"],
    r.method = "escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6203_BS"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/d5a59ca8-2e91-472e-8571-d12ce4478679"})
MERGE (c)-[r:TEACHES_KNOWLEDGE]->(s)
SET r.confidence = 0.6997,
    r.evidence_ids = ["MAIN", "L09", "L12", "L13", "L14"],
    r.method = "escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6203_BS"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/da6393d5-a53c-4863-abc7-51f36281d74e"})
MERGE (c)-[r:TEACHES_KNOWLEDGE]->(s)
SET r.confidence = 0.6964,
    r.evidence_ids = ["MAIN", "L09", "L12", "L13", "L14"],
    r.method = "escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6203_BS"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/0a9acb6b-1139-4be9-b431-3a80a959f2f4"})
MERGE (c)-[r:TEACHES_KNOWLEDGE]->(s)
SET r.confidence = 0.6878,
    r.evidence_ids = ["MAIN", "L09", "L12", "L13", "L14"],
    r.method = "escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6203_BS"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/3ec2e4d6-7000-4905-bf1a-c5b1679416de"})
MERGE (c)-[r:TEACHES_KNOWLEDGE]->(s)
SET r.confidence = 0.6846,
    r.evidence_ids = ["MAIN", "L12", "L13", "L14"],
    r.method = "escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6203_BS"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/e2d0daae-2aa1-40cc-99e2-b340b02f97d3"})
MERGE (c)-[r:TEACHES_KNOWLEDGE]->(s)
SET r.confidence = 0.6741,
    r.evidence_ids = ["MAIN", "L09", "L12", "L13", "L14"],
    r.method = "escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6203_BS"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/cf532795-a1fd-43bd-8407-6e43f877e6e3"})
MERGE (c)-[r:TEACHES_KNOWLEDGE]->(s)
SET r.confidence = 0.6602,
    r.evidence_ids = ["MAIN", "L09", "L12", "L13", "L14"],
    r.method = "escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6203_BS"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/9d2e926f-53d9-41f5-98f3-19dfaa687f3f"})
MERGE (c)-[r:TEACHES_KNOWLEDGE]->(s)
SET r.confidence = 0.6586,
    r.evidence_ids = ["MAIN", "L09", "L12", "L13", "L14"],
    r.method = "escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6203_BS"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/ab1e97ed-2319-4293-a8b7-072d2648822f"})
MERGE (c)-[r:TEACHES_KNOWLEDGE]->(s)
SET r.confidence = 0.6385,
    r.evidence_ids = ["MAIN", "L09", "L12", "L13", "L14"],
    r.method = "escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "IT6203_BS"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/a7f0fbe0-c546-4f30-8e41-34a58c64567e"})
MERGE (c)-[r:TEACHES_KNOWLEDGE]->(s)
SET r.confidence = 0.4287,
    r.evidence_ids = ["MAIN", "L12", "L13"],
    r.method = "escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "OPTIONAL",
    r.schema_version = "3.0";
