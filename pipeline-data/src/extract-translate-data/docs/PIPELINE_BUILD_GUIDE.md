
Tài liệu này là **kim chỉ nam xây dựng hệ thống**, dùng cho cả người lẫn agent
code. Không lẫn với `AGENT.md` (nguyên tắc kỹ thuật chi tiết từng module) —
file này trả lời câu hỏi "xây theo thứ tự nào, vì sao, xong mỗi bước thì biết
là xong chưa".

---

## 1. Tổng quan hệ thống — 3 luồng dữ liệu

Hệ thống nhận 3 loại nguồn đầu vào khác hẳn nhau về độ đầy đủ, nên **không
dùng chung một pipeline trích xuất** — chỉ hội tụ tại M6 (nạp KG).

| Luồng | Nguồn | Đặc điểm | Có CLO không |
|---|---|---|---|
| **A — Syllabus** | PDF scan | Ảnh, cần OCR, đề cương chi tiết đầy đủ | Có |
| **B — CTDT** | PDF/HTML structured | Chương trình đào tạo, khung học phần | Không cần (không phải cấp CLO) |
| **C — mhtml đại cương** | Trang web `sv.haui.edu.vn` lưu `.mhtml` | Structured (HTML thật, không cần OCR) nhưng **CLO/Mục tiêu trống hoàn toàn** | **Không — phải bổ sung** |

Luồng C là nguồn mới, phát sinh từ thực tế: các môn đại cương bắt buộc
(Giải tích, Triết học, GDTC...) không có file PDF đề cương riêng, chỉ tồn tại
dưới dạng trang chi tiết học phần trên cổng thông tin sinh viên, và trang đó
không hề điền phần Mục tiêu/CLO.

```
LUỒNG A (PDF scan)          LUỒNG B (CTDT)              LUỒNG C (mhtml đại cương)
raw/syllabus/*.pdf          raw/ctdt/*                   raw/mhtml/*.mhtml
  ↓ M1 (OCR + QA flag)        ↓ M2B (extract trực tiếp)    ↓ M2C-a (parse HTML, KHÔNG OCR)
  ↓ M2 (extraction)                                        ↓ M2C-b (bổ sung field thiếu)
  ↓ M3 (translation)          ↓ M3B                        ↓ M2C-c (human review 100% cho CLO)
  ↓ M4 (TEACHES_SKILL)                                     ↓ M3C
  ↓ M5 (SUPPORTS_SKILL)                                    ↓ M4/M5 (dùng chung code Luồng A)
  └──────────────┬──────────────────────┬──────────────────┘
                  ↓
                 M6 — Normalize → CSV → Neo4j (merge cả 3 theo crawl_course_key)
```

---

## 2. Nguyên tắc thiết kế xuyên suốt (áp dụng cho cả 3 luồng)

Đây là các nguyên tắc đã thống nhất, nhắc lại có bổ sung cho Luồng C:

1. **Never LLM URIs** — ESCO URI/label chỉ lấy từ `esco_data/`, LLM không
   bao giờ tự sinh.
2. **Không xóa dữ liệu điểm thấp** — chỉ hạ tier, giữ để audit.
3. **Threshold trong config**, không hardcode.
4. **Provenance đi xuyên suốt tới KG** — mọi field/edge suy luận đều phải
   mang theo dấu vết nguồn gốc, không được "biến mất" giữa các module.
5. **Mọi nội dung do máy suy luận (không phải trích xuất trực tiếp từ
   nguồn) đều phải qua người review trước khi có mặt trong dữ liệu cấp cho
   M4/M5** — nguyên tắc này áp dụng chung cho: OCR review (Luồng A), CLO
   bổ sung (Luồng C), SUPPORTS_SKILL (mọi luồng).

### Nguyên tắc mới cho Luồng C: `field_provenance` theo từng field

Khác với `ocr_quality` (một cờ cho cả record, dùng ở Luồng A), Luồng C cần
gắn cờ **theo từng field riêng lẻ**, vì độ tin cậy khác nhau tùy field trong
cùng một bản ghi:

| Giá trị | Ý nghĩa | Yêu cầu review |
|---|---|---|
| `extracted` | Lấy trực tiếp từ trang mhtml (Mô tả, Nội dung chương trình, Số tín chỉ...) | Không cần |
| `reference_copied` | Copy từ đề cương phiên bản cũ **cùng mã học phần** tìm được | Review nhẹ (đối chiếu còn đúng không) |
| `llm_inferred` | LLM suy luận dựa trên Mô tả + Nội dung chương trình đã có | **Bắt buộc review 100%**, đặc biệt field Mục tiêu/CLO |

Field Mục tiêu/CLO luôn là field rủi ro cao nhất vì nó là **input duy nhất**
mà M4 dùng để tìm TEACHES_SKILL — nếu CLO bị bịa mà không ai phát hiện, toàn
bộ skill-matching của học phần đó coi như xây trên nền giả nhưng trông có vẻ
có căn cứ (vì "có CLO" làm evidence).

---

## 3. Luồng C — thiết kế chi tiết

### Bước M2C-a: Parse HTML (không qua OCR)

`.mhtml` là snapshot HTML thật (multipart MIME, quoted-printable), decode
bằng `email` + `BeautifulSoup` chuẩn, **không cần MinerU**. Trích các field
có sẵn trên trang: Đơn vị đào tạo, Mã học phần, Tên học phần, Mô tả, Số tín
chỉ, Nội dung chương trình (STT + Tên mục + giờ tín chỉ theo loại), Phương
pháp đánh giá.

Field không có trên trang (thường xuyên trống ở nhóm môn đại cương): Mục
tiêu (Kiến thức/Kỹ năng/Thái độ), Phương pháp giảng dạy, Tài liệu tham
khảo → để `null`, không suy luận ở bước này.

### Bước M2C-b: Bổ sung field thiếu

Thứ tự ưu tiên nguồn bổ sung:

1. **Tìm đề cương phiên bản cũ cùng mã học phần** (nếu có lưu trữ từ trước
   khi trường đổi format website) → copy trực tiếp, gắn
   `field_provenance: reference_copied`.
2. **Không có bản cũ** → dùng LLM suy luận, nhưng bắt buộc cho LLM ngữ
   cảnh thật đã trích được (Mô tả + toàn bộ Nội dung chương trình 14 mục),
   **không** để LLM suy luận chỉ từ tên môn. Gắn `field_provenance:
   llm_inferred`.

### Bước M2C-c: Review bắt buộc

Mọi field `llm_inferred` thuộc nhóm Mục tiêu/CLO đi vào hàng đợi review
100%, không có mức auto-accept dù confidence cao — cùng nguyên tắc đã áp
cho SUPPORTS_SKILL. Field phụ (PP giảng dạy, tài liệu tham khảo) có thể
review có chọn lọc theo mức độ quan trọng.

### Sau M2C-c

Record đi tiếp qua M3 (dịch) → M4/M5 **dùng chung code với Luồng A**, không
cần viết lại — vì từ đây trở đi dữ liệu đã ở cùng schema `SyllabusL2`, chỉ
khác cờ `field_provenance` đi kèm để truy vết sau này.

### Quyết định còn mở — cần xác nhận trước khi build

Số lượng học phần thuộc Luồng C (đại cương, dạng mhtml, thiếu CLO) quyết
định có đáng xây cả M2C-b tự động hay không:

- **Nếu số lượng nhỏ (khoảng vài chục môn)**: các môn đại cương dùng chung
  toàn trường, không lặp lại theo từng ngành — viết tay CLO chuẩn (tham
  khảo CDIO hoặc đề cương môn tương đương ở nguồn khác) có thể nhanh và an
  toàn hơn xây cả bước LLM suy luận + review cho một tập nhỏ.
- **Nếu số lượng lớn**: xây M2C-b như thiết kế trên là hợp lý.

---

## 4. Cấu trúc thư mục cập nhật (thêm so với bản trước)

```
nckh_pipeline/
├── data/raw/mhtml/              # mới — input Luồng C
├── pipeline/
│   ├── m2c_mhtml_extract.py     # mới — parse HTML, KHÔNG qua MinerU
│   ├── m2c_supplement.py        # mới — bổ sung field thiếu + closed-loop review queue
│   └── prompts/
│       └── supplement_clo.txt   # mới — prompt suy luận CLO có ngữ cảnh
```

Các phần còn lại giữ nguyên cấu trúc đã có (`AGENT.md`, `config.yaml`,
`schemas.py`, M1/M3/M4/M5/M6, `shared/`, `scripts/run.py`).

`schemas.py` cần thêm field `field_provenance: dict[str, Literal["extracted",
"reference_copied", "llm_inferred"]]` vào `SyllabusL1`/`SyllabusL2` (dùng
chung cho cả Luồng A lẫn C — Luồng A mặc định toàn bộ field là `extracted`).

`config.yaml` cần thêm block `mhtml_supplement:` với các threshold liên quan
(vd. có bắt buộc tìm reference cũ trước khi cho phép LLM suy luận hay không).

---

## 5. Quy trình xây dựng hệ thống — theo giai đoạn

Xây theo đúng thứ tự dưới đây, **không nhảy cóc** — mỗi giai đoạn có tiêu
chí hoàn thành riêng, giai đoạn sau phụ thuộc dữ liệu giai đoạn trước.

### Phase 0 — Chuẩn bị nền

- Nạp `esco_data/` (skills, occupations, skill_occupation_relations).
- Điền `config.yaml`, `.env`.
- Dựng schema `schemas.py` đầy đủ (kể cả field_provenance của Luồng C).

**Xong khi:** `esco_data/` có thể load được bằng script test đơn giản,
config/env đã đủ key.

### Phase 1 — Luồng B (CTDT) trước tiên

Vì đơn giản nhất (không OCR, không LLM phức tạp), và **tạo node `HocPhan`
gốc** mà Luồng A/C sẽ enrich vào sau.

**Xong khi:** chạy `run.py --flow ctdt` ra được `CTDT_*.json` hợp lệ theo
schema, có `crawl_course_key` duy nhất cho mỗi học phần.

### Phase 2 — Luồng A (Syllabus scan)

Build M1 (OCR + 3 chỉ số + 3 mức flag) trước, review thật một batch nhỏ để
tinh chỉnh threshold trong `config.yaml` trước khi chạy full. Sau đó M2, M3.

**Xong khi:** với một batch mẫu (~20 file), tỷ lệ `REJECT` và
`NEEDS_REVIEW` ở mức hợp lý (không quá 50% — nếu quá cao, threshold đang
sai hoặc chất lượng scan đầu vào có vấn đề, cần xử lý trước khi chạy full).

### Phase 3 — Luồng C (mhtml đại cương)

Chỉ build nếu Phase 3 xác định số lượng đủ lớn (xem mục 3, "Quyết định còn
mở"). Build M2C-a trước (parse thuần, không LLM) — kiểm tra output đúng với
vài file mẫu. Sau đó mới build M2C-b (bổ sung) + hàng đợi review.

**Xong khi:** với file mẫu `BS6038`, output JSON có đủ field `extracted`
đúng thực tế trang web, các field thiếu được đánh dấu `null` +
`field_provenance` rõ ràng, chưa có field nào bị bịa mà không gắn cờ.

### Phase 4 — M4 (TEACHES_SKILL)

Build sau khi có dữ liệu thật từ ít nhất Luồng A hoặc C để test retrieval.
Test trên tập nhỏ đã biết trước đáp án (môn mà người trong ngành xác nhận
rõ dạy skill gì) để đo recall trước khi chạy full — đây chính là audit mẫu
đã thống nhất, làm ngay từ đầu chứ không đợi cuối.

**Xong khi:** audit mẫu 15-20 học phần cho kết quả recall chấp nhận được
(không có ngưỡng tuyệt đối — do team tự đặt dựa trên mức độ tin cậy cần
thiết của KG).

### Phase 5 — M5 (SUPPORTS_SKILL)

Build sau M4 vì cần tái dùng embedding model + FAISS index. Test closed-loop
lookup kỹ trước — đây là nơi rủi ro LLM bịa cao nhất, cần chắc chắn cơ chế
chặn hoạt động đúng trước khi chạy batch lớn.

**Xong khi:** thử với vài case cố tình cho LLM đề xuất skill không có thật
trong ESCO, xác nhận `closed_loop_lookup()` loại đúng, không lọt vào output.

### Phase 6 — M6 (KG loader) + merge 3 luồng

Build cuối cùng, vì phụ thuộc output của cả 3 luồng. Kiểm tra kỹ merge
logic theo `crawl_course_key` — đây là điểm dễ tạo node trùng nhất.

**Xong khi:** nạp thử vào Neo4j một tập nhỏ, không có node `HocPhan` trùng
lặp, mọi skill edge đều mang đủ trường provenance quy định ở `AGENT.md`
mục 4.

### Phase 7 — Validation toàn hệ thống

Chạy full 3 luồng trên toàn bộ dữ liệu thật, đối chiếu số liệu tổng (số học
phần, số edge theo loại) với kỳ vọng ban đầu, rà lại các case `REJECT`,
`zero_reason`, `llm_proposed_no_esco_match` để xem có pattern lỗi hệ thống
nào không trước khi coi là hoàn thành.

---

## 6. Checklist tổng trước khi coi một luồng là "xong"

- [ ] Mọi field suy luận (OCR review, CLO bổ sung, SUPPORTS_SKILL) đều có
      cờ provenance và đã qua review theo đúng mức bắt buộc.
- [ ] Không có ESCO URI nào không tồn tại trong `esco_data/`.
- [ ] Không có node `HocPhan` trùng `crawl_course_key`.
- [ ] Log `zero_reason` / `llow_confidence_discarded` / `llm_proposed_no_esco_match`
      đã được xem qua ít nhất một lần, không có pattern lỗi rõ ràng bị bỏ qua.
- [ ] Threshold hiện tại trong `config.yaml` đã qua ít nhất một vòng tinh
      chỉnh dựa trên dữ liệu thật, không còn là giá trị đoán ban đầu.
