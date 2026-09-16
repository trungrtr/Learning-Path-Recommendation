# `teaches-skill` — Kiến trúc & Đặc tả công nghệ (v3)

> Bản này viết lại toàn bộ bằng tiếng Việt, cập nhật đúng theo định dạng dữ liệu đầu vào thực tế (4 file JSON/1 học phần), và thiết kế lại Tầng 1 theo hướng ensemble NLP mà tao đã chốt (ESCOXLM-R + esco-extract-skill + SkillSpan + LLM fallback), cùng toàn bộ các tầng phía sau.

---

# 0. Thay đổi so với bản trước (v2) — đọc trước khi vào chi tiết

## 0.1 Những gì thay đổi

| # | Nội dung | Bản v2 | Bản v3 | Lý do |
|---|---|---|---|---|
| 1 | Ngôn ngữ | Tiếng Anh | **Tiếng Việt toàn bộ** | Theo yêu cầu |
| 2 | Input Contract | Giả định 1 file JSON gộp (course_description, clos[], lessons[]) | **4 file JSON tách riêng/học phần**: `hoc_phan.json`, `clo.json`, `bai_hoc.json`, `muc_tieu.json`, join qua `ma_hoc_phan` + `source_hash` | Khớp đúng dữ liệu Layer 2 output thật đã upload (IT6204) |
| 3 | Evidence Builder | 3 loại: DESCRIPTION, CLO, LESSON | **4 loại**: MO_TA, MUC_TIEU (mới), CLO, BAI_HOC | Dữ liệu thật có thêm "mục tiêu học phần" (G1/G2/G3) là 1 nguồn evidence độc lập, song song với CLO, không lồng trong CLO |
| 4 | Tầng 1 (Extraction) | LLM là chính, ESCOXLM-R/SkillSpan là tùy chọn/nghiên cứu | **Ensemble 4 nguồn chạy song song**: ESCOXLM-R (2 checkpoint riêng cho skill & knowledge) + esco-extract-skill + SkillSpan (bổ sung) + LLM fallback (chỉ gọi khi 3 nguồn kia không ra kết quả) | Theo yêu cầu mới + phát hiện quan trọng ở mục 0.2 bên dưới |
| 5 | Mới | — | **Tầng 7 (Skill vs Knowledge) dùng thêm tín hiệu từ `loai_muc_tieu`** và từ nhánh extraction (skill-head vs knowledge-head) làm tín hiệu phụ trợ, ESCO `skill_type` vẫn là nguồn quyết định cuối | Dữ liệu `muc_tieu.json` có sẵn nhãn KIEN_THUC/KY_NANG/TU_CHU_TRACH_NHIEM — tín hiệu quý, nên tận dụng |
| 6 | Mới | — | **Trọng số evidence khi tổng hợp (Tầng 9)**: bài học thường chỉ có tiêu đề (không có nội dung tóm tắt) → tin cậy thấp hơn mô tả/mục tiêu/CLO | Quan sát từ dữ liệu thật: toàn bộ `noi_dung_tom_tat` trong `bai_hoc.json` là `null` |

## 0.2 Phát hiện quan trọng cần đính chính (từ tra cứu thực tế)

Ở bản v2 mình từng nhận định ESCOXLM-R không có sẵn "đầu" trích xuất (extraction head) và phải fine-tune mới dùng được — **nhận định đó chưa chính xác**. Tra cứu lại cho thấy nhóm tác giả ESCOXLM-R đã công bố **2 checkpoint token-classification dùng được ngay** (chỉ cần inference, không cần train thêm):

- `jjzha/escoxlmr_skill_extraction` — trích **skill span** trực tiếp từ văn bản
- `jjzha/escoxlmr_knowledge_extraction` — trích **knowledge span** trực tiếp từ văn bản

Đây là tin tốt kép: (1) chạy inference-only nên **không cần GPU** (chỉ chậm hơn trên CPU, model ~2.2GB, nhưng với quy mô 2 CTDT hiện tại thì hoàn toàn khả thi); (2) hai checkpoint tách sẵn skill/knowledge **khớp thẳng** với việc phân nhánh `TEACHES_SKILL`/`TEACHES_KNOWLEDGE` sau này.

Với SkillSpan, tra cứu cho thấy nhóm tác giả có công bố các model pretrain miền job-posting (`jjzha/jobbert-base-cased`, `jjzha/jobspanbert-base-cased`) và có 1 demo trích xuất skill trực tuyến, nhưng **chưa xác nhận chắc chắn** có checkpoint token-classification tải về dùng ngay tương đương 2 checkpoint ESCOXLM-R ở trên hay không. Vì vậy SkillSpan trong v3 này được xếp là **nguồn bổ sung, độ ưu tiên thấp hơn**, cần nhóm tự kiểm tra lại repo/demo trước khi đưa vào production, đồng thời vẫn giữ cảnh báo lệch domain cũ (job posting vs. văn bản học phần).

---

# 1. Mục đích

`teaches-skill` là thành phần ánh xạ kỹ năng/kiến thức trong pipeline Knowledge Graph học phần.

Nhiệm vụ:

> Từ nội dung học phần đã làm sạch và dịch sang tiếng Anh (CLO, bài học, mục tiêu, mô tả học phần), ánh xạ sang các concept ESCO chuẩn (skill/knowledge), rồi xuất quan hệ `TEACHES_SKILL` / `TEACHES_KNOWLEDGE` vào Knowledge Graph.

### Không thuộc phạm vi (đã xử lý ở tầng trên, trong `extract-translate-data`)

- Parse PDF, OCR, tách layout văn bản gốc
- Làm sạch, dịch thuật syllabus thô
- Trích mã học phần từ PDF, trích tiên quyết từ syllabus

---

# 2. Kiến trúc tổng thể (v3)

```text
Layer 2 Output
(4 file JSON / học phần — đã sạch + tiếng Anh + có cấu trúc)
        |
        v
+-------------------------------+
| Tầng 0. Kiểm tra đầu vào       |
|         Python + Pydantic      |
+-------------------------------+
        |
        v
+-------------------------------+
| Tầng 0.5. Evidence Builder     |
|   MO_TA / MUC_TIEU / CLO /     |
|   BAI_HOC                      |
+-------------------------------+
        |
        v
+---------------------------------------------------+
| TẦNG 1 — Sinh ứng viên bằng NLP (ensemble 4 nguồn) |
|                                                      |
|  ESCOXLM-R        ESCOXLM-R      esco-extract-skill |
|  (skill head)   (knowledge head)                    |
|       |                |                 |          |
|       +-------+--------+                 |          |
|               |                          |          |
|          SkillSpan (bổ sung)             |          |
|               |                          |          |
|               +----------- LLM fallback -+          |
|                  (chỉ gọi khi 3 nguồn trên rỗng)     |
+---------------------------------------------------+
        |
        v
  Mention thô  +  ESCO candidate trực tiếp (từ esco-extract-skill)
        |
        v
+-------------------------------+
| Tầng 2 — Match mention → ESCO  |
|   BM25 + Dense (FAISS)         |
+-------------------------------+
        |
        v
+-------------------------------+
| Tầng 3 — Hợp nhất (RRF)        |
+-------------------------------+
        |
        v
                Top-K ESCO
        |
        v
+-------------------------------+
| Tầng 4 — Rerank                |
|   Cross-Encoder UniSkill       |
|   (pretrained, không fine-tune)|
+-------------------------------+
        |
        v
+-------------------------------+
| Tầng 5 — Quyết định ngưỡng     |
|   (chiến lược ít dữ liệu)      |
+-------------------------------+
        |
        v
+-------------------------------+
| Tầng 6 — Chuẩn hóa ESCO        |
|   URI / Label / skill_type     |
+-------------------------------+
        |
        v
+-------------------------------+
| Tầng 7 — Phân loại Skill vs    |
|   Knowledge (ESCO + tín hiệu   |
|   phụ trợ từ mục tiêu/nhánh    |
|   trích xuất)                  |
+-------------------------------+
        |
        v
+-------------------------------+
| Tầng 8 — Provenance            |
+-------------------------------+
        |
        v
+-------------------------------+
| Tầng 9 — Tổng hợp Evidence →   |
|   Học phần (dedup, trọng số    |
|   theo loại evidence)          |
+-------------------------------+
        |
        v
+-------------------------------+
| Tầng 10 — Xuất KG (Neo4j)      |
|   TEACHES_SKILL /               |
|   TEACHES_KNOWLEDGE             |
+-------------------------------+
```

---

# 3. Input Contract (đúng theo dữ liệu thật)

Mỗi học phần gồm **4 file JSON riêng biệt**, liên kết với nhau qua `ma_hoc_phan` và `source_hash`. Ví dụ minh họa: học phần `IT6204`.

## 3.1 `<ma_hoc_phan>__hoc_phan.json` — thông tin học phần (object, không phải array)

| Field | Vai trò trong pipeline |
|---|---|
| `ma_hoc_phan` | Khóa join chính giữa 4 file |
| `ten_vi`, `ten_en` | Tên học phần (hiển thị / đối chiếu) |
| `mo_ta_tom_tat`, `mo_ta_tom_tat_en` | → nguồn evidence loại **MO_TA** (dùng bản `_en` cho extraction) |
| `so_tin_chi_tong` | Metadata, không dùng cho extraction |
| `ctdt_memberships[]` | Thông tin chương trình đào tạo chứa học phần này (ma_ctdt, nhom_id, loai_nhom...) — dùng cho lọc theo 30 ngành, không phải evidence text |
| `source_hash` | Khóa join phụ, đối chiếu tính toàn vẹn giữa 4 file |

## 3.2 `<ma_hoc_phan>__clo.json` — danh sách CLO (array)

| Field | Vai trò |
|---|---|
| `ma_cdr_goc` | Mã CLO (vd `L1`, `L2`, `L3`) — dùng để nối ngược từ `bai_hoc.ma_clo` |
| `noi_dung`, `noi_dung_en` | → nguồn evidence loại **CLO** |
| `pi_so[]` | Chỉ số chương trình liên quan (program indicator) — metadata, giữ trong provenance, không dùng cho extraction |
| `muc_do` | **Chưa rõ ngữ nghĩa** (ví dụ thấy giá trị `"IT"` ở cả 3 CLO) — cần hỏi lại nhóm/tài liệu CTDT gốc trước khi gán vai trò cho field này trong pipeline; tạm thời chỉ lưu như metadata, không dùng để quyết định logic |

## 3.3 `<ma_hoc_phan>__bai_hoc.json` — danh sách bài học (array)

| Field | Vai trò |
|---|---|
| `ten_bai`, `ten_bai_en` | → nguồn evidence loại **BAI_HOC** |
| `noi_dung_tom_tat`, `noi_dung_tom_tat_en` | Nội dung chi tiết bài học — **quan sát thực tế: luôn `null`** trong dữ liệu hiện có, nghĩa là evidence của bài học chỉ còn lại tiêu đề (ngắn) |
| `ma_clo[]` | Liên kết tới CLO (0, 1 hoặc nhiều mã) — dùng để nối provenance bài học → CLO tương ứng; có thể rỗng (bài học không gắn CLO nào, vd "Bài tập tổng hợp") |

## 3.4 `<ma_hoc_phan>__muc_tieu.json` — mục tiêu học phần (array)

| Field | Vai trò |
|---|---|
| `ma_muc_tieu` | Mã mục tiêu (G1, G2, G3...) — có thể `null` |
| `loai_muc_tieu` | `KIEN_THUC` \| `KY_NANG` \| `TU_CHU_TRACH_NHIEM` — **tín hiệu quan trọng**, dùng làm gợi ý phụ trợ ở Tầng 7 (Skill vs Knowledge) |
| `noi_dung`, `noi_dung_en` | → nguồn evidence loại **MUC_TIEU** |
| `so_ctdt[]` | Trong dữ liệu ví dụ luôn rỗng — không có liên kết trực tiếp giữa mục tiêu và CLO |

## 3.5 Ghi chú quan trọng về dữ liệu thật

1. **Mục tiêu (muc_tieu) và CLO là hai nguồn evidence song song**, không lồng nhau — không có field nào nối trực tiếp `muc_tieu` với `clo` trong dữ liệu hiện có.
2. **Bài học phần lớn chỉ có tiêu đề**, không có nội dung tóm tắt → độ giàu thông tin thấp hơn hẳn 3 loại evidence còn lại → cần trọng số thấp hơn khi tổng hợp (xem Tầng 9).
3. Luôn ưu tiên field `_en` cho extraction/matching (ESCO là taxonomy tiếng Anh), giữ field tiếng Việt gốc (`noi_dung`, `ten_bai`, `mo_ta_tom_tat`...) chỉ để hiển thị và phục vụ human review bằng tiếng Việt.
4. `muc_do: "IT"` trong CLO — chưa xác định được ý nghĩa, **cần xác nhận với nhóm** trước khi dùng trong logic bất kỳ.

---

# 4. Tầng 0 — Kiểm tra đầu vào

- Python 3.x + Pydantic v2, validate cả 4 file cùng lúc theo `ma_hoc_phan`, kiểm tra chéo `source_hash` khớp nhau giữa 4 file (phát hiện lệch phiên bản dữ liệu).
- Cấu hình YAML, logging chuẩn, test bằng `pytest`.
- Không cần LLM ở tầng này.

---

# 5. Tầng 0.5 — Evidence Builder (cập nhật: 4 loại evidence)

```text
Học phần (IT6204)
 |
 +-- MO_TA        (1 evidence, từ hoc_phan.mo_ta_tom_tat_en)
 |
 +-- MUC_TIEU
 |     +-- G1 (KIEN_THUC)
 |     +-- G2 (KY_NANG)
 |     +-- G3 (TU_CHU_TRACH_NHIEM)
 |
 +-- CLO
 |     +-- L1
 |     +-- L2
 |     +-- L3
 |
 +-- BAI_HOC
       +-- "Overview of..." (ma_clo: [L1])
       +-- "System Requirements Elicitation" (ma_clo: [])
       +-- ... (ma_clo: [L1, L2] hoặc [L2, L3] hoặc [L3]...)
```

Ví dụ cụ thể (dùng đúng dữ liệu IT6204 đã upload):

```json
{
  "evidence_id": "IT6204_MUCTIEU_G2",
  "course_code": "IT6204",
  "source_type": "MUC_TIEU",
  "source_id": "G2",
  "text": "Apply the analysis and design process, use software design tools and the UML language to model a specific software system, and develop technical design documents and software solution designs that meet requirements. Apply teamwork skills to achieve learning objectives.",
  "meta": { "loai_muc_tieu": "KY_NANG" }
}
```

```json
{
  "evidence_id": "IT6204_BAIHOC_05",
  "course_code": "IT6204",
  "source_type": "BAI_HOC",
  "source_id": "L05",
  "text": "System Structural Analysis Using Class Diagrams",
  "meta": { "linked_clo": ["L2", "L3"], "content_richness": "title_only" }
}
```

Trường `content_richness: "title_only"` được gắn tự động khi `noi_dung_tom_tat_en` là `null` — dùng ở Tầng 9 để hạ trọng số.

Công nghệ: Python + Pydantic, xử lý rule-based, không cần model ML — giống v2.

---

# 6. TẦNG 1 — Sinh ứng viên bằng NLP (ensemble 4 nguồn)

## Mục tiêu

Với mỗi evidence unit, chạy song song 4 nguồn để tối đa hóa recall của tập ứng viên, trước khi đưa qua các bước match/rerank/quyết định.

## 6.1 Nguồn A — ESCOXLM-R (2 checkpoint, dùng ngay không cần fine-tune)

```text
Evidence text (_en)
     |
     +----------------------------+
     |                             |
     v                             v
jjzha/escoxlmr_skill_extraction   jjzha/escoxlmr_knowledge_extraction
     |                             |
     v                             v
 Skill mention(s)              Knowledge mention(s)
```

- Cả hai đều là model **token-classification**, chạy inference trực tiếp, không cần train thêm.
- Vì tách sẵn skill/knowledge ngay tại bước trích xuất, **gắn nhãn nguồn** (`from_head: skill` hay `from_head: knowledge`) vào mỗi mention để dùng làm tín hiệu phụ trợ ở Tầng 7.
- Model khá nặng (~2.2GB/checkpoint) — chạy CPU vẫn ổn với quy mô 2 CTDT hiện tại, nhưng nên có cache theo `evidence_id` để không phải chạy lại khi lặp pipeline lúc refactor.

## 6.2 Nguồn B — `esco-extract-skill`

```text
Evidence text
     |
     v
esco-extract-skill (runtime candidate generation)
     |
     v
ESCO candidate (URI trực tiếp, không qua bước mention trung gian)
```

- Đây là công cụ nội bộ đã có sẵn — không cần train, không cần model bên ngoài.
- Vì trả thẳng ESCO URI, nguồn này **bỏ qua Tầng 2 (match)**, đi thẳng vào Tầng 3 (fusion).

## 6.3 Nguồn C — SkillSpan (bổ sung, độ ưu tiên thấp hơn)

```text
Evidence text
     |
     v
Model miền job-posting (JobBERT/JobSpanBERT hoặc checkpoint
NER đã fine-tune tương ứng — CẦN NHÓM XÁC NHẬN checkpoint cụ thể
trước khi dùng production)
     |
     v
Mention thô (độ tin cậy thấp hơn, do lệch domain job-posting
vs. văn bản học phần)
```

- Dùng như nguồn **bổ sung recall**, không phải nguồn chính.
- Gắn nhãn nguồn `from_source: skillspan` để Tầng 9/Tầng 5 có thể hạ trọng số/độ tin cậy khi cần.

## 6.4 Nguồn D — LLM fallback (chỉ gọi khi cần)

```text
IF (Nguồn A + Nguồn B + Nguồn C đều rỗng)
   OR (không có ứng viên nào từ Nguồn B đạt ngưỡng tối thiểu)
THEN
   gọi LLM (qua API, JSON schema ràng buộc) để trích mention
```

- Giữ nguyên nguyên tắc cũ: LLM không được tự quyết định ESCO URI hay skill/knowledge type, chỉ đề xuất chuỗi mention.
- Vì chỉ gọi khi cần (fallback thật sự, không chạy cho mọi evidence), chi phí API được kiểm soát tốt.
- Cache theo `evidence_id` + phiên bản prompt để tránh gọi lại khi re-run pipeline.

## 6.5 Output của Tầng 1

Hai loại đối tượng, đều mang theo nhãn nguồn để phục vụ provenance và trọng số về sau:

- **Mention thô** (từ Nguồn A, C, D) → cần đưa tiếp qua Tầng 2 để tìm ESCO URI tương ứng.
- **ESCO candidate trực tiếp** (từ Nguồn B) → đi thẳng vào Tầng 3.

---

# 7. Tầng 2 — Match mention → ESCO candidate

Không đổi về nguyên lý so với bản v2 (chỉ áp dụng cho mention thô, không áp dụng cho candidate đã có URI từ `esco-extract-skill`):

- **BM25** (`rank_bm25`) trên `preferred_label + alternative_labels + description` của ESCO — mạnh với thuật ngữ chính xác.
- **Dense retrieval** (Sentence-Transformers, model nhỏ chạy CPU tốt, ví dụ `all-MiniLM-L6-v2`) + **FAISS** — mạnh với tương đồng ngữ nghĩa.
- Cả hai chạy trên tập ESCO đã lọc theo 30 ngành sẵn có.

---

# 8. Tầng 3 — Hợp nhất bằng RRF (nhiều kênh)

```text
                    Mention / Evidence
                            |
        +----------+--------+--------+-----------+
        |          |                 |           |
        v          v                 v           v
      BM25       Dense          esco-extract-   (ứng viên đã
   (Tầng 2)     (Tầng 2)          skill (B)      có URI, đưa
                                                  thẳng vào đây)
        |          |                 |           |
        +----------+--------+--------+-----------+
                            |
                            v
                          RRF
                            |
                            v
                   Top-K ứng viên ESCO
```

Công thức RRF không đổi, vẫn tổng quát cho N kênh:

```text
RRF(d) = Σ_i 1 / (k + rank_i(d))
```

Cài đặt thuần Python, không cần thư viện ngoài.

---

# 9. Tầng 4 — Rerank bằng Cross-Encoder

Không đổi so với v2 — phần này đã đúng với ràng buộc không GPU:

- Baseline: `cross-encoder/ms-marco-MiniLM-L6-v2`.
- Production: **UniSkill Cross-Encoder pretrained**, chỉ inference, không fine-tune (vì 2 CTDT hiện có nằm trong domain gốc của UniSkill). Chỉ cân nhắc fine-tune khi có GPU + dữ liệu CTDT ngành ngoài CNTT.
- Chỉ rerank Top-K (20–50) mỗi evidence unit → chi phí CPU nhỏ dù model tương đối lớn.

---

# 10. Tầng 5 — Quyết định ngưỡng (chiến lược ít dữ liệu)

Không đổi nguyên lý so với v2:

1. Chạy Cross-Encoder cho toàn bộ cặp evidence–candidate của 2 CTDT hiện có, quan sát phân phối điểm số để chọn `T_high`/`T_low` ban đầu (điểm gãy/elbow, hoặc theo percentile).
2. Human spot-check có chọn lọc ở dải điểm biên (quanh threshold), không label toàn bộ.
3. Đối chiếu với nhãn đã có từ vòng review M5 (nếu có) như một bước sanity-check.
4. Lưu threshold trong `configs/decision.yaml`, coi là tạm thời, hiệu chỉnh lại khi có thêm CTDT ngành khác.

```text
score >= T_high        -> ACCEPT
T_low <= score < T_high -> REVIEW / CHƯA CHẮC
score < T_low           -> REJECT
```

---

# 11. Tầng 6 — Chuẩn hóa ESCO

Không đổi — URI/label/skill_type luôn lấy từ ESCO index, không bao giờ để LLM tự sinh.

---

# 12. Tầng 7 — Phân loại Skill vs Knowledge (cập nhật: thêm tín hiệu phụ trợ)

## Nguyên tắc

**ESCO `skill_type` vẫn là nguồn quyết định cuối cùng** (canonical) — không đổi so với v2. Nhưng giờ có thêm 2 tín hiệu phụ trợ để phát hiện các trường hợp cần review thêm:

1. **Nhãn từ nhánh trích xuất ở Tầng 1** — mention đến từ `escoxlmr_skill_extraction` hay `escoxlmr_knowledge_extraction`.
2. **`loai_muc_tieu`** của evidence gốc (nếu evidence là loại MUC_TIEU) — `KIEN_THUC` gợi ý nghiêng về knowledge, `KY_NANG` gợi ý nghiêng về skill, `TU_CHU_TRACH_NHIEM` (tự chủ/trách nhiệm) hiện chưa có quan hệ ESCO tương ứng rõ ràng — **cần bàn thêm** có nên tạo quan hệ thứ 3 (ví dụ `DEVELOPS_ATTRIBUTE`) hay bỏ qua loại mục tiêu này khỏi phạm vi `teaches-skill`.

## Xử lý mismatch

```text
Ví dụ: mention đến từ escoxlmr_skill_extraction (tín hiệu: skill)
        nhưng ESCO gắn concept khớp có skill_type = "knowledge"
        -> đánh dấu "review" thay vì tự động accept,
           dù điểm Cross-Encoder cao
```

Đây là bổ sung mới so với v2, tận dụng chính việc tách sẵn 2 checkpoint ở Tầng 1 làm một lớp kiểm tra chéo miễn phí.

---

# 13. Tầng 8 — Provenance & Explainability

Cập nhật thêm các trường nguồn gốc (so với v2):

```json
{
  "course_code": "IT6204",
  "esco_uri": "http://data.europa.eu/esco/skill/...",
  "preferred_label": "Design database systems",
  "type": "skill",
  "confidence": 0.94,
  "evidence": [
    {
      "source_type": "MUC_TIEU",
      "source_id": "G2",
      "text": "...",
      "meta": { "loai_muc_tieu": "KY_NANG" }
    }
  ],
  "extraction": {
    "source": "escoxlmr_skill_extraction",
    "matched_head_type": "skill",
    "esco_type_agrees": true
  },
  "retrieval": {
    "bm25_rank": 2,
    "dense_rank": 1,
    "esco_extract_skill_rank": null,
    "rrf_rank": 1
  },
  "model": { "cross_encoder_score": 0.94 }
}
```

---

# 14. Tầng 9 — Tổng hợp Evidence → Học phần (cập nhật: trọng số theo loại evidence)

## Nguyên tắc gộp (giữ nguyên từ v2)

Gộp theo `(course_code, esco_uri)`, giữ toàn bộ evidence đóng góp, không chỉ giữ evidence điểm cao nhất.

## Bổ sung mới — trọng số theo độ giàu thông tin của evidence

Vì dữ liệu thật cho thấy **BAI_HOC** thường chỉ có tiêu đề (không nội dung), nên khi tổng hợp:

| Loại evidence | Độ giàu thông tin | Vai trò khi tổng hợp |
|---|---|---|
| MO_TA | Cao (mô tả đầy đủ) | Nguồn chính |
| MUC_TIEU | Cao (câu văn đầy đủ, có nhãn skill/knowledge sẵn) | Nguồn chính, ưu tiên cao nhất nhờ có `loai_muc_tieu` |
| CLO | Cao | Nguồn chính |
| BAI_HOC (có nội dung) | Trung bình | Nguồn hỗ trợ |
| BAI_HOC (chỉ có tiêu đề — `content_richness: title_only`) | Thấp | **Chỉ mang tính hỗ trợ/củng cố** — không nên là bằng chứng duy nhất để accept một skill nếu không có CLO/mục tiêu nào xác nhận thêm |

Ví dụ với dữ liệu IT6204: bài học "System Structural Analysis Using Class Diagrams" (chỉ có tiêu đề, gắn CLO L2+L3) nên được coi là bằng chứng củng cố cho skill đã được CLO L2/L3 xác nhận, không phải nguồn độc lập để tạo cạnh `TEACHES_SKILL` mới nếu CLO chưa xác nhận điều đó.

---

# 15. Tầng 10 — Xuất Knowledge Graph

Không đổi so với v2 — `TEACHES_SKILL` / `TEACHES_KNOWLEDGE`, thuộc tính gồm confidence, danh sách evidence_id đóng góp, method.

```cypher
MATCH (c:Course {code: "IT6204"})
MATCH (s:ESCOConcept {uri: "http://data.europa.eu/esco/skill/..."})
CREATE (c)-[:TEACHES_SKILL {
    confidence: 0.94,
    evidence_ids: ["IT6204_MUCTIEU_G2", "IT6204_CLO_L3"],
    method: "ESCOXLM-R+esco-extract-skill+UniSkill-CrossEncoder"
}]->(s);
```

---

# 16. Cấu trúc repo đề xuất (cập nhật)

```text
teaches-skill/
│
├── configs/
│   ├── model.yaml
│   ├── esco.yaml
│   ├── retrieval.yaml
│   └── decision.yaml
│
├── data/
│   ├── input/            # 4 file JSON / học phần
│   ├── esco/
│   ├── uniskill/
│   └── processed/
│
├── cache/
│   ├── llm_extraction/
│   └── model_inference/   # cache output của ESCOXLM-R / SkillSpan theo evidence_id
│
├── src/
│   ├── ingestion/
│   │   └── validator.py           # validate + đối chiếu source_hash giữa 4 file
│   │
│   ├── evidence/
│   │   └── builder.py             # 4 loại: MO_TA, MUC_TIEU, CLO, BAI_HOC
│   │
│   ├── extraction/
│   │   ├── escoxlmr_skill.py      # jjzha/escoxlmr_skill_extraction
│   │   ├── escoxlmr_knowledge.py  # jjzha/escoxlmr_knowledge_extraction
│   │   ├── skillspan.py           # nguồn bổ sung, cần xác nhận checkpoint
│   │   ├── llm_fallback.py
│   │   └── extractor.py           # điều phối 4 nguồn + logic fallback
│   │
│   ├── esco/
│   │   ├── loader.py
│   │   ├── normalizer.py
│   │   └── taxonomy.py
│   │
│   ├── retrieval/
│   │   ├── bm25.py
│   │   ├── bi_encoder.py
│   │   ├── faiss_index.py
│   │   ├── esco_extract_skill_client.py
│   │   └── hybrid.py
│   │
│   ├── fusion/
│   │   └── rrf.py
│   │
│   ├── reranking/
│   │   └── cross_encoder.py
│   │
│   ├── decision/
│   │   ├── threshold.py
│   │   └── calibration.py
│   │
│   ├── classification/            # MỚI
│   │   └── skill_vs_knowledge.py  # ESCO skill_type + tín hiệu phụ trợ
│   │
│   ├── aggregation/
│   │   └── course_rollup.py       # có trọng số theo loại evidence
│   │
│   ├── provenance/
│   │   └── tracker.py
│   │
│   └── export/
│       ├── json.py
│       └── neo4j.py
│
├── training/    # chỉ cho tương lai (khi có GPU + dữ liệu ngành ngoài CNTT)
├── evaluation/
├── tests/
├── requirements.txt
├── pyproject.toml
└── README.md
```

---

# 17. Bảng công nghệ tổng hợp

| Tầng | Công nghệ chính | Tham chiếu | Cần GPU? |
|---|---|---|---|
| Kiểm tra đầu vào | Python + Pydantic | — | Không |
| Evidence Builder | Python | — | Không |
| Tầng 1 — Nguồn A | `jjzha/escoxlmr_skill_extraction`, `jjzha/escoxlmr_knowledge_extraction` | Hugging Face | Không (inference-only) |
| Tầng 1 — Nguồn B | `esco-extract-skill` | nội bộ | Không |
| Tầng 1 — Nguồn C | SkillSpan (JobBERT/JobSpanBERT) | cần xác nhận checkpoint | Không (inference-only, nếu có checkpoint phù hợp) |
| Tầng 1 — Nguồn D | LLM qua API | nhà cung cấp đã chọn | Không |
| Tầng 2 | BM25 (`rank_bm25`) + Sentence-Transformers + FAISS | — | Không |
| Tầng 3 | RRF (tự cài) | — | Không |
| Tầng 4 | Cross-Encoder UniSkill (pretrained) | LREC 2026 | Không |
| Tầng 5 | Percentile/elbow + human spot-check | — | Không |
| Tầng 6 | ESCO API/local index | ESCO | Không |
| Tầng 7 | ESCO `skill_type` + tín hiệu phụ trợ | — | Không |
| Tầng 8 | JSON/Pydantic | — | Không |
| Tầng 9 | Custom, có trọng số | — | Không |
| Tầng 10 | Neo4j | Neo4j | Không |

Toàn bộ pipeline production chạy được **không cần GPU**. Hai hạng mục cần GPU (fine-tune SkillSpan/ESCOXLM-R cho miền học phần, fine-tune UniSkill) đều để dành cho tương lai khi có thêm CTDT ngành ngoài CNTT.

---

# 18. Nguyên tắc kiến trúc chính (v3)

1. Layer 2 là điểm bắt đầu — không lặp lại xử lý tiền kỳ ở đây.
2. ESCO là taxonomy chuẩn duy nhất — URI/concept cuối cùng luôn lấy từ ESCO.
3. UniSkill là dữ liệu giám sát/tham chiếu (dùng pretrained Cross-Encoder), không phải taxonomy thứ hai.
4. **Tầng 1 là ensemble 4 nguồn** (ESCOXLM-R skill+knowledge, esco-extract-skill, SkillSpan, LLM fallback) — không có nguồn nào là "chính" tuyệt đối, LLM chỉ chạy khi cần (fallback thật sự).
5. Tách extraction (tìm mention) khỏi matching (ánh xạ ra ESCO).
6. Hợp nhất bằng RRF, không phụ thuộc thang điểm giữa các kênh.
7. Cross-Encoder chỉ rerank sau khi đã có candidate, chạy inference-only.
8. Threshold hiệu chỉnh theo chiến lược ít dữ liệu (phân phối điểm + spot-check), không giả định có tập validation đầy đủ.
9. Skill vs Knowledge: ESCO là quyết định cuối, tín hiệu từ Tầng 1 và `loai_muc_tieu` chỉ dùng để phát hiện mismatch cần review.
10. Evidence cấp học phần được tổng hợp có trọng số theo độ giàu thông tin, không coi mọi evidence ngang nhau.
11. Giữ provenance đầy đủ, bao gồm cả nguồn trích xuất nào đã sinh ra mention.
12. Cache theo `evidence_id` cho mọi bước tốn chi phí (LLM API, inference model lớn) để pipeline có thể re-run rẻ khi refactor.

---

# 19. Câu hỏi còn mở (cần nhóm xác nhận, chưa tự suy đoán)

1. Ý nghĩa của field `muc_do` trong `clo.json` (hiện thấy giá trị `"IT"` ở mọi CLO của IT6204) — có phải mã hóa cho mức độ/level nào đó không?
2. Loại mục tiêu `TU_CHU_TRACH_NHIEM` có nên ánh xạ vào ESCO không, hay cần một quan hệ KG riêng ngoài `TEACHES_SKILL`/`TEACHES_KNOWLEDGE`?
3. Có checkpoint token-classification cụ thể nào của SkillSpan (không chỉ model pretrain miền job-posting) đã được nhóm gốc công bố công khai để dùng ngay không, hay cần tự fine-tune sau này?

---

# 20. Mô tả một câu cho đề tài nghiên cứu

> `teaches-skill` là pipeline ánh xạ kỹ năng/kiến thức từ học phần sang ESCO, sử dụng ensemble 4 nguồn NLP (ESCOXLM-R tách sẵn skill/knowledge, công cụ nội bộ esco-extract-skill, SkillSpan bổ sung, và LLM fallback) để sinh ứng viên, hợp nhất bằng Reciprocal Rank Fusion đa kênh, rerank bằng Cross-Encoder UniSkill pretrained, ra quyết định theo ngưỡng hiệu chỉnh trong điều kiện ít dữ liệu, tổng hợp có trọng số từ nhiều loại evidence (mô tả, mục tiêu, CLO, bài học) cấp học phần, và xuất quan hệ `TEACHES_SKILL`/`TEACHES_KNOWLEDGE` có thể giải thích được vào Knowledge Graph — toàn bộ chạy được không cần GPU.
