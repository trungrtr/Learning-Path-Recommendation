MATCH (c:Course {code: "SC6265"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/ccd0a1d9-afda-43d9-b901-96344886e14d"})
MERGE (c)-[r:TEACHES_KNOWLEDGE]->(s)
SET r.confidence = 0.8335,
    r.evidence_ids = ["MAIN", "L1", "L2", "L13", "L16", "L17", "L18", "L20", "L21", "L22", "L23", "L24"],
    r.method = "escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "SC6265"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/d31fab87-2a7d-485c-b699-2901ca294b15"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.8092,
    r.evidence_ids = ["MAIN", "L1", "L2", "L13", "L16", "L17", "L18", "L19", "L20", "L21", "L22", "L23", "L24"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "SC6265"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/21d2f96d-35f7-4e3f-9745-c533d2dd6e97"})
MERGE (c)-[r:TEACHES_KNOWLEDGE]->(s)
SET r.confidence = 0.7995,
    r.evidence_ids = ["MAIN", "L1", "L2", "L13", "L16", "L17", "L18", "L20", "L21", "L22", "L23", "L24"],
    r.method = "escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "SC6265"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/5b9cde20-f1b9-4adc-bfb3-dbf70b14138d"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.7834,
    r.evidence_ids = ["MAIN", "L1", "L2", "L13", "L16", "L17", "L18", "L19", "L20", "L21", "L22", "L23", "L24"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "SC6265"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/2c4e11ef-da18-4e19-816b-e6bc19e12424"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.7694,
    r.evidence_ids = ["MAIN", "L1", "L2", "L13", "L16", "L17", "L19", "L20", "L21", "L22", "L23", "L24"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "SC6265"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/5be3d306-6cf1-4b49-aa1d-01651dd4ba4c"})
MERGE (c)-[r:TEACHES_KNOWLEDGE]->(s)
SET r.confidence = 0.7523,
    r.evidence_ids = ["MAIN", "L1", "L2", "L13", "L16", "L17", "L18", "L19", "L20", "L22", "L23", "L24"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "SC6265"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/13bdd41a-2a18-441f-96db-41252c519413"})
MERGE (c)-[r:TEACHES_KNOWLEDGE]->(s)
SET r.confidence = 0.7001,
    r.evidence_ids = ["MAIN", "L1", "L2", "L13", "L16", "L17", "L18", "L20", "L22", "L23", "L24"],
    r.method = "escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "SECONDARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "SC6265"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/42ed3bfb-1a01-4c8b-9758-fc6438865734"})
MERGE (c)-[r:TEACHES_KNOWLEDGE]->(s)
SET r.confidence = 0.6990,
    r.evidence_ids = ["MAIN", "L1", "L2", "L13", "L16", "L17", "L18", "L20", "L22", "L23", "L24"],
    r.method = "escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "SECONDARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "SC6265"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/f9670490-8aa4-4540-b121-d440a8294aab"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.6986,
    r.evidence_ids = ["MAIN", "L1", "L2", "L13", "L16", "L17", "L19", "L20", "L21", "L22", "L23", "L24"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "SC6265"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/2bde42ae-e776-41c1-9ded-b07b30bfe985"})
MERGE (c)-[r:TEACHES_KNOWLEDGE]->(s)
SET r.confidence = 0.6981,
    r.evidence_ids = ["MAIN", "L1", "L2", "L13", "L16", "L17", "L18", "L20", "L21", "L22", "L23", "L24"],
    r.method = "escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "SC6265"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/e8b89eb6-51e8-4c3a-babb-88b2e110376b"})
MERGE (c)-[r:TEACHES_KNOWLEDGE]->(s)
SET r.confidence = 0.6948,
    r.evidence_ids = ["MAIN", "L1", "L2", "L13", "L16", "L17", "L18", "L20", "L22", "L23", "L24"],
    r.method = "escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "SC6265"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/19a8293b-8e95-4de3-983f-77484079c389"})
MERGE (c)-[r:TEACHES_KNOWLEDGE]->(s)
SET r.confidence = 0.6902,
    r.evidence_ids = ["MAIN", "L1", "L2", "L13", "L16", "L18", "L20", "L21", "L22", "L23", "L24"],
    r.method = "escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "PRIMARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "SC6265"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/47b9bbcf-356c-4782-83a4-7f5a1b2b51a3"})
MERGE (c)-[r:TEACHES_KNOWLEDGE]->(s)
SET r.confidence = 0.6886,
    r.evidence_ids = ["MAIN", "L1", "L2", "L13", "L16", "L17", "L18", "L20", "L21", "L22", "L23", "L24"],
    r.method = "escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "SECONDARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "SC6265"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/fecf8a0d-62c4-4e71-9b03-0f4fc2ad7bf5"})
MERGE (c)-[r:TEACHES_KNOWLEDGE]->(s)
SET r.confidence = 0.6656,
    r.evidence_ids = ["MAIN", "L1", "L2", "L19", "L20", "L21", "L24"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "SECONDARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "SC6265"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/7d10fcb2-b368-48ab-996b-7c9fafcf68ed"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.6598,
    r.evidence_ids = ["MAIN", "L1", "L2", "L13", "L16", "L17", "L18", "L20", "L21", "L22", "L23", "L24"],
    r.method = "escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "SECONDARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "SC6265"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/9973a5a2-7822-4161-99e9-95c781eb63f8"})
MERGE (c)-[r:TEACHES_KNOWLEDGE]->(s)
SET r.confidence = 0.6596,
    r.evidence_ids = ["MAIN", "L1", "L2", "L16", "L18", "L20", "L21", "L22", "L23", "L24"],
    r.method = "escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "SECONDARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "SC6265"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/022dc430-872a-473a-9cf4-fed4895e58ad"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.6465,
    r.evidence_ids = ["MAIN", "L1", "L2", "L16", "L19", "L20", "L21", "L24"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "SECONDARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "SC6265"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/0ccdfe98-f845-4598-84a1-3dca66e9d9a3"})
MERGE (c)-[r:TEACHES_KNOWLEDGE]->(s)
SET r.confidence = 0.6431,
    r.evidence_ids = ["MAIN", "L1", "L2", "L13", "L16", "L17", "L20", "L22", "L23", "L24"],
    r.method = "escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "SECONDARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "SC6265"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/0de61385-de6d-4146-ba32-1cc1bc102220"})
MERGE (c)-[r:TEACHES_KNOWLEDGE]->(s)
SET r.confidence = 0.6422,
    r.evidence_ids = ["MAIN", "L1", "L2", "L13", "L16", "L17", "L18", "L20", "L22", "L23", "L24"],
    r.method = "escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "SECONDARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "SC6265"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/4c016b68-4116-468c-9dc6-42710c239e4a"})
MERGE (c)-[r:TEACHES_KNOWLEDGE]->(s)
SET r.confidence = 0.6420,
    r.evidence_ids = ["MAIN", "L1", "L2", "L13", "L16", "L18", "L20", "L21", "L22", "L23", "L24"],
    r.method = "escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "SECONDARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "SC6265"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/69bbd53f-fbb0-4476-b4b2-ef7844464e28"})
MERGE (c)-[r:TEACHES_KNOWLEDGE]->(s)
SET r.confidence = 0.6358,
    r.evidence_ids = ["MAIN", "L1", "L2", "L13", "L16", "L17", "L18", "L19", "L20", "L22", "L23", "L24"],
    r.method = "escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "OPTIONAL",
    r.schema_version = "3.0";

MATCH (c:Course {code: "SC6265"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/000f1d3d-220f-4789-9c0a-cc742521fb02"})
MERGE (c)-[r:TEACHES_KNOWLEDGE]->(s)
SET r.confidence = 0.6332,
    r.evidence_ids = ["MAIN", "L1", "L2", "L16", "L18", "L19", "L20", "L22", "L23", "L24"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "SECONDARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "SC6265"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/2daec0e6-f0c1-43e8-8178-aedba99130ec"})
MERGE (c)-[r:TEACHES_SKILL]->(s)
SET r.confidence = 0.6230,
    r.evidence_ids = ["MAIN", "L1", "L2", "L13", "L16", "L17", "L19", "L20", "L21", "L22", "L23", "L24"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "SECONDARY",
    r.schema_version = "3.0";

MATCH (c:Course {code: "SC6265"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/58d7a289-dafd-4363-833f-d1dc4140885e"})
MERGE (c)-[r:TEACHES_KNOWLEDGE]->(s)
SET r.confidence = 0.6055,
    r.evidence_ids = ["MAIN", "L1", "L2", "L13", "L16", "L17", "L18", "L20", "L22", "L23", "L24"],
    r.method = "escoxlmr_knowledge+UniSkill-CrossEncoder",
    r.tier = "OPTIONAL",
    r.schema_version = "3.0";

MATCH (c:Course {code: "SC6265"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/51586df8-1c46-4b47-8583-773cb63bf00b"})
MERGE (c)-[r:TEACHES_KNOWLEDGE]->(s)
SET r.confidence = 0.5952,
    r.evidence_ids = ["MAIN", "L1", "L2", "L13", "L16", "L17", "L18", "L20", "L22", "L23", "L24"],
    r.method = "escoxlmr_knowledge+escoxlmr_skill+UniSkill-CrossEncoder",
    r.tier = "OPTIONAL",
    r.schema_version = "3.0";
