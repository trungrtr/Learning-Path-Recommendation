# Định hướng Phát triển `teaches_skill_pipeline` thành Công trình Nghiên cứu Khoa học (NCKH)

Tài liệu này vạch ra lộ trình cụ thể để chuyển hóa luồng trích xuất kỹ năng (Skill Extraction & Linking) hiện tại từ một dự án kỹ thuật (Engineering Project) thành một bài báo nghiên cứu khoa học (Scientific Research Paper) chuẩn mực.

---

## 1. Đặt vấn đề và Câu hỏi Nghiên cứu (Research Questions - RQs)

Một công trình NCKH cần bắt đầu bằng việc giải quyết những "khoảng trống" (research gaps) trong các nghiên cứu trước đây. Đối với luồng này, tính mới nằm ở việc áp dụng pipeline trích xuất vào **văn bản giáo trình (Course Syllabi)** thay vì tin tuyển dụng, và việc kết hợp **Hybrid Retrieval + Cross-Encoder**.

**Các Câu hỏi Nghiên cứu đề xuất:**
*   **RQ1 (Extraction):** Việc kết hợp mô hình trích xuất chuyên dụng (SkillSpan) cải thiện hiệu năng bao nhiêu phần trăm so với việc sử dụng toàn văn (full-text) của đề cương môn học khi thực hiện ánh xạ (linking) vào ontology ESCO?
*   **RQ2 (Matching):** Phương pháp lai (Hybrid Search: BM25 + Dense Vector + Reciprocal Rank Fusion) giải quyết bài toán "từ vựng ẩn dụ/hàn lâm" trong giáo trình như thế nào so với các phương pháp đơn lẻ?
*   **RQ3 (Reranking & Decision):** Kiến trúc phân tầng với Cross-Encoder và logic Thresholding dựa trên ngữ cảnh giáo dục (môn đại cương vs. môn chuyên ngành) có thực sự giúp giảm thiểu tỷ lệ False Positives (gán sai kỹ năng) hay không?

---

## 2. Xây dựng Bộ Dữ liệu Chuẩn (Gold Standard Dataset)

🔴 **Đây là bước quan trọng nhất.** Đánh giá khoa học không thể dựa trên dữ liệu Mock (như `m4_gold_labels.csv` hiện tại).

1.  **Lấy mẫu dữ liệu (Sampling):** 
    *   Chọn ngẫu nhiên 50 - 100 đề cương môn học đại diện cho các khối ngành (IT, Kinh tế, Y tế, Kỹ thuật...).
    *   Đảm bảo bao gồm đủ các loại môn: Lý thuyết, Thực hành, Đồ án/Capstone.
2.  **Gán nhãn thủ công (Annotation):**
    *   Mời 2-3 chuyên gia (giảng viên, người xây dựng chương trình) đọc đề cương và gán các mã ESCO tương ứng (Skill/Knowledge).
3.  **Đo lường độ tin cậy (Inter-Annotator Agreement - IAA):**
    *   Sử dụng chỉ số **Cohen’s Kappa** hoặc **Fleiss’ Kappa** để chứng minh sự đồng thuận giữa các chuyên gia gán nhãn, khẳng định tính khách quan của bộ dữ liệu chuẩn.

---

## 3. Thiết lập Phương pháp luận So sánh (Baselines & Ablation Study)

Để chứng minh luồng hiện tại là ưu việt, cần thiết lập các baselines (mô hình cơ sở) để so sánh và thực hiện nghiên cứu cắt bỏ (Ablation Study) nhằm chứng minh vai trò của từng module.

### 3.1. Các Baselines đề xuất
*   **Baseline 1 (Lexical-only):** Trích xuất từ khóa bằng TF-IDF/YAKE và tìm kiếm BM25 trực tiếp vào ESCO.
*   **Baseline 2 (Dense-only):** Mã hóa toàn bộ text đề cương bằng Sentence-BERT và tìm kiếm vector (KNN).
*   **Baseline 3 (Zero-shot LLM - Tùy chọn):** Đưa đề cương vào một LLM (như ChatGPT/Llama-3) với prompt yêu cầu ánh xạ sang danh sách ESCO.

### 3.2. Ablation Study (Nghiên cứu cắt bỏ)
Tắt từng phần của luồng để xem độ chính xác giảm bao nhiêu:
*   **Cấu hình 1:** Không có tầng T1 (Bỏ SkillSpan, dùng raw text).
*   **Cấu hình 2:** Không có T3 (Bỏ RRF, chỉ dùng kết quả của một model matching).
*   **Cấu hình 3:** Không có T4 (Bỏ tầng Cross-Encoder Reranking).
*   **Cấu hình 4:** Không có logic T5 (Bỏ Thresholding theo đặc thù môn học).
*   **Mô hình đề xuất (Proposed):** Chạy full luồng kiến trúc hiện tại.

---

## 4. Đo lường và Đánh giá (Evaluation Metrics)

Sử dụng các độ đo tiêu chuẩn trong bài toán Information Extraction & Entity Linking:
1.  **Precision (P):** Tỷ lệ kỹ năng dự đoán đúng / Tổng số kỹ năng dự đoán ra. (Hệ thống có bị "nói phét" không?).
2.  **Recall (R):** Tỷ lệ kỹ năng dự đoán đúng / Tổng số kỹ năng thực sự có trong môn học. (Hệ thống có bỏ sót không?).
3.  **F1-Score:** Trung bình điều hòa của P và R.
4.  **Mean Reciprocal Rank (MRR):** (Dành riêng cho tầng Matching/Reranking) Đánh giá xem kết quả đúng có được xếp hạng ở top đầu hay không.

*(Cần cập nhật file `eval_metrics.py` để tính thêm F1-Score và MRR thay vì chỉ Precision/Recall và FP Rate như hiện tại).*

---

## 5. Phân tích Lỗi (Error Analysis) chuyên sâu

Một bài báo khoa học chất lượng cao luôn cần mổ xẻ những điểm yếu của mô hình. Phân tích tối thiểu 15-20% các trường hợp sai lệch:
*   **Phân tích False Positives (Nhận diện thừa):**
    *   *Lỗi ngữ cảnh (Context Error):* VD môn "Xử lý ngôn ngữ tự nhiên" trích ra "Ngôn ngữ học" (Linguistics) nhưng bản chất là Computer Science.
    *   *Lỗi từ vựng đa nghĩa (Polysemy):* "Python" (Lập trình) vs "Python" (Động vật).
*   **Phân tích False Negatives (Nhận diện thiếu):**
    *   *Lỗi Out-of-Vocabulary (OOV):* Các công nghệ quá mới chưa có trong bản cập nhật ESCO hiện tại (VD: "Prompt Engineering").
    *   *Lỗi diễn đạt gián tiếp:* Đề cương viết "Làm quen với các công cụ quản lý mã nguồn" (Hệ thống không link được tới "Git").

---

## 6. Điểm nhấn Tính Mới (Novelty & Contribution) để viết Bài báo

Khi viết bài, hãy nhấn mạnh vào 2 đóng góp chính của công trình này:

1.  **Kiến trúc lai End-to-End (Architectural Contribution):** Đóng góp một kiến trúc đường ống hoàn chỉnh (từ Ingestion đến Decision) kết hợp giữa Information Extraction (SkillSpan) và Hybrid Dense-Sparse Linking, giải quyết bài toán nhiễu trong văn bản dài.
2.  **Logic Quyết định dựa trên Sư phạm (Pedagogical-aware Decision Logic):** Khác biệt hoàn toàn với các nghiên cứu xử lý tin tuyển dụng (Job Postings), luồng này ứng dụng các trọng số và Thresholding khác nhau tùy thuộc vào tính chất môn học (Môn nền tảng, Môn chuyên ngành, Đồ án). Đây là một cách tiếp cận mang đậm tính "Domain Knowledge" rất được hội đồng đánh giá cao.
