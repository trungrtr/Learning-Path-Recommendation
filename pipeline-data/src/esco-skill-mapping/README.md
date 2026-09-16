# ESCO Skill Mapping Pipeline

Dự án này đảm nhiệm vai trò cốt lõi trong việc **ánh xạ (mapping) và liên kết (linking)** các thực thể khóa học đại học (như mục tiêu, chuẩn đầu ra, nội dung bài học) với hệ sinh thái phân loại kỹ năng chuẩn châu Âu (**ESCO Taxonomy**). 

Hệ thống được thiết kế thành 2 luồng pipeline độc lập, chuyên biệt cho từng loại kỹ năng nhằm đảm bảo độ chính xác cao nhất và cấu trúc hóa dưới dạng Knowledge Graph.

## 🎯 Phân luồng Pipeline (Architecture)

Dự án sử dụng cấu trúc `src-layout` hiện đại và phân làm 2 package chính bên trong thư mục `src/`:

### 1. Teaches Skill Pipeline (`src/teaches_skill_pipeline`)
Đảm nhiệm việc trích xuất và liên kết các kỹ năng chuyên môn cứng (**Hard/Technical Skills**) mà môn học trực tiếp giảng dạy.
*   **Công nghệ**: Retrieval-Augmented Generation (RAG) + Semantic Search.
*   **Phương pháp**: 
    * Sử dụng **FAISS** để tìm kiếm vector ngữ nghĩa (Vector Retrieval) dựa trên Embedding.
    * Sử dụng **Cross-Encoder Reranking** (HuggingFace Transformers) để chấm điểm và tinh chỉnh lại độ tương đồng ngữ nghĩa.
    * Trả về danh sách kỹ năng chuyên môn khớp nhất.

### 2. Supports Skill Pipeline (`src/supports_skill_pipeline`)
Đảm nhiệm việc trích xuất các kỹ năng nền tảng, kỹ năng mềm, hoặc tư duy (**Foundational/Soft Skills**) mà khóa học gián tiếp hỗ trợ phát triển.
*   **Công nghệ**: LLM Reasoning + Closed-loop ESCO lookup.
*   **Phương pháp**: 
    * Sử dụng sức mạnh suy luận của LLM (Mô hình ngôn ngữ lớn) để đọc ngữ cảnh khóa học và trích xuất ra các concept hỗ trợ.
    * Tra cứu vòng lặp với dữ liệu ESCO để tìm ra các mã kỹ năng chuẩn xác.

## 🛠 Tech Stack (Công nghệ sử dụng)

*   **Ngôn ngữ**: Python 3.10+
*   **Mô hình ngôn ngữ (LLMs)**: `google-genai` (Gemini 2.5 Flash,...)
*   **Xử lý Ngôn ngữ Tự nhiên & Embedding**: `sentence-transformers`, `transformers`, `torch`
*   **Vector Database (Local)**: `faiss-cpu` (Tối ưu tìm kiếm triệu bản ghi trên CPU)
*   **Xử lý dữ liệu**: `pandas`, `pydantic` (Data Validation)
*   **Lưu trữ Đồ thị**: `neo4j` (Export dữ liệu cuối cùng vào Knowledge Graph)

## 📁 Cấu trúc thư mục (Directory Structure)

```text
esco-skill-mapping/
├── data/                       # Dữ liệu nội bộ sinh ra trong quá trình chạy
│   ├── data_teaches_skill/     # Dữ liệu & kết quả của luồng Teaches
│   └── data_support_skill/     # Dữ liệu & kết quả của luồng Supports
├── scripts/
│   └── esco_dataset.py         # Script để khởi tạo/cập nhật bộ dữ liệu ESCO 30 nghề (Filtered ESCO)
├── src/                        # Thư mục mã nguồn chính (Source Code)
│   ├── teaches_skill_pipeline/ # Pipeline liên kết kỹ năng chuyên môn cứng
│   └── supports_skill_pipeline/# Pipeline liên kết kỹ năng nền tảng/mềm
├── pyproject.toml              # Cấu hình project và dependencies
└── README.md                   # File tài liệu này
```

## 🚀 Cài đặt và Sử dụng

**Bước 1: Cài đặt môi trường**
Dự án sử dụng file `pyproject.toml` để quản lý thư viện. Cài đặt toàn bộ dependencies và set up package ở chế độ development bằng lệnh:
```bash
pip install -e .
```

**Bước 2: Cấu hình biến môi trường**
Tạo file `.env` từ file mẫu `.env.example` và điền các API Keys cần thiết:
```bash
cp .env.example .env
# Điền GEMINI_API_KEY và NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD
```

**Bước 3: Chạy Pipeline**
Vì code được đặt trong kiến trúc `src/`, bạn có thể chạy các module bằng cách khai báo `PYTHONPATH`:
```bash
# Trên Windows PowerShell
$env:PYTHONPATH="src"

# Khởi chạy một module bất kỳ
python src/teaches_skill_pipeline/pipeline.py
python src/supports_skill_pipeline/pipeline.py
```

## 📊 Về bộ dữ liệu chuẩn ESCO (Filtered Dataset)
Thay vì sử dụng toàn bộ hơn 14,000 kỹ năng của ESCO (rất nhiễu), hệ thống sử dụng một tập dữ liệu đã được tinh gọn (Filtered ESCO Dataset) tập trung vào đúng **30 nhóm nghề CNTT cốt lõi** tại thị trường Việt Nam.

Bạn có thể tạo lại/cập nhật tập dữ liệu này bằng script có sẵn:
```bash
python scripts/esco_dataset.py
```
Dữ liệu chuẩn hóa sẽ được xuất ra thư mục `esco_data` phục vụ cho cả 2 pipeline.
