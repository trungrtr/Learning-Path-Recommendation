CONSTRAINTS = [
    "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Course) REQUIRE c.id IS UNIQUE",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (s:ESCOSkill) REQUIRE s.uri IS UNIQUE",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (ch:Chapter) REQUIRE ch.id IS UNIQUE",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (l:Lesson) REQUIRE l.id IS UNIQUE",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (clo:CLO) REQUIRE clo.id IS UNIQUE",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (o:Occupation) REQUIRE o.uri IS UNIQUE",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (p:CtdtProgram) REQUIRE p.ma_ctdt IS UNIQUE",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (g:CtdtGroup) REQUIRE g.group_id IS UNIQUE",
]

QUERIES = {
    # Nodes
    "courses.csv": """
        UNWIND $batch AS row
        MERGE (c:Course {id: row.course_id})
        SET c.name = row.name_vi, c.internal_code = row.internal_course_code
    """,
    "esco_skills.csv": """
        UNWIND $batch AS row
        MERGE (s:ESCOSkill {uri: row.skill_uri})
        SET s.name = row.skill_label, s.description = row.skill_description
    """,
    "occupations.csv": """
        UNWIND $batch AS row
        MERGE (o:Occupation {uri: row.occupation_uri})
        SET o.name = row.occupation_label, o.code = row.occupation_id, o.description = row.occupation_description
    """,
    "chapters.csv": """
        UNWIND $batch AS row
        MERGE (ch:Chapter {id: row.chapter_id})
        SET ch.name = row.title_vi
    """,
    "lessons.csv": """
        UNWIND $batch AS row
        MERGE (l:Lesson {id: row.lesson_id})
        SET l.name = row.title_vi
    """,
    "clos.csv": """
        UNWIND $batch AS row
        MERGE (clo:CLO {id: row.clo_id})
        SET clo.name = row.content_vi
    """,
    "ctdt_programs.csv": """
        UNWIND $batch AS row
        MERGE (p:CtdtProgram {ma_ctdt: row.ma_ctdt})
        SET p.ten_nganh = row.ten_nganh, p.tong_so_tin_chi = toFloat(row.tong_so_tin_chi)
    """,
    "ctdt_groups.csv": """
        UNWIND $batch AS row
        MERGE (g:CtdtGroup {group_id: row.group_id})
        SET g.nhom_id = row.nhom_id, g.ten_nhom = row.ten_nhom, g.tong_so_tin = toFloat(row.tong_so_tin)
    """,
    
    # Relationships
    "course_skill_relationships.csv": """
        UNWIND $batch AS row
        MATCH (c:Course {id: row.course_id})
        MATCH (s:ESCOSkill {uri: row.skill_uri})
        MERGE (c)-[r:TEACHES_SKILL]->(s)
        SET r.retrieval_score = toFloat(row.retrieval_score), 
            r.rerank_score = toFloat(row.rerank_score),
            r.validation_confidence = toFloat(row.validation_confidence),
            r.evidence_unit_ids = row.evidence_unit_ids
    """,
    "occupation_skill_relationships.csv": """
        UNWIND $batch AS row
        MATCH (o:Occupation {uri: row.occupation_uri})
        MATCH (s:ESCOSkill {uri: row.skill_uri})
        MERGE (o)-[r:REQUIRES_SKILL]->(s)
        SET r.relation_type = row.relation_type
    """,
    "entity_relationships.csv": """
        UNWIND $batch AS row
        MATCH (src {id: row.source_id})
        MATCH (tgt {id: row.target_id})
        CALL apoc.create.relationship(src, row.relationship_type, {}, tgt) YIELD rel
        RETURN count(rel)
    """,
    "ctdt_course_relationships.csv": """
        UNWIND $batch AS row
        MATCH (g:CtdtGroup {group_id: row.group_id})
        MERGE (c:Course {internal_code: row.ma_hp})
        ON CREATE SET c.id = "COURSE_PLACEHOLDER_" + row.ma_hp
        MERGE (g)-[r:HAS_COURSE]->(c)
        SET r.hoc_ky = toInteger(row.hoc_ky)
    """,
    "ctdt_course_dependency_relationships.csv": """
        UNWIND $batch AS row
        MERGE (c1:Course {internal_code: row.ma_hp})
        ON CREATE SET c1.id = "COURSE_PLACEHOLDER_" + row.ma_hp
        MERGE (c2:Course {internal_code: row.dependency_ma_hp})
        ON CREATE SET c2.id = "COURSE_PLACEHOLDER_" + row.dependency_ma_hp
        MERGE (c1)-[r:REQUIRES_COURSE]->(c2)
        SET r.dependency_type = row.dependency_type
    """,
    "ctdt_program_group_relationships.csv": """
        UNWIND $batch AS row
        MATCH (p:CtdtProgram {ma_ctdt: row.ma_ctdt})
        MATCH (g:CtdtGroup {group_id: row.group_id})
        MERGE (p)-[:HAS_GROUP]->(g)
    """,
    "ctdt_group_relationships.csv": """
        UNWIND $batch AS row
        MATCH (g1:CtdtGroup {group_id: row.child_group_id})
        MATCH (g2:CtdtGroup {group_id: row.parent_group_id})
        MERGE (g1)-[:BELONGS_TO_GROUP]->(g2)
    """
}
