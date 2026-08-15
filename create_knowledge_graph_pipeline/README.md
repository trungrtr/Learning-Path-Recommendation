# Tầng 1 — Nạp dữ liệu vào Knowledge Graph

Đây là **Tầng 1** của hệ thống tổng: nhận các file Markdown đề cương học phần
đã được tiền xử lý, trích xuất bằng LLM, chuẩn hoá và xuất CSV để nạp Neo4j.
Tầng này không crawl, không xử lý MHTML và không chứa các tầng gợi ý/khuyến
nghị phía sau của hệ thống.

## Luồng xử lý trong Tầng 1

```text
data/input/markdown/*.md
        │
        ├─ trich_xuat       LangExtract + Gemini trích xuất theo schema nguồn
        ▼
data/work/extracted/*.json
        │
        ├─ chuan_hoa        gom các lần trích xuất, khử trùng, giải quyết xung đột
        ▼
data/work/canonical/*.json
        │
        ├─ lien_ket_ky_nang tìm skill mention và liên kết với ESCO bằng embedding
        ▼
data/work/skill_links/*.json
        │
        └─ xuat_neo4j
data/output/neo4j/*.csv  →  Neo4j
```

## Cấu trúc thư mục

```text
configs/
  settings.yaml                    # đường dẫn, model LLM, ngưỡng xử lý
data/
  input/markdown/                  # đầu vào .md đã làm sạch
  reference/esco/                  # ESCO skills.csv chính thức
  work/
    extracted/                     # kết quả LLM theo từng tài liệu
    canonical/                     # hồ sơ học phần đã chuẩn hoá
    skill_links/                   # skill mention đã liên kết ESCO
  output/neo4j/                    # CSV sẵn sàng nạp Neo4j
docs/
  source_document_schema.json
  canonical_course_schema.json
  canonicalization_design.md
src/                      # mã nguồn của riêng Tầng 1
  dung_chung/                      # config, logging, ID, hash, chuẩn hoá text
  mo_hinh_du_lieu/                 # hợp đồng Pydantic giữa các công đoạn
  trich_xuat/                      # Markdown → JSON bằng LLM
    cau_lenh/                       # prompt cho LLM
    schema_langextract.py           # schema LangExtract bám theo source_document_schema.json
  chuan_hoa/                        # gộp và chuẩn hoá dữ liệu
  lien_ket_ky_nang/                # liên kết kỹ năng ESCO
  xuat_neo4j/                      # JSON → CSV Neo4j
    mau_cypher/                     # truy vấn Cypher tham khảo
  chay.py                           # chạy trọn Tầng 1
tests/
  test_extraction/
  test_canonicalization/
  test_skill_linking/
  test_common/
```

## Chạy

Thiết lập `LANGEXTRACT_API_KEY` (hoặc `GEMINI_API_KEY`), chuẩn bị `course_key_map.json` để ánh xạ tên file
Markdown sang `crawl_course_key`, và đặt ESCO dump tại `data/reference/esco/`.
Có thể sao chép `data/input/course_key_map.example.json` rồi thay bằng danh sách
file thực tế.

```powershell
pip install -r requirements.txt
$env:LANGEXTRACT_API_KEY = "..."
$env:PYTHONPATH = "src"

python -m chay --course-key-map data/input/course_key_map.json
```

Có thể chạy từng công đoạn khi cần kiểm tra hoặc chạy lại một bước:

```powershell
python -m trich_xuat.run --input data/input/markdown --output data/work/extracted --course-key-map data/input/course_key_map.json
python -m chuan_hoa.run --input data/work/extracted --output data/work/canonical
python -m lien_ket_ky_nang.run --input data/work/canonical --esco-dir data/reference/esco --output data/work/skill_links
python -m xuat_neo4j.neo4j --canonical data/work/canonical --skill-links data/work/skill_links --output data/output/neo4j
```

`crawl_course_key` là khóa ổn định từ hệ thống tiền xử lý; không suy ra từ LLM.
ESCO chỉ được nạp từ dump chính thức, không được LLM tự sinh.
LangExtract dùng schema có ràng buộc tại `src/trich_xuat/schema_langextract.py`;
kết quả tiếp tục được Pydantic kiểm tra trước khi ghi JSON.
