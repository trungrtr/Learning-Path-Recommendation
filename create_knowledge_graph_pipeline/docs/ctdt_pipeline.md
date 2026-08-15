# CTDT Pipeline

Luồng chương trình đào tạo chạy độc lập với luồng đề cương học phần:

```text
data/00_input/CTDT/*.pdf|*.md|*.txt
  -> extract_ctdt
  -> data/01_ctdt_extracted/*.json
  -> kg_export_ctdt
  -> data/06_kg_ready/ctdt_*.csv
```

Chạy toàn bộ luồng:

```powershell
$env:PYTHONPATH = "."
python -m pipeline.run_ctdt_pipeline --config config.yaml
```

Chạy từng bước:

```powershell
python -m pipeline.extract_ctdt --config config.yaml
python -m pipeline.kg_export.ctdt --config config.yaml
```

Các file KG-ready được ghi thêm vào `data/06_kg_ready` và không ghi đè các CSV học phần/skill hiện có:

- `ctdt_programs.csv`
- `ctdt_groups.csv`
- `ctdt_program_group_relationships.csv`
- `ctdt_group_relationships.csv`
- `ctdt_course_relationships.csv`
- `ctdt_course_dependency_relationships.csv`
- `ctdt_kg_export.json`

Quan hệ học phần trong CTDT dùng `ma_hp` để Neo4j import match với `HocPhan.internal_course_code` hoặc mã học phần tương ứng ở tầng import Cypher.
