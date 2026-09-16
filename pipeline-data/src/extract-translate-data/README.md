# Extract & Translate Data Pipeline

Đây là luồng dữ liệu tiền xử lý cốt lõi của dự án NCKH 2026. Mục tiêu duy nhất của pipeline này là: **nhận dữ liệu thô (raw data) từ nhiều nguồn khác nhau (PDF, HTML, mhtml), trích xuất thông tin có cấu trúc (extraction), và dịch sang tiếng Anh (translation)** để tạo ra các "Data Contract" sạch sẽ, đồng nhất chuẩn bị cho luồng [ESCO Skill Mapping](../esco-skill-mapping/).

## 🎯 3 Luồng Xử Lý Chính (Data Flows)

Do đặc thù dữ liệu đầu vào rất đa dạng về định dạng và mức độ đầy đủ thông tin, pipeline được chia làm 3 luồng xử lý song song:

### 1. Luồng A — Syllabus (Đề cương chi tiết học phần)
*   **Đầu vào**: Các file PDF đề cương môn học dạng scan.
*   **Đặc điểm**: Đầy đủ thông tin (Mục tiêu, Chuẩn đầu ra - CLO, Nội dung bài học) nhưng là ảnh scan.
*   **Quy trình**:
    1. **M1 (OCR)**: Sử dụng MinerU để bóc tách text từ ảnh PDF.
    2. **M2 (Extraction)**: Dùng LLM Gemini trích xuất thông tin theo cấu trúc JSON định sẵn.
    3. **M3 (Translation)**: Dịch toàn bộ thực thể sang tiếng Anh.

### 2. Luồng B — CTDT (Chương trình đào tạo)
*   **Đầu vào**: Các file PDF/HTML cấu trúc của chương trình đào tạo tổng thể.
*   **Đặc điểm**: Chứa thông tin tổng quan, danh sách học phần, cấu trúc cây môn học (không có CLO chi tiết).
*   **Quy trình**:
    1. **M2B (Extraction)**: Trích xuất trực tiếp bằng LLM (không cần OCR).
    2. **M3B (Translation)**: Dịch sang tiếng Anh.

### 3. Luồng C — Các môn Đại cương (MHTML)
*   **Đầu vào**: Trang chi tiết học phần môn đại cương (Toán, Triết, GDTC...) lưu dưới dạng `.mhtml`.
*   **Đặc điểm**: Format HTML chuẩn, nhưng **không hề có phần Mục tiêu và CLO**.
*   **Quy trình**:
    1. **M2C-a (HTML Parsing)**: Bóc tách trực tiếp bằng code Python (không dùng LLM, không OCR).
    2. **M2C-b (Completion)**: Dùng LLM bổ sung các trường bị thiếu (như Mục tiêu, CLO) dựa trên mô tả môn học.
    3. **M2C-c (Human Review)**: Bắt buộc review thủ công 100% đối với các CLO do AI tự bịa ra.
    4. **M3C (Translation)**: Dịch sang tiếng Anh.

*(Đầu ra của cả 3 luồng này sẽ hội tụ lại thành các file JSON chuẩn mực - Data Contract).*

## 🛠 Tech Stack (Công nghệ)

*   **Ngôn ngữ**: Python 3.10+
*   **Mô hình ngôn ngữ (LLM)**: `google-genai` (Gemini 2.5 Flash / Pro) dùng để bóc tách cấu trúc và dịch thuật.
*   **OCR**: `MinerU` (PDF Parsing cực mạnh cho tài liệu khoa học/bảng biểu).
*   **Cấu trúc dữ liệu (Data Validation)**: `pydantic`.

## 📁 Cấu trúc thư mục

```text
extract-translate-data/
├── data/                       # Chứa dữ liệu raw, interim, và processed (Data Contract)
├── docs/                       # Tài liệu thiết kế hệ thống quan trọng
│   ├── AGENT.md                # Bộ nguyên tắc bắt buộc cho AI Agent
│   └── PIPELINE_BUILD_GUIDE.md # Kim chỉ nam kiến trúc 3 luồng dữ liệu
├── pipeline/                   # Source code chính của pipeline
│   ├── m1/                     # Logic OCR (MinerU)
│   ├── m2/                     # Logic Extraction (LLM / HTML Parsing)
│   ├── m3/                     # Logic Translation
│   └── orchestrator.py         # Kịch bản điều phối các luồng
├── scripts/
│   ├── run.py                  # Entrypoint khởi chạy pipeline
│   └── check_setup.py          # Script kiểm tra môi trường
├── shared/                     # Utilities dùng chung (logger, file_io, llm_client)
├── config.yaml                 # Cấu hình system (models, prompts, thresholds)
└── README.md                   # File này
```

## 🚀 Hướng dẫn khởi chạy

**1. Cài đặt môi trường**
```bash
pip install -r requirements.txt
```

**2. Cấu hình biến môi trường**
Đảm bảo bạn đã sao chép `.env.example` thành `.env` và điền `GEMINI_API_KEY`:
```bash
cp .env.example .env
```

**3. Chạy pipeline**
Bạn có thể khởi chạy riêng lẻ từng luồng xử lý thông qua `scripts/run.py`:

```bash
# Chạy Luồng B (Chương trình đào tạo)
python scripts/run.py --flow ctdt

# Chạy Luồng A (Đề cương chi tiết học phần - PDF)
python scripts/run.py --flow syllabus

# Chạy Luồng C (Môn đại cương - MHTML)
python scripts/run.py --flow mhtml
```

> ⚠️ **Lưu ý quan trọng**: Đọc kỹ file `docs/AGENT.md` và `docs/PIPELINE_BUILD_GUIDE.md` nếu bạn muốn tìm hiểu sâu hoặc muốn tùy chỉnh logic trích xuất của pipeline này. Không tự ý sửa luồng nếu không hiểu rõ Data Contract!
