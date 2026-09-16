Cấu trúc hiện tại của luồng **`teaches_skill_pipeline_B`** được thiết kế theo dạng **Kiến trúc phân tầng (Layered Architecture)**, chia nhỏ quy trình từ lúc nạp dữ liệu môn học cho đến lúc xuất ra bản đồ kỹ năng (Skill/Knowledge Mapping) cuối cùng.

Dựa vào mã nguồn của file điều phối chính `pipeline.py` và cấu trúc thư mục, đây là chi tiết các thành phần và các bước chạy của luồng này:

### 1. Cấu trúc thư mục (Directory Structure)
- **`pipeline.py`**: File đóng vai trò "Nhạc trưởng" (Orchestrator). Chứa class `TeachesSkillPipeline` để khởi tạo cấu hình và chạy tuần tự các tầng (Layer 00 → Layer 10).
- **`configs/`**: Chứa các file cấu hình như `default_config.yaml` và `pipeline_config.py` để tùy chỉnh thông số chạy (như đường dẫn, model LLM, v.v).
- **`models/`**: Định nghĩa các Schema (Pydantic / Dataclass) dùng xuyên suốt pipeline để đảm bảo tính nhất quán của dữ liệu (VD: `candidate.py`, `evidence.py`, `mention.py`, `schemas.py` chứa định dạng output).
- **`utils/`**: Chứa các hàm tiện ích hỗ trợ như `async_llm.py` (gọi API LLM), `model_loader.py` và `text.py` (xử lý văn bản).
- **`layers/`**: Thư mục quan trọng nhất chứa logic cốt lõi của từng giai đoạn (Layer).

### 2. Chi tiết Quy trình hoạt động (Workflow / Layers)
Khi luồng chạy cho một học phần (VD: IT6218), nó sẽ đi qua tuần tự các tầng sau:

* **Tầng 00: Ingestion (`layer_00_ingestion.py`)**
  * Nạp 4 file JSON Data Contract của học phần (như file `IT6218__hoc_phan.json` bạn đang xem).
  * Validate kiểm tra tính hợp lệ của dữ liệu đầu vào.
* **Tầng 005: Evidence Builder (`layer_005_evidence_builder.py`)**
  * Tiền xử lý và gom nhóm các text đầu vào thành các "Bằng chứng" (Evidence Units) như Mục tiêu môn học, Chuẩn đầu ra (CLO), và Tên Bài học.
* **Tầng 01: Extraction (`layer_01_extraction.py`)**
  * Dùng LLM (Mô hình ngôn ngữ lớn) để đọc các Evidence và trích xuất ra các cụm từ quan trọng (Mentions) đại diện cho kỹ năng hoặc kiến thức.
* **Tầng 02: Retrieval (`layer_02_retrieval.py`)**
  * Tìm kiếm và ghép nối các Mentions với từ điển chuẩn ESCO thông qua hệ thống tìm kiếm kết hợp (BM25 + FAISS + RRF) để lấy ra các Candidates tiềm năng nhất.
* **Tầng 04: Reranking & Decision (`layer_04_reranking.py`)**
  * Xếp hạng lại (Rerank) các Candidates tìm được dựa vào độ phù hợp với ngữ cảnh của học phần, sau đó quyết định chấp nhận (Accepted) hay loại bỏ (Rejected) Candidate đó.
* **Tầng 05: LLM Verification (`layer_05_llm_verification.py`)**
  * Kiểm tra chéo lại lần cuối bằng LLM đối với những mappings đã được chấp nhận ở Tầng 04, đảm bảo tính chính xác cao nhất (giảm thiểu False Positive).
* **Tầng 06-10: Post Processing (`layer_06_to_10.py`)**
  * Các bước hậu kỳ, chuẩn hóa dữ liệu cuối cùng và xuất ra dưới dạng các bản ghi `SkillTeacherRecord` chuẩn format (đánh dấu đây là quan hệ `TEACHES_SKILL` hay `TEACHES_KNOWLEDGE`).

> [!TIP]
> Nhờ cách thiết kế tách biệt (decoupled) này, việc tinh chỉnh hay thay đổi mô hình LLM, thuật toán tìm kiếm (FAISS/BM25) đều có thể được thực hiện độc lập ở từng Tầng (Layer) mà không làm ảnh hưởng đến phần còn lại của luồng dữ liệu.
