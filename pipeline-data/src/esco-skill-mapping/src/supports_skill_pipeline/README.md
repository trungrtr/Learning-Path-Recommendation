# Supports Skill Pipeline (M5 - Foundational & Soft Skill Linking)

Luồng `supports_skill_pipeline` là một module trí tuệ nhân tạo chuyên biệt để bóc tách các **Kỹ năng bổ trợ, kỹ năng mềm, hoặc kỹ năng nền tảng (Foundational & Soft Skills)**. 

Khác với các kỹ năng chuyên môn cứng thường được ghi rõ rành rọt trong đề cương, các kỹ năng bổ trợ (như Tư duy logic, Làm việc nhóm, Giải quyết vấn đề) thường chỉ được đề cập ngầm định (implicitly). Do đó, luồng này sử dụng sức mạnh suy luận của LLM (Large Language Models) kết hợp với các thuật toán tìm kiếm đa kênh để tìm ra chúng.

---

## 🚀 Công Nghệ Cốt Lõi (Core Technologies)

1. **LLM Reasoning (Suy luận bằng LLM)**:
   - Sử dụng `google-genai` (Gemini 2.5 Flash / Pro).
   - Nhiệm vụ: Đọc toàn bộ ngữ cảnh của khóa học và suy luận ra các "Concept" kỹ năng mềm/nền tảng ẩn dưới bề mặt văn bản. LLM ở đây không map trực tiếp vào ESCO để tránh ảo giác, mà chỉ đóng vai trò "gợi ý ý tưởng".
2. **Multi-Channel Retrieval (Tìm kiếm đa kênh)**:
   - Thay vì chỉ dùng 1 bộ tìm kiếm, hệ thống dùng 3 kênh độc lập để quét từ điển ESCO: **FAISS** (Tìm theo ngữ nghĩa vector), **BM25** (Tìm theo từ khóa thô), và **ESCOXLM-R** (Mô hình tinh chỉnh riêng).
3. **Reciprocal Rank Fusion (RRF)**:
   - Nhiệm vụ: Hợp nhất và xếp hạng lại (Fusion & Ranking) kết quả từ 3 kênh tìm kiếm trên. Ứng viên nào xuất hiện trên cả 3 kênh với thứ hạng cao sẽ được đẩy lên Top 1.

---

## 🏗 Kiến Trúc 7 Bước (7-Step Pipeline)

Quy trình xử lý hoàn toàn tự động (Auto-Accept) từ việc đọc dữ liệu đến khi xuất file:

*   **S1 (Preprocessing):** Gom toàn bộ văn bản (Mô tả, Mục tiêu, CLO) của một học phần thành một khối ngữ cảnh (Context) duy nhất.
*   **S2 (Concept Extraction):** Bơm Context vào LLM kèm Prompt chuyên biệt để LLM "rút trích" ra danh sách các khái niệm kỹ năng bổ trợ thô (Raw Concepts).
*   **S3 (Candidate Retrieval):** Mang các Raw Concepts này đi quét trong ESCO database qua 3 kênh (FAISS, BM25, ESCOXLM-R).
*   **S4 (RRF Fusion):** Hợp nhất kết quả từ 3 kênh để lọc bỏ nhiễu.
*   **S5 (Multi-signal Ranking):** Chấm điểm lại các ứng viên dựa trên công thức đa tín hiệu (Tổng hợp điểm RRF + Điểm Model + Điểm Evidence).
*   **S6 (Auto-Accept & JSON Export):** Tự động dán nhãn phê duyệt (Accepted) cho các ứng viên Top K (mặc định K=10) và xuất ra file JSON chuẩn.
*   **S7 (Neo4j Export):** Tự động sinh các câu lệnh Cypher để import thẳng vào Graph Database (Neo4j).

---

## 📁 Cấu Trúc Đầu Ra (Output Structure)

Dữ liệu đầu ra của luồng này được lưu tại `../../data/data_support_skill/` (tính từ gốc `src/`).

```text
data/data_support_skill/
├── IT6204/                                       
│   ├── knowledge__structured_thinking.json       # Bằng chứng & ESCO Concept của một Kiến thức nền tảng
│   └── skill__logical_reasoning.json             # Bằng chứng & ESCO Concept của một Kỹ năng mềm
├── IT6208/
├── _cypher/                                      
│   └── IT6204__supports.cypher                   # Các lệnh Neo4j (MERGE) tự động sinh
└── _review/                                      
    └── (Các thư mục dùng cho human-review nếu cần thiết)
```

---

## ⚙️ Hướng Dẫn Cấu Hình (Configuration)

Mọi thông số trọng yếu được quản lý tập trung tại `configs/default_config.yaml`.
*   **Cấu hình LLM**: Bạn có thể đổi mô hình (ví dụ từ `gemini-2.5-flash` sang `gemini-2.5-pro` để suy luận sâu hơn) hoặc chỉnh `temperature` (hiện tại set bằng `0.0` để tối ưu tính nhất quán).
*   **Top K (Giới hạn số lượng)**: Số lượng kỹ năng bổ trợ tối đa trả về cho một học phần (Mặc định: 10). Bạn có thể tăng lên nếu muốn lấy rộng hơn.

---

## 💻 Cách Chạy (Execution)

Bạn có thể chạy luồng này độc lập (với điều kiện đã setup PYTHONPATH trỏ vào `src/`):

```bash
# Đứng tại thư mục esco-skill-mapping/
$env:PYTHONPATH="src"
python src/supports_skill_pipeline/pipeline.py
```
