# Kiến trúc skill matching hiện hành

Luồng chính không dùng SkillNER hay LLM skill-hóa. Mỗi kỹ năng đầu ra đều được
truy vết về unit có sẵn trong đề cương canonical và về ESCO skill pool nội bộ.

```text
Course Markdown
  -> extract_course: Layer 1 extraction (lossless source records + provenance)
  -> Layer 2 canonical merge (lossless children + provenance/conflicts)
  -> translated units: course name, CLO, chapter
  -> direct query + ability query
  -> bi-encoder retrieval từ ESCO IT-30 pool
  -> UniSkill_Bert re-rank
  -> aggregate theo course_id
```

Các direct query giữ nguyên bản dịch của unit. Ability query chỉ thêm ngữ cảnh:
học phần có prefix `BS` dùng `foundation/support`; học phần khác dùng
`direct skill/teaches skill`. Kết quả giữ `evidence_queries` để audit.

Lệnh chạy:

```powershell
python -m pipeline.merge
python -m pipeline.extract_translate.run_extract_translate
D:\NCKH_2026\notebook\venv\Scripts\python.exe -m pipeline.skill_matching.pipeline
```

`pipeline.extract_skill` đã được retire và không nằm trong luồng chính. Nó không
được phép tạo skill mới hoặc gọi LLM.
