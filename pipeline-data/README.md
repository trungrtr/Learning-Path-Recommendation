# 📂 Cấu trúc thư mục: `pipeline-data`

> Thư mục này là **Workspace & Data Hub** (Trung tâm dữ liệu và mã nguồn) cho toàn bộ 파이프라인 (pipeline) xử lý dữ liệu và xây dựng Knowledge Graph của dự án.
> Việc tổ chức chung này giúp quản lý tập trung mã nguồn, tài liệu, script tiện ích và đặc biệt là luồng dữ liệu trung gian giao tiếp giữa các module rời rạc một cách hệ thống, hạn chế rác dữ liệu.

---

## 🌳 Tree View (Tổng quan cấu trúc)

```text
pipeline-data/
│
├── 📁 raw/                       # ── Input gốc ban đầu ──
│   ├── 1_markdown/               #   Markdown từ MinerU (OCR từ tài liệu PDF)
│   ├── 4_ctdt/                   #   Dữ liệu CTĐT (Chương trình đào tạo) đã structured
│   └── 5_mhtml/                  #   MHTML được lưu trực tiếp từ web
│
├── 📁 contract/                  # ── Giao tiếp giữa các module ──
│                                 #   File JSON chuẩn hóa kết xuất từ module extract.
│                                 #   Dùng làm input đầu vào cho module mapping (ví dụ: esco-skill-mapping)
│
├── 📁 esco_data/                 # ── Dữ liệu tham chiếu tĩnh ──
│                                 #   Các file định nghĩa taxonomy tải từ ESCO 
│                                 #   (skills_en.csv, occupations_en.csv, ...)
│
├── 📁 data_missing/              # ── Dữ liệu thiếu/lỗi ──
│                                 #   Nơi chứa các dữ liệu bị thiếu sót cần được xử lý bổ sung
│
├── 📁 final_kg_export/           # ── Output cuối cùng ──
│                                 #   File CSV Node/Edge chuẩn bị để nạp (MERGE) vào Neo4j
│
├── 📁 src/                       # ── Source Code chính ──
│   ├── extract-translate-data/   #   Mã nguồn xử lý M2/M3: Trích xuất, làm sạch, và dịch dữ liệu
│   ├── esco-skill-mapping/       #   Mã nguồn xử lý M4/M5/M6: Ánh xạ chuẩn kỹ năng ESCO
│   └── extract-entities/         #   Mã nguồn trích xuất thực thể bổ sung
│
├── 📁 scripts/                   # ── Script tiện ích & Tooling ──
│                                 #   Các kịch bản tự động hóa (scripts): 
│                                 #   - Build vector database (build_bm25.py, build_faiss.py)
│                                 #   - Sửa/vá dữ liệu lỗi (fix_missing_course_data.py)
│                                 #   - Trích xuất dữ liệu ESCO (esco_extractor.py), v.v.
│
├── 📁 docs/                      # ── Tài liệu dự án ──
│                                 #   Lưu trữ tài liệu thiết kế kiến trúc, schema đồ thị (kg_schema.json),
│                                 #   và các quyết định thiết kế quan trọng.
│
├── 📄 .env                       # File cấu hình biến môi trường chung
└── 📁 .venv/                     # Môi trường ảo Python (Virtual Environment) chung
```

---

## 🔄 Vai trò & Luồng dữ liệu (Data Flow)

Thư mục này vận hành theo một luồng xử lý (pipeline) liên tục như sau:

1. **Thu thập & Tiền xử lý (`raw/` ➡️ `src/extract-translate-data/` ➡️ `contract/`)**
   - Các script trong `extract-translate-data` sẽ đọc dữ liệu thô (unstructured/semi-structured) từ `raw/`.
   - Dữ liệu được làm sạch, trích xuất cấu trúc định dạng chuẩn và dịch sang tiếng Anh (nếu cần thiết). 
   - Kết quả đầu ra (thường là JSON) sẽ được đẩy vào `contract/`.

2. **Ánh xạ Kỹ năng - Skill Mapping (`contract/` & `esco_data/` ➡️ `src/esco-skill-mapping/`)**
   - Mã nguồn trong `esco-skill-mapping` nhận đầu vào là các khóa học/chương trình từ `contract/` và đối chiếu với từ điển chuẩn từ `esco_data/`.
   - Sử dụng LLM, Similarity Search hoặc các phương pháp NLP để liên kết nội dung với danh mục ESCO.

3. **Xây dựng Đồ thị Tri thức (`...` ➡️ `final_kg_export/`)**
   - Dữ liệu sau ánh xạ được tái cấu trúc thành dạng đồ thị: Đỉnh (Nodes) và Cạnh (Edges/Relationships).
   - Dữ liệu này được lưu trữ thành các file CSV tại `final_kg_export/`, tuân thủ schema trong `docs/kg_schema.json`, sẵn sàng để import trực tiếp vào **Neo4j**.

4. **Vận hành & Hỗ trợ (`scripts/` & `data_missing/`)**
   - Trong quá trình chạy pipeline, những record gặp lỗi hoặc thiếu dữ liệu được đẩy vào `data_missing/`.
   - Kỹ sư dữ liệu có thể sử dụng các công cụ độc lập trong thư mục `scripts/` để xử lý lại (re-process), hoặc sinh index hỗ trợ tra cứu (FAISS, BM25).

---

## 🛠 Cài đặt môi trường

Dự án khuyến khích sử dụng chung một môi trường ảo (Virtual Environment) ở cấp thư mục `pipeline-data` để dễ quản lý dependencies giữa các module con:

```bash
# 1. Khởi tạo môi trường ảo Python
python -m venv .venv

# 2. Kích hoạt môi trường (trên Windows)
.venv\Scripts\activate

# 3. Cài đặt các thư viện cần thiết
# Lưu ý: Cần đi vào từng thư mục src/ con để cài đặt requirements cụ thể nếu có.
# Ví dụ: pip install -r src/extract-translate-data/requirements.txt
```
