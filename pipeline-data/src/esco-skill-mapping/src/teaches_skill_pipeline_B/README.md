# Teaches-Skill Pipeline v3 (Pipeline B)

Được thiết kế theo cấu trúc **Layered Architecture (Kiến trúc phân tầng)**, **teaches_skill_pipeline_B** là một pipeline End-to-End mạnh mẽ và tối ưu tốc độ, chuyên dùng để trích xuất và ánh xạ các kỹ năng/kiến thức từ Đề cương chi tiết học phần (Syllabus) vào Hệ thống phân loại Châu Âu (ESCO).

Pipeline là sự kết hợp hoàn hảo giữa **Năng lực truy xuất quy mô lớn (Retrieval)** và **Độ chính xác tuyệt đối của Mô hình Ngôn ngữ Lớn (LLM)**. Tốc độ xử lý trung bình cho một môn học được tối ưu ở mức **~10-15 giây** nhờ ứng dụng toàn diện cơ chế **Async Batching** và **Key Rotation**.

---

## Kiến trúc Pipeline (Layer 00 ➡️ Layer 10)

Pipeline được chia làm 6 cụm xử lý (Layers) chính, chạy tuần tự để đảm bảo độ chính xác cao nhất:

### 1. Layer 00 & 005 - Ingestion, Validation & Filter
- Đọc dữ liệu Đề cương học phần (Course Syllabus) từ các file JSON thô (bao gồm: Chuẩn đầu ra CLO, Tên bài học, Mục tiêu, Mô tả,...).
- **Course Filter**: Tự động nhận diện và loại bỏ các học phần đại cương không mang kỹ năng chuyên ngành (như *Triết học, Kinh tế, Âm nhạc, Giáo dục thể chất, Ngoại ngữ,...*) để tối ưu tài nguyên.
- Làm sạch, hợp nhất và đóng gói các đoạn văn bản hợp lệ thành các `EvidenceUnit` (Đơn vị bằng chứng).

### 2. Layer 01 - LLM Extraction 
- LLM (Gemini 3.1 Flash-Lite) đọc toàn bộ Đề cương học phần để bóc tách/trích xuất các cụm danh từ mang ý nghĩa kỹ năng/kiến thức (mentions).
- Quá trình gọi API được xử lý **bất đồng bộ (Async Batching)**. Hệ thống tự động gộp nhiều đoạn văn bản thành một request duy nhất để gọi LLM thay vì chạy tuần tự.
- Hệ thống hỗ trợ **Key Rotation**, tự động luân chuyển liên tục qua nhiều API Key khác nhau (từ `GEMINI_API_KEY1` đến `9`) khi gặp lỗi Rate Limit, đảm bảo không bao giờ bị gián đoạn.

### 3. Layer 02 & 03 - Hybrid Retrieval & RRF
- **Mục tiêu**: Tìm kiếm các kỹ năng tương đồng nhất từ bộ từ điển chuẩn ESCO với hơn 14,000 khái niệm.
- Dùng cơ chế **Hybrid Search**:
  - **FAISS (Dense Retrieval)**: Tìm kiếm theo ngữ nghĩa sử dụng vector embeddings.
  - **BM25 (Sparse Retrieval)**: Tìm kiếm theo từ khóa (Lexical search) chống thất thoát thuật ngữ hẹp.
- Hợp nhất kết quả từ 2 công cụ trên bằng thuật toán **RRF (Reciprocal Rank Fusion)** để xếp hạng sơ bộ các ứng viên (Candidates).

### 4. Layer 04 - Cross-Encoder Reranking
- Sử dụng mô hình **UniSkill (Cross-Encoder Bert)** để chấm điểm (scoring) độ tương đồng ngữ nghĩa trực tiếp giữa Cặp (Từ khóa trích xuất - Mô tả kỹ năng ESCO).
- Cross-Encoder "đọc" cả 2 văn bản cùng lúc, giúp hiểu chính xác ngữ cảnh để quyết định xem kỹ năng ESCO có thực sự khớp với từ khóa gốc hay không.
- Áp dụng mốc Threshold để phân loại quyết định dứt khoát thành **2 trạng thái nhị phân**: **ACCEPT** (Chấp nhận) hoặc **REJECT** (Từ chối). Không có trạng thái lấp lửng. Bất cứ ứng viên nào vi phạm các bộ đếm rào chắn an toàn (Guardrails) như *Security Drift*, *Domain Block* cũng sẽ bị giáng thẳng xuống **REJECT**.

### 5. Layer 05 - LLM Verification (Giám khảo LLM)
- Các kỹ năng nhóm `ACCEPT` sẽ tiếp tục đối mặt với một vòng thẩm định cuối cùng của LLM (Gemini).
- Tầng này sử dụng **Async Batching** (gộp nhiều ứng viên/request) và gửi đồng loạt lên LLM thẩm định. LLM sẽ đối chiếu nội dung môn học và mô tả ESCO, sau đó quyết định kỹ năng này có thực sự được dạy hay không.
- Bất kỳ ứng viên nào bị LLM từ chối sẽ lập tức chuyển trạng thái thành **REJECT**.

### 6. Layer 06 ➡️ 10 - Post-Processing & Export
- Chuẩn hóa (Normalization) dữ liệu lại với định dạng ESCO Metadata.
- Phân loại rạch ròi giữa Knowledge (Kiến thức) và Skill (Kỹ năng).
- Gắn vết (Provenance Tracking) để ghi lại toàn bộ quy trình và lý do chấp nhận/loại bỏ của LLM (`llm_reasoning`).
- Xuất kết quả ra thư mục (thường là `data/data_teaches_B/`) theo định dạng `JSON`, bao gồm 1 file `_summary.json` tổng quan và các file chi tiết cho từng kỹ năng. 

---

## Các công cụ / Thư viện sử dụng
- **Ngôn ngữ**: Python 3.10+
- **LLM API**: Gọi REST API bằng `httpx` (hoàn toàn bất đồng bộ), model *gemini-3.1-flash-lite*.
- **Mô hình NLP**: 
  - `sentence-transformers` (Dành cho Dense Retrieval - Paraphrase Multilingual).
  - `transformers` (Cross-Encoder / UniSkill).
- **Vector Database**: `faiss-cpu` (Truy xuất không gian đa chiều tốc độ cao).
- **Search Engine**: Thư viện `rank_bm25` cho Keyword Search.

## Cách chạy
Khởi chạy kiểm thử toàn bộ Pipeline với 4 môn học ngẫu nhiên:
```bash
python run_test.py
```
