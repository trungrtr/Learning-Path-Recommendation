# AGENT.md — Nguyên tắc bắt buộc khi triển khai pipeline

Đây là phần **tạo dữ liệu**, không phải sản phẩm cuối. Mọi output của pipeline
này sẽ được các công đoạn sau (matching, KG, ứng dụng) tin tưởng gần như
tuyệt đối, vì vậy nguyên tắc xuyên suốt là:

> **Không bao giờ để lỗi "âm thầm" trôi xuống các bước sau mà không để lại
> dấu vết truy ngược được.**

Đọc hết file này trước khi viết code cho bất kỳ module nào. Nếu một quyết
định thiết kế mâu thuẫn với nguyên tắc ở đây, dừng lại hỏi lại, không tự ý
đổi.

---

## 0. Sơ đồ tổng quan (bắt buộc giữ nguyên hướng đi)

```
LUỒNG A — Đề cương học phần (PDF scan)
raw/syllabus/*.pdf
  → [M1] PDF → MD (MinerU) + gắn cờ chất lượng OCR
  → [M2] Extraction (LangExtract + Gemini) → layer1 → layer2 canonical
  → [M3] Semantic translation sang EN
  → [M4] Trích keyword skill + ESCO linking → SkillEvidence (TEACHES_SKILL)
  → [M5] LLM tìm SUPPORTS_SKILL + human review → SkillMatch
  → [M6] Normalize → CSV → Neo4j

LUỒNG B — Chương trình đào tạo (structured, KHÔNG scan)
raw/ctdt/*.pdf|html
  → [M2] CTDT extraction trực tiếp (skip M1, không qua MinerU)
  → [M3] Translation (lightweight)
  → [M6] Normalize → CSV → Neo4j (skip M4/M5 — CTDT không có CLO để trích skill)
```

Node `HocPhan` được tạo từ Luồng B trước, sau đó Luồng A **làm giàu** bằng
skill edges. M6 merge theo `crawl_course_key`, không được tạo trùng node.

---

## 1. M1 — Gắn cờ chất lượng OCR (bắt buộc, không phải optional)

OCR tiếng Việt từ scan rất hay lỗi dấu, vỡ bảng. Nếu không chặn ở đây,
Gemini ở M2 sẽ "tự vá" câu cho mượt — tức là **bịa** mà không ai biết.

### Chỉ số tính cho mỗi file/trang, ngay sau khi MinerU trả MD

| Chỉ số | Cách tính |
|---|---|
| `table_col_mismatch` | Số cột mỗi hàng trong bảng markdown lệch với header |
| `garbled_char_ratio` | % ký tự không thuộc bảng mã tiếng Việt hợp lệ (regex) |
| `short_page_ratio` | Số từ trang / số từ trung bình các trang cùng tài liệu |
| `gemini_self_score` | (phụ, không dùng làm căn cứ chính) LLM tự chấm đoạn văn có mượt không |

### Phân loại 3 mức — KHÔNG chỉ 2 mức OK/NEEDS_REVIEW

- `OK` → tự động đi tiếp sang M2.
- `NEEDS_REVIEW` → người mở PDF gốc đối chiếu, sửa tay, đánh dấu resolved
  rồi mới cho qua M2.
- `REJECT` → lỗi quá nặng (vd. `garbled_char_ratio` > ngưỡng loại), loại
  thẳng khỏi pipeline, không tốn công review một tài liệu không đọc được.

Ngưỡng đặt trong `config.yaml`, KHÔNG hardcode — sẽ phải tinh chỉnh nhiều
lần theo chất lượng máy scan từng trường.

### Bắt buộc

- Giữ **2 bản MD riêng biệt**: `raw` (MinerU xuất thẳng) và `reviewed`
  (sau khi người sửa tay). Không ghi đè — cần so sánh lại khi nghi ngờ lỗi.
- Trường `ocr_quality` phải **đi xuyên suốt** toàn bộ pipeline, tới tận
  CSV nạp KG (giống cách `retrieval_score`, `validation_confidence` đã có
  ở M4/M5). Không dừng pipeline chờ review 100% — cho M2 chạy tiếp trên cả
  file bị flag, chỉ cần trường này đi kèm để sau này truy vết được.
- Log riêng `logs/m1_quality.jsonl` (chất lượng nội dung), tách khỏi log
  lỗi kỹ thuật gọi API MinerU. Xuất thêm 1 CSV tổng hợp chỉ liệt kê dòng
  `NEEDS_REVIEW` — đây mới là thứ người review thực sự mở, không đọc JSONL.

---

## 2. M4 — TEACHES_SKILL (dạy trực tiếp)

Bản chất: **explicit text matching** — CLO/nội dung bài học nói rõ đang
dạy kỹ năng gì, dùng embedding + FAISS + UniSkill rerank để khớp với ESCO.

### Bắt buộc

- Input phải lấy từ **cả CLO lẫn `Bai.ten_bai`** (nội dung từng bài học),
  không chỉ CLO. Người viết đề cương có thể quên ghi một kỹ năng vào CLO
  dù thực tế bài học có dạy — chỉ dùng CLO sẽ miss (false negative).
- ESCO URI **chỉ** lấy từ `esco_data/skills_en.csv`. LLM/thuật toán không
  bao giờ được tự sinh URI.
- Case điểm thấp (`< θ_low`) **không xóa hẳn** — chỉ hạ tier thành
  `low_confidence_discarded`, vẫn ghi vào log kèm điểm số. Xóa hẳn thì mất
  khả năng audit lại sau này khi phát hiện thiếu sót.
- Ngưỡng nên nghiêng về **recall cao hơn precision** — thà đưa dư ứng viên
  cho người lọc bớt ở M5, còn hơn để thuật toán tự quyết bỏ sớm không ai
  biết.

### Trường hợp 0 kết quả — phải phân biệt rõ lý do, không chỉ ghi "0 skills"

| `zero_reason` | Ý nghĩa | Xử lý |
|---|---|---|
| `no_candidates_generated` | Retrieval không sinh ứng viên nào | Với môn khối chuyên ngành/kỹ thuật → nghi vấn, ưu tiên review. Với môn đại cương (Triết học, GDTC...) → có thể là kết quả đúng, không phải lỗi |
| `all_below_threshold` | Có ứng viên nhưng bị lọc hết vì điểm thấp | Luôn đẩy sang người review — rất có thể ngưỡng đang đặt quá chặt |

Không được coi "0 skill" là lỗi mặc định hay đúng mặc định — phải log lý do
để phân biệt.

### Audit định kỳ đo recall thật (không thể tự động hóa 100%)

Chọn mẫu 15-20 học phần đã biết rõ nội dung (người trong ngành xác nhận),
kiểm tra pipeline có tìm đúng skill mà con người biết chắc là có dạy không.
Làm lại mỗi lần đổi threshold hoặc đổi embedding model — không phải làm
một lần rồi thôi.

---

## 3. M5 — SUPPORTS_SKILL (bổ trợ, gián tiếp)

Bản chất khác hẳn M4: kỹ năng bổ trợ thường **không xuất hiện trong CLO**
(vd. môn dạy theo nhóm, có báo cáo, dùng git nộp bài → phát triển "làm việc
nhóm", "version control" dù CLO không nhắc). Không thể dùng retrieval trực
tiếp như M4 — cần LLM suy luận trên ngữ cảnh rộng hơn.

### Input — KHÔNG được phụ thuộc vào TEACHES_SKILL đã có

Sai lầm cần tránh: nếu bắt SUPPORTS_SKILL phải "neo" vào TEACHES_SKILL đã
xác nhận rồi mới tra occupation, thì môn nào chưa xác nhận được
TEACHES_SKILL nào (kể cả do M4 miss, không phải do môn thực sự không dạy
gì) sẽ không tìm được SUPPORTS_SKILL luôn. Vì vậy:

- Cho LLM nguồn ngữ cảnh **độc lập**, không cần TEACHES_SKILL làm điều
  kiện tiên quyết: tên môn, mục tiêu môn học, phương pháp giảng dạy, hình
  thức đánh giá, nội dung từng bài học.
- Dùng thêm bảng quan hệ nghề nghiệp–kỹ năng có sẵn trong
  `esco_data/skill_occupation_relations.csv` làm gợi ý có cấu trúc: nếu
  môn có liên quan tới một occupation nào đó, các optional skill của
  occupation đó là ứng viên hợp lý cho SUPPORTS_SKILL — cho LLM danh sách
  ứng viên có căn cứ thay vì để nó tự sinh từ đầu.

### Chống LLM bịa skill — bắt buộc "closed-loop lookup"

LLM chỉ được **đề xuất tên bằng lời** (`skill_label` tự do), không bao giờ
được coi là nguồn cuối cùng. Quy trình bắt buộc:

1. LLM đề xuất, ví dụ `"làm việc nhóm"` — chỉ text, không URI.
2. Encode bằng **cùng embedding model** dùng ở M4, search FAISS top-K
   trong `skills_en.csv`.
3. Tính similarity giữa label LLM đề xuất và ESCO skill gần nhất.
4. Điểm dưới ngưỡng → coi là LLM bịa, loại thẳng, không tạo edge. Log
   riêng `llm_proposed_no_esco_match` để sau này biết LLM hay bịa ở loại
   môn nào, phục vụ tinh chỉnh prompt.
5. Điểm đạt ngưỡng → edge cuối cùng dùng **URI và label chính thức của
   ESCO**, KHÔNG dùng nguyên văn LLM viết.

Ngưỡng similarity cho SUPPORTS_SKILL đặt **chặt hơn** TEACHES_SKILL — tín
hiệu đầu vào (LLM suy luận tự do) đã yếu hơn CLO trực tiếp, ngưỡng lỏng sẽ
cộng dồn sai số hai lần (LLM đoán sai + match sai).

### Human review — luôn bắt buộc, không có mức auto-accept

Khác với M4 (có thể auto-accept tier HIGH), **mọi** SUPPORTS_SKILL đều
phải qua người review dù confidence LLM chấm cao — vì bản chất là suy luận
gián tiếp, dễ sai kiểu "nghe hợp lý nhưng không đúng" mà máy không tự phát
hiện được.

Log phải hiển thị **song song cả 2**: label LLM đề xuất và label ESCO đã
match, để người review thấy cả hai cạnh nhau — việc chính của người review
không phải "có nên thêm skill này" mà là "skill ESCO matched có đúng ý với
ngữ cảnh môn học không" (bắt lỗi lệch nghĩa: FAISS có thể khớp nhầm
"quản lý nhóm" thay vì "làm việc trong nhóm" dù điểm similarity cao).

---

## 4. Provenance — mọi edge bắt buộc mang theo

```
retrieval_score, rerank_score, validation_confidence,
evidence_ids[], ocr_quality (kế thừa từ M1), zero_reason (nếu có),
edge_type (TEACHES_SKILL | SUPPORTS_SKILL | REQUIRES_SKILL)
```

Mục đích: khi phát hiện một `HocPhan` có dữ liệu sai trong KG, phải lần
ngược lại được lỗi bắt nguồn từ đâu — OCR, extraction, matching, hay do
LLM suy luận — không được để lỗi "biến mất" giữa các module.

---

## 5. Nguyên tắc chung (áp dụng cho toàn bộ pipeline)

| Nguyên tắc | Thực thi |
|---|---|
| Idempotency | Module check output đã tồn tại trước khi chạy lại; dùng `content_hash` |
| Never LLM URIs | ESCO URI chỉ từ `esco_data/`; LLM chỉ đề xuất label để lookup |
| Human checkpoint | Pipeline dừng sau M5 chờ review; chỉ `decision=yes` mới tạo edge |
| Không xóa hẳn dữ liệu điểm thấp | Hạ tier + log, giữ khả năng audit lại |
| Threshold trong config, không hardcode | Cần tinh chỉnh nhiều lần theo dữ liệu thực tế |
| Two-stream merge | `HocPhan` từ Luồng B, enrich bằng skill edges từ Luồng A, merge theo `crawl_course_key` |
| Structured logging | Mọi module ghi JSONL; không dùng `print()` |

---

## 6. Việc cần làm khi bắt đầu code (thứ tự gợi ý)

1. `pipeline/schemas.py` — định nghĩa toàn bộ Pydantic model trước, bao
   gồm cả `ocr_quality`, `zero_reason` cho các schema liên quan.
2. `pipeline/m1_pdf_to_md.py` — MinerU call + 3 chỉ số + phân loại 3 mức.
3. `pipeline/m2_extraction.py`, `m3_translation.py` — theo thiết kế cũ,
   chỉ cần đảm bảo field `ocr_quality` được truyền tiếp, không bị rớt.
4. `pipeline/m4_esco_linking.py` — retrieval trên CLO + `Bai.ten_bai`,
   giữ low-tier thay vì xóa, ghi `zero_reason`.
5. `pipeline/m5_labeling.py` — input độc lập TEACHES_SKILL, closed-loop
   lookup, log song song (LLM label, ESCO matched label), không auto-accept.
6. `pipeline/m6_kg_loader.py` — đảm bảo mọi edge mang đủ trường provenance
   ở mục 4 trước khi export CSV.
