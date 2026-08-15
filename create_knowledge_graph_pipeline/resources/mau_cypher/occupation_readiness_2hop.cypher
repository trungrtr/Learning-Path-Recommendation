// Ví dụ truy vấn 2-hop: sinh viên đã học những course nào có chạm tới các
// skill cần cho 1 nghề (occupation) X, giả định có sẵn node Occupation
// (import riêng từ ESCO occupations.csv) và quan hệ REQUIRES_SKILL.
//
// Hop 1: Occupation -> Skill (từ ESCO)
// Hop 2: Skill <- MENTIONS_SKILL <- (Chuong | Bai | MoTaHocPhan) <- HocPhan
//
// Đây là template - sửa $occupation_uri khi gọi thật.

MATCH (o:Occupation {uri: $occupation_uri})-[:REQUIRES_SKILL]->(s:ESCOSkill)
MATCH (entity)-[m:MENTIONS_SKILL]->(s)
MATCH (c:HocPhan)-[:HAS_CHAPTER|HAS_LESSON*0..1]->(entity)
RETURN
  c.course_code AS course_code,
  c.name_vi AS course_name,
  collect(DISTINCT s.preferred_label) AS skills_covered,
  count(DISTINCT s) AS num_skills_covered
ORDER BY num_skills_covered DESC
