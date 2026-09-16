MATCH (c:Course {code: "BS6054_BS"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/31c69100-b612-4a61-8db5-fd314318854c"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.7175,
    r.evidence_ids = ["MAIN", null, "L11", "L15", "L16"],
    r.method = "escoxlmr_skill+escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "BS6054_BS"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/561c2525-5bd8-4d86-8f45-820f4be7db93"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.7102,
    r.evidence_ids = ["MAIN", null, "L16", "L18"],
    r.method = "escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "BS6054_BS"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/2b92a5b2-6758-4ee3-9fb4-b6387a55cc8f"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.7079,
    r.evidence_ids = ["MAIN", null, "L12", "L16", "L18", "L19"],
    r.method = "escoxlmr_skill+escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "BS6054_BS"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/f2d57f41-43b4-4f5b-8100-3df5c21eda50"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.6938,
    r.evidence_ids = ["MAIN", null, "L11", "L12"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "BS6054_BS"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/cc7370dd-69fa-4c67-a96f-d4d135d38700"})
MERGE (c)-[r:TEACHES_KNOWLEDGE]->(s)
SET r.confidence = 0.6657,
    r.evidence_ids = ["MAIN", null, "L12", "L16"],
    r.method = "escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "BS6054_BS"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/6360a934-cc87-4954-9656-b32db20592e3"})
MERGE (c)-[r:TEACHES_KNOWLEDGE]->(s)
SET r.confidence = 0.6352,
    r.evidence_ids = ["MAIN", null, "L11", "L16"],
    r.method = "escoxlmr_skill+escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "BS6054_BS"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/48db96bf-3314-45c6-bad8-fdb6e20e5639"})
MERGE (c)-[r:TEACHES_KNOWLEDGE]->(s)
SET r.confidence = 0.6206,
    r.evidence_ids = ["MAIN", null, "L11", "L12", "L16", "L19"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "SECONDARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "BS6054_BS"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/f6ac6241-adb2-4ce2-b35f-09832cbb11ea"})
MERGE (c)-[r:TEACHES_KNOWLEDGE]->(s)
SET r.confidence = 0.6160,
    r.evidence_ids = ["MAIN", null, "L16", "L18", "L19"],
    r.method = "escoxlmr_skill+escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "SECONDARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "BS6054_BS"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/50b100ea-74fd-4706-99db-3e4ca55e51b8"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.6100,
    r.evidence_ids = ["MAIN", null, "L12", "L18", "L19"],
    r.method = "escoxlmr_skill+escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "SECONDARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "BS6054_BS"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/c544a9f3-5945-4b54-afed-de0697852817"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.6053,
    r.evidence_ids = ["MAIN", null, "L16", "L18"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "SECONDARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "BS6054_BS"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/edebd83d-35f6-4ed5-a940-6c203d178c01"})
MERGE (c)-[r:TEACHES_KNOWLEDGE]->(s)
SET r.confidence = 0.5659,
    r.evidence_ids = ["MAIN", null, "L12", "L16", "L19"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "SECONDARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "BS6054_BS"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/b011c8b4-76e1-4bbc-8bb9-1d205e7b618a"})
MERGE (c)-[r:TEACHES_KNOWLEDGE]->(s)
SET r.confidence = 0.5526,
    r.evidence_ids = ["MAIN", null, "L11", "L15", "L18", "L19"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "OPTIONAL",
    r.schema_version = "3.0";

MATCH (c:Course {code: "BS6054_BS"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/901105f8-3a08-453e-b1dc-23619e317fd3"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.5267,
    r.evidence_ids = ["MAIN", "L11", "L15", "L16", "L18", "L19", "L20"],
    r.method = "escoxlmr_skill+escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "OPTIONAL",
    r.schema_version = "3.0";

MATCH (c:Course {code: "BS6054_BS"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/4fabca9a-7435-4f33-b1da-3cdb00340fdc"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.4845,
    r.evidence_ids = ["MAIN", null, "L11", "L16", "L18", "L19"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "OPTIONAL",
    r.schema_version = "3.0";

MATCH (c:Course {code: "BS6054_BS"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/f9670490-8aa4-4540-b121-d440a8294aab"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.4415,
    r.evidence_ids = ["MAIN", null, "L12", "L16"],
    r.method = "escoxlmr_skill+escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "OPTIONAL",
    r.schema_version = "3.0";

MATCH (c:Course {code: "BS6054_BS"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/72a74f69-5cf1-43c5-99b9-62a444578919"})
MERGE (c)-[r:TEACHES_KNOWLEDGE]->(s)
SET r.confidence = 0.4379,
    r.evidence_ids = ["MAIN", null, "L11", "L15", "L16", "L18", "L19"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "OPTIONAL",
    r.schema_version = "3.0";

MATCH (c:Course {code: "BS6054_BS"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/b0a3bb25-a02f-43ed-ab1f-994fa66a424a"})
MERGE (c)-[r:TEACHES_KNOWLEDGE]->(s)
SET r.confidence = 0.4327,
    r.evidence_ids = ["MAIN", null, "L11", "L12", "L18"],
    r.method = "escoxlmr_skill+escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "OPTIONAL",
    r.schema_version = "3.0";

MATCH (c:Course {code: "BS6054_BS"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/861cc783-6d4c-442e-9081-3a6e389be454"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.4162,
    r.evidence_ids = ["MAIN", null, "L15", "L16", "L18"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "OPTIONAL",
    r.schema_version = "3.0";

MATCH (c:Course {code: "BS6054_BS"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/d38871eb-b988-495e-8fca-345677b597a8"})
MERGE (c)-[r:TEACHES_KNOWLEDGE]->(s)
SET r.confidence = 0.4152,
    r.evidence_ids = ["MAIN", null, "L11", "L12", "L15", "L16", "L19"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "OPTIONAL",
    r.schema_version = "3.0";

MATCH (c:Course {code: "BS6054_BS"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/1b70a55d-b8a4-49fc-96c6-15ab4cff2522"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.4117,
    r.evidence_ids = ["MAIN", null, "L12", "L16", "L18"],
    r.method = "escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "OPTIONAL",
    r.schema_version = "3.0";

MATCH (c:Course {code: "BS6054_BS"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/4216e465-7baa-4884-a241-54b197bb9278"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.4028,
    r.evidence_ids = ["MAIN", null, "L12", "L16", "L18"],
    r.method = "escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "OPTIONAL",
    r.schema_version = "3.0";

MATCH (c:Course {code: "BS6054_BS"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/8f6ed69b-29d0-4c01-81ba-f05920a185f3"})
MERGE (c)-[r:TEACHES_KNOWLEDGE]->(s)
SET r.confidence = 0.3952,
    r.evidence_ids = ["MAIN", "L15", "L18", "L19", "L20"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "OPTIONAL",
    r.schema_version = "3.0";

MATCH (c:Course {code: "BS6054_BS"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/23b45aa6-a479-486d-9e6f-062cbab7c68a"})
MERGE (c)-[r:TEACHES_KNOWLEDGE]->(s)
SET r.confidence = 0.3547,
    r.evidence_ids = ["MAIN", null, "L11", "L15", "L18", "L19"],
    r.method = "escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "OPTIONAL",
    r.schema_version = "3.0";
