# Teaches-Skill Pipeline v3 (Pipeline B) — Revised

Được thiết kế theo cấu trúc **Layered Architecture (Kiến trúc phân tầng)**, **teaches_skill_pipeline_B** là một pipeline End-to-End mạnh mẽ và tối ưu tốc độ, chuyên dùng để trích xuất và ánh xạ các kỹ năng/kiến thức từ Đề cương chi tiết học phần (Syllabus) vào Hệ thống phân loại Châu Âu (ESCO).

Pipeline là sự kết hợp hoàn hảo giữa **Năng lực truy xuất quy mô lớn (Retrieval)** và **Độ chính xác tuyệt đối của Mô hình Ngôn ngữ Lớn (LLM)**. Tốc độ xử lý trung bình cho một môn học được tối ưu ở mức **~10-15 giây** nhờ ứng dụng toàn diện cơ chế **Async Batching** và **Key Rotation**.

---

## Kiến trúc Pipeline (Layer 00 ➡️ Layer 10)

Pipeline được chia làm 7 cụm xử lý (Layers) chính, chạy tuần tự để đảm bảo độ chính xác cao nhất:

### 1. Layer 00 & 005 — Ingestion, Validation & Filter
- Đọc dữ liệu Đề cương học phần (Course Syllabus) từ các file JSON thô (bao gồm: Chuẩn đầu ra CLO, Tên bài học, Mục tiêu, Mô tả,...).
- **Course Filter**: Tự động nhận diện và loại bỏ các học phần đại cương không mang kỹ năng chuyên ngành (như *Triết học, Kinh tế, Âm nhạc, Giáo dục thể chất, Ngoại ngữ,...*) để tối ưu tài nguyên.
- Làm sạch, hợp nhất và đóng gói các đoạn văn bản hợp lệ thành các `EvidenceUnit` (Đơn vị bằng chứng).

### 2. Layer 01 — LLM Extraction
- LLM (Gemini 3.1 Flash-Lite) đọc toàn bộ Đề cương học phần để bóc tách/trích xuất các cụm danh từ mang ý nghĩa kỹ năng/kiến thức (mentions).
- Quá trình gọi API được xử lý **bất đồng bộ (Async Batching)**. Hệ thống tự động gộp nhiều đoạn văn bản thành một request duy nhất để gọi LLM thay vì chạy tuần tự.
- Hệ thống hỗ trợ **Key Rotation**, tự động luân chuyển liên tục qua nhiều API Key khác nhau (từ `GEMINI_API_KEY1` đến `9`) khi gặp lỗi Rate Limit, đảm bảo không bao giờ bị gián đoạn.
- **[MỚI]** Ngoài mentions chính, Layer 01 đồng thời trích xuất song song **raw technical terms** (thuật ngữ kỹ thuật thô) từ cùng EvidenceUnit — các cụm từ cụ thể như tên thuật toán, công cụ, framework, khái niệm kỹ thuật hẹp ẩn trong CLO và tên bài học. Đây là nguồn đầu vào cho Layer 055.

> **Phân biệt 2 loại output của Layer 01:**
> - `Mention` — cụm từ mang nghĩa kỹ năng/kiến thức hoàn chỉnh, đủ điều kiện map thẳng vào ESCO. VD: *"machine learning", "lập trình hướng đối tượng"*
> - `RawTechnicalTerm` — thuật ngữ kỹ thuật cụ thể, ẩn bên trong CLO, không nhất thiết là skill hoàn chỉnh. VD: *"gradient descent", "scikit-learn", "backpropagation"*

### 3. Layer 02 & 03 — Hybrid Retrieval & RRF
- **Mục tiêu**: Tìm kiếm các kỹ năng tương đồng nhất từ bộ từ điển chuẩn ESCO với hơn 14,000 khái niệm.
- Dùng cơ chế **Hybrid Search**:
  - **FAISS (Dense Retrieval)**: Tìm kiếm theo ngữ nghĩa sử dụng vector embeddings.
  - **BM25 (Sparse Retrieval)**: Tìm kiếm theo từ khóa (Lexical search) chống thất thoát thuật ngữ hẹp.
- Hợp nhất kết quả từ 2 công cụ trên bằng thuật toán **RRF (Reciprocal Rank Fusion)** để xếp hạng sơ bộ các ứng viên (Candidates).
- Layer này chỉ xử lý `Mention` — không xử lý `RawTechnicalTerm`.

### 4. Layer 04 — Cross-Encoder Reranking
- Sử dụng mô hình **UniSkill (Cross-Encoder Bert)** để chấm điểm (scoring) độ tương đồng ngữ nghĩa trực tiếp giữa Cặp (Từ khóa trích xuất - Mô tả kỹ năng ESCO).
- Cross-Encoder "đọc" cả 2 văn bản cùng lúc, giúp hiểu chính xác ngữ cảnh để quyết định xem kỹ năng ESCO có thực sự khớp với từ khóa gốc hay không.
- Áp dụng mốc Threshold để phân loại quyết định dứt khoát thành **2 trạng thái nhị phân**: **ACCEPT** hoặc **REJECT**. Bất cứ ứng viên nào vi phạm các bộ đếm rào chắn an toàn (Guardrails) như *Security Drift*, *Domain Block* cũng sẽ bị giáng thẳng xuống **REJECT**.

### 5. Layer 05 — LLM Verification (Giám khảo LLM)
- Các kỹ năng nhóm `ACCEPT` sẽ tiếp tục đối mặt với một vòng thẩm định cuối cùng của LLM (Gemini).
- Tầng này sử dụng **Async Batching** và gửi đồng loạt lên LLM thẩm định. LLM đối chiếu nội dung môn học và mô tả ESCO, sau đó quyết định kỹ năng này có thực sự được dạy hay không.
- Bất kỳ ứng viên nào bị LLM từ chối sẽ lập tức chuyển trạng thái thành **REJECT**.
- Output cuối của Layer 05: danh sách `VerifiedMapping` — cặp (Mention → KyNangESCO) đã xác nhận, kèm `llm_reasoning` và `evidence_unit_id` nguồn gốc.

---

### ✨ [MỚI] Layer 055 — Concept Tag Mapper

> **Vị trí**: Chạy sau Layer 05, trước Layer 06-10.  
> **Mục đích**: Xây dựng `ConceptTag` nodes và các edges phục vụ GNN link prediction trong Knowledge Graph.

Layer này **không làm thêm bất kỳ ESCO matching nào** — nó tổng hợp lại từ dữ liệu đã có ở các layer trước để tạo ra cấu trúc bổ trợ cho GNN.

**Input nhận từ các layer trước:**

| Nguồn | Dữ liệu nhận |
|---|---|
| Layer 005 | `EvidenceUnit` — câu nguồn gốc (CLO text, tên bài) kèm `evidence_unit_id` |
| Layer 01 | `RawTechnicalTerm` — danh sách thuật ngữ kỹ thuật thô chưa qua ESCO matching |
| Layer 05 | `VerifiedMapping` — cặp (Mention → ESCO URI) đã xác nhận, kèm score và reasoning |
| Pipeline config | `pipeline_type = "teaches"` → xác định `role` trên edge |

**Quy trình xử lý bên trong Layer 055:**

```
Bước 1 — Tổng hợp ConceptTag candidates:
  Nguồn A: Mention từ VerifiedMapping (Layer 05 ACCEPT)
  Nguồn B: RawTechnicalTerm từ Layer 01
  → Union, normalize (lowercase, strip) → dedup theo tên

Bước 2 — Deduplication check:
  Kiểm tra ConceptTag "gradient descent" đã tồn tại trong store chưa?
  Nếu có → chỉ tạo edge mới, không tạo node mới

Bước 3 — Tạo EVIDENCE_FOR edges:
  Chỉ áp dụng cho Nguồn A (đã có ESCO URI từ VerifiedMapping)
  ConceptTag(mention_text) → [EVIDENCE_FOR { confidence, pipeline_source }] → KyNangESCO(uri)

Bước 4 — Tạo HAS_CONCEPT edges:
  Cho tất cả ConceptTag (cả A và B)
  HocPhan(ma) → [HAS_CONCEPT { role:"teach", source_sentence, extraction_score }] → ConceptTag
```

**Output của Layer 055:**

```
ConceptTagRecord:
  ten: "gradient descent"
  loai: "algorithm" | "tool" | "technique" | "theory"
  embedding: [...]               ← sinh tại đây

HAS_CONCEPT edge:
  role: "teach"                  ← lấy từ pipeline_type config
  source_sentence_id: "CLO_3"   ← từ EvidenceUnit nguồn
  extraction_score: 0.87

EVIDENCE_FOR edge (chỉ Nguồn A):
  esco_uri: "esco:skill/xxx"
  confidence: 0.91               ← từ VerifiedMapping
  pipeline_source: "teaches_B"
```

---

### 6. Layer 06 ➡️ 10 — Post-Processing & Export
- Chuẩn hóa (Normalization) dữ liệu lại với định dạng ESCO Metadata.
- Phân loại rạch ròi giữa Knowledge (Kiến thức) và Skill (Kỹ năng).
- Gắn vết (Provenance Tracking) để ghi lại toàn bộ quy trình và lý do chấp nhận/loại bỏ của LLM (`llm_reasoning`).
- **[MỚI]** Xuất thêm `ConceptTagRecord`, `HAS_CONCEPT edges`, `EVIDENCE_FOR edges` từ Layer 055 vào cùng thư mục output.
- Xuất kết quả ra thư mục `data/data_teaches_B/` theo định dạng `JSON`, bao gồm 1 file `_summary.json` tổng quan và các file chi tiết cho từng kỹ năng.

---

## Luồng dữ liệu tổng quan (Updated)

```
EvidenceUnit (CLO, tên bài, mục tiêu)
    │
    ├──[Mention path]──────────────────────────────────────────────────────────────────┐
    │   Layer 01 → Layer 02&03 → Layer 04 → Layer 05                                  │
    │                                           ↓                                      │
    │                                    VerifiedMapping                               │
    │                                    (Mention → ESCO URI)                          │
    │                                           │                                      │
    └──[RawTechnicalTerm path]──────────────────┤                                      │
        Layer 01 (parallel)                     │                                      │
            ↓                                   │                                      │
        RawTechnicalTerm ─────────────────► Layer 055 ──► ConceptTagRecord            │
                                                              HAS_CONCEPT {teach}      │
                                                              EVIDENCE_FOR             │
                                                                    │                  │
                                                                    ▼                  ▼
                                                              Layer 06-10 ──► Final Export
                                                                    (TEACHES_SKILL / TEACHES_KNOWLEDGE)
```

---

## Các công cụ / Thư viện sử dụng
- **Ngôn ngữ**: Python 3.10+
- **LLM API**: Gọi REST API bằng `httpx` (hoàn toàn bất đồng bộ), model *gemini-3.1-flash-lite*.
- **Mô hình NLP**:
  - `sentence-transformers` (Dành cho Dense Retrieval + sinh ConceptTag embedding).
  - `transformers` (Cross-Encoder / UniSkill).
- **Vector Database**: `faiss-cpu` (Truy xuất không gian đa chiều tốc độ cao).
- **Search Engine**: Thư viện `rank_bm25` cho Keyword Search.

## Cách chạy
Khởi chạy kiểm thử toàn bộ Pipeline với 4 môn học ngẫu nhiên:
```bash
python run_test.py
```
