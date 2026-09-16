# BUILD TASKS — Đưa từng Task cho Antigravity, theo đúng thứ tự

Mỗi Task dưới đây là **một prompt độc lập**, đủ ngữ cảnh để dán thẳng vào
Antigravity mà không cần giải thích thêm. Làm lần lượt Task 0 → Task 8,
**không nhảy cóc** — Task sau phụ thuộc output thật của Task trước để test.

Trước khi bắt đầu Task 0: đảm bảo Antigravity có quyền đọc cả 3 file
`AGENT.md`, `PIPELINE_BUILD_GUIDE.md`, `config.yaml`, `pipeline/schemas.py`
trong repo — mọi Task bên dưới đều tham chiếu ngược lại các file này thay vì
lặp lại toàn bộ nguyên tắc.

---

## Task 0 — Chuẩn bị nền

```
Đọc AGENT.md và PIPELINE_BUILD_GUIDE.md trong repo trước khi làm gì khác.

Việc cần làm:
1. Hoàn thiện pipeline/schemas.py: bổ sung field `field_provenance:
   dict[str, Literal["extracted","reference_copied","llm_inferred"]]`
   vào SyllabusL1 và SyllabusL2 (dùng chung cho Luồng A và C — Luồng A mặc
   định toàn bộ field là "extracted"). Giữ nguyên các model khác đã có.
2. Viết shared/file_io.py đầy đủ: read_yaml_config, read_json, write_json,
   append_jsonl (giữ nguyên content_hash đã có).
3. Viết shared/logger.py: get_logger() ghi JSONL vào logs/{module}.jsonl,
   format {ts, module, level, msg, meta}. Dùng logging.Handler chuẩn của
   Python, không tự viết writer thủ công.
4. Viết một script scripts/check_setup.py: load config.yaml, kiểm tra các
   key bắt buộc trong .env đã có (không rỗng), kiểm tra esco_data/ có đủ 3
   file (skills_en.csv, occupations_en.csv, skill_occupation_relations.csv)
   không, in báo cáo OK/thiếu.

Không viết logic cho M1-M6 trong Task này — chỉ nền tảng dùng chung.

Xong khi: `python scripts/check_setup.py` chạy được và báo đúng trạng thái
thật của môi trường (thiếu gì báo đúng cái đó).
```

---

## Task 1 — Luồng B: M2B CTDT extraction

```
Đọc AGENT.md mục "0. Sơ đồ tổng quan" và pipeline/schemas.py (model
CtdtSchema) trước khi code.

Việc cần làm — hoàn thiện pipeline/m2_extraction.py, hàm ctdt_extract():
1. Nhận đường dẫn file PDF/HTML trong data/raw/ctdt/.
2. Parse ra: ma_ctdt, crawl_course_key, danh sách nhom_hoc_phan, danh sách
   hoc_phan con trong mỗi nhóm (rule-based theo dot-notation group code,
   KHÔNG dùng LLM ở bước này vì dữ liệu đã structured).
3. Validate bằng Pydantic (CtdtSchema), lỗi thì ghi vào logs/conflicts/
   thay vì raise cứng — không được để một file lỗi chặn cả batch.
4. Ghi output ra data/interim/extracted/ctdt/CTDT_{ma_ctdt}.json.
5. Idempotent: nếu content_hash không đổi so với lần chạy trước, skip.

Không đụng vào M1, M2 (syllabus), M3-M6 trong Task này.

Xong khi: chạy được trên toàn bộ file mẫu trong data/raw/ctdt/, mỗi file
cho ra đúng 1 JSON hợp lệ theo schema, crawl_course_key duy nhất cho mỗi
học phần (không trùng giữa các file CTDT khác nhau).
```

---

## Task 2 — Luồng A: M1 OCR + gắn cờ chất lượng

```
Đọc AGENT.md mục 1 (Gắn cờ chất lượng OCR) TRƯỚC KHI CODE — đây là mục bắt
buộc quan trọng nhất của Task này, không được bỏ qua bất kỳ điểm nào trong
đó.

Việc cần làm — hoàn thiện pipeline/m1_pdf_to_md.py:
1. call_mineru(): gọi MinerU API (đọc key từ .env), upload PDF, poll job,
   tải markdown về. Idempotent — nếu data/interim/md/{ma_hoc_phan}.raw.md
   đã tồn tại thì skip, không gọi lại API.
2. compute_quality_metrics(): tính đúng 3 chỉ số trong AGENT.md mục 1
   (table_col_mismatch, garbled_char_ratio, short_page_ratio). Gọi
   gemini_self_score CHỈ KHI config.yaml -> ocr_quality.use_gemini_self_score
   = true, và điểm này KHÔNG được dùng trong classify_flag().
3. classify_flag(): đọc ngưỡng từ config.yaml -> ocr_quality.*, trả về
   đúng 1 trong 3 giá trị OK / NEEDS_REVIEW / REJECT theo đúng bảng trong
   AGENT.md mục 1 (không tự đặt ngưỡng khác trong code).
4. process_batch(): chạy hàng loạt có concurrency giới hạn (không spam
   MinerU API), ghi mỗi file 1 dòng vào logs/m1_quality.jsonl, đồng thời
   xuất data/interim/m1_needs_review.csv chỉ chứa các dòng NEEDS_REVIEW
   (cột: ma_hoc_phan, file, 3 chỉ số, lý do flag) để người review mở trực
   tiếp bằng Excel.
5. File REJECT: KHÔNG ghi vào .raw.md như file OK — ghi riêng vào
   data/interim/md/rejected/ kèm lý do, không cho đi tiếp sang M2.

Không viết logic sửa tay (đó là việc người review làm ngoài code) — chỉ
cần đảm bảo cấu trúc thư mục sẵn sàng để người review lưu bản
{ma_hoc_phan}.reviewed.md cạnh bản .raw.md.

Xong khi: chạy trên khoảng 20 file PDF mẫu, log JSONL đầy đủ, CSV
needs_review mở lên đọc được, tỷ lệ REJECT/NEEDS_REVIEW hợp lý (không phải
gần 100% — nếu vậy nghĩa là threshold hoặc code đang sai, cần báo lại chứ
không tự ý nới lỏng ngưỡng).
```

---

## Task 3 — Luồng A: M2 extraction + M3 translation

```
Đọc pipeline/schemas.py (SyllabusL1, SyllabusL2) trước khi code.

Việc cần làm:
1. pipeline/m2_extraction.py:
   - layer1_extract(): nhận đường dẫn .reviewed.md (fallback .raw.md nếu
     chưa được review), dùng LangExtract + Gemini để trích theo schema
     SyllabusL1. Field `ocr_quality` nhận nguyên từ M1, KHÔNG tính lại,
     KHÔNG cho LLM tự đoán giá trị này.
   - Prompt LangExtract PHẢI yêu cầu: nếu thông tin không có trong văn bản
     thì trả null, không tự suy diễn — ghi rõ điều này trong
     pipeline/prompts/extract.txt.
   - layer2_merge(): gộp nhiều SD_* cùng ma_hoc_phan thành 1 COURSE_*.json,
     dùng content_hash để dedup, ocr_quality của bản gộp = mức xấu nhất
     trong các bản L1 được gộp (REJECT > NEEDS_REVIEW > OK).
2. pipeline/m3_translation.py:
   - translate_record(): dịch nguyên record (không field-by-field) để giữ
     nhất quán thuật ngữ, gọi qua shared/llm_client.py.
   - Không dịch: mã học phần, ESCO URI (chưa có ở bước này thì bỏ qua),
     số liệu.
   - check_consistency(): kiểm tra glossary lock cơ bản (vd. "học phần" ->
     "course" nhất quán), CHỈ cảnh báo, không tự sửa.

Xong khi: chạy trên output đã review của Task 2, ra được COURSE_*_en.json
hợp lệ theo schema, ocr_quality vẫn còn nguyên trong bản dịch (kiểm tra
bằng cách so field này ở input/output phải giống hệt nhau).
```

---

## Task 4 — Luồng C: M2C mhtml extraction + bổ sung

```
CHỈ làm Task này SAU KHI xác nhận số lượng học phần Luồng C đủ lớn để đáng
xây tự động (xem PIPELINE_BUILD_GUIDE.md mục 3, phần "Quyết định còn mở").
Nếu chưa xác nhận, dừng lại hỏi trước khi code.

Đọc PIPELINE_BUILD_GUIDE.md mục 3 (Luồng C — thiết kế chi tiết) trước khi
code — đây là bước rủi ro cao nhất trong toàn hệ thống (LLM có thể bịa
CLO), phải bám đúng thiết kế, không tự sáng tạo thêm.

Việc cần làm:
1. pipeline/m2c_mhtml_extract.py:
   - Decode .mhtml bằng module `email` chuẩn của Python (multipart,
     quoted-printable) lấy phần text/html, parse bằng BeautifulSoup.
   - Trích các field CÓ SẴN trên trang (Đơn vị đào tạo, Mã/Tên học phần,
     Mô tả, Số tín chỉ, Nội dung chương trình theo từng dòng STT + Tên mục
     + giờ tín chỉ, Phương pháp đánh giá).
   - KHÔNG dùng MinerU, không OCR — đây là HTML thật.
   - Field không có trên trang (Mục tiêu/CLO, PP giảng dạy, Tài liệu tham
     khảo) để null, gắn field_provenance tương ứng = chưa xác định ở bước
     này (sẽ gắn ở bước 2).
2. pipeline/m2c_supplement.py:
   - Bước a: tìm đề cương phiên bản cũ cùng mã học phần trong
     data/raw/legacy_reference/ (thư mục cần tạo mới, để trống, người
     dùng tự nạp file tham khảo cũ nếu có). Nếu tìm thấy field tương ứng
     -> copy trực tiếp, gắn field_provenance = "reference_copied".
   - Bước b: field vẫn còn thiếu sau bước a -> gọi LLM, PHẢI đưa nguyên
     Mô tả + toàn bộ Nội dung chương trình đã trích ở bước 1 làm ngữ cảnh
     (không được chỉ đưa tên môn). Dùng prompt trong
     pipeline/prompts/supplement_clo.txt (cần viết mới). Gắn
     field_provenance = "llm_inferred".
   - Xuất tất cả record có field_provenance = "llm_inferred" thuộc nhóm
     Mục tiêu/CLO ra 1 file CSV riêng để review 100% bắt buộc (không được
     gộp chung với các field phụ ít quan trọng hơn).
3. Viết pipeline/prompts/supplement_clo.txt: yêu cầu LLM chỉ suy luận dựa
   trên ngữ cảnh được cung cấp, không bịa thêm ngoài phạm vi Nội dung
   chương trình đã có, và phải trả lời ở định dạng CLO có thể map vào
   schema (Kiến thức/Kỹ năng/Thái độ).

Xong khi: chạy thử với file BS6038.mhtml mẫu trong data/raw/mhtml/, ra
đúng các field extracted khớp thực tế trang web, field Mục tiêu được điền
llm_inferred có nội dung hợp lý dựa trên 14 mục nội dung chương trình đã
có (không phải câu chung chung kiểu chỉ dựa vào tên môn "Giải tích").
```

---

## Task 5 — M4: TEACHES_SKILL

```
Đọc AGENT.md mục 2 trước khi code — đặc biệt phần "Trường hợp 0 kết quả"
và "Audit định kỳ".

Việc cần làm — hoàn thiện pipeline/m4_esco_linking.py:
1. extract_skill_phrases(): trích phrase từ CẢ CLO lẫn Bai.ten_bai, gắn
   source_text_type cho mỗi phrase.
2. embedding_retrieve(): encode bằng model trong config.yaml ->
   models.embedding_model, build/load FAISS index từ esco_data/skills_en.csv
   (build 1 lần, cache lại, không rebuild mỗi lần chạy).
3. uniskill_rerank(): rerank bằng cross-encoder, input là câu đầy đủ chứ
   không phải chỉ tên môn.
4. build_skill_evidence():
   - Phân tier theo config.yaml -> teaches_skill.rerank_score_high/low.
   - Tier dưới rerank_score_low: gắn "low_confidence_discarded", VẪN GHI
     vào output, không xóa.
   - Nếu danh sách rỗng: xác định zero_reason đúng theo bảng trong
     AGENT.md mục 2 (no_candidates_generated vs all_below_threshold).

Sau khi code xong, viết thêm script scripts/audit_sample.py: lấy ngẫu
nhiên N học phần (N truyền qua argument), xuất ra file để người review
điền tay "skill thực tế có dạy" rồi so sánh với kết quả M4, in ra recall
ước tính. Đây là công cụ audit định kỳ, không phải chạy 1 lần.

Xong khi: chạy trên output Task 3 (và Task 4 nếu đã làm), audit_sample.py
chạy được và cho ra số liệu recall trên tập mẫu người review đã điền.
```

---

## Task 6 — M5: SUPPORTS_SKILL

```
Đọc AGENT.md mục 3 TOÀN BỘ trước khi code — Task này rủi ro cao nhất về
mặt hallucination, không được bỏ qua bước closed-loop lookup dù bất kỳ lý
do gì.

Việc cần làm — hoàn thiện pipeline/m5_labeling.py:
1. generate_candidates(): nhận course_context (CLO, phương pháp giảng dạy,
   đánh giá, Bai.ten_bai) + occupation_hints (từ
   esco_data/skill_occupation_relations.csv dựa theo TEACHES_SKILL đã có,
   NẾU có — không bắt buộc phải có mới chạy được hàm này). Gọi LLM theo
   pipeline/prompts/labeling.txt, trả về list label thô.
2. closed_loop_lookup():
   - Encode từng label bằng ĐÚNG embedding_model dùng ở M4 (dùng chung
     hàm, không viết lại encode riêng).
   - FAISS search ESCO, tính esco_match_score.
   - Dưới config.yaml -> supports_skill.esco_match_score_min: loại, ghi
     log riêng "llm_proposed_no_esco_match" (label LLM đề xuất + điểm gần
     nhất tìm được, để sau này biết LLM hay bịa ở loại môn nào).
   - Đạt ngưỡng: giữ SkillCandidateM5 với cả llm_proposed_label lẫn
     esco_matched_label.
3. export_for_review(): xuất CSV có 2 cột llm_proposed_label và
   esco_matched_label CẠNH NHAU (không phải 2 sheet riêng) để người review
   so sánh trực tiếp, cột decision để trống cho người điền yes/no.
4. import_decisions(): đọc lại file đã điền, chỉ decision=yes mới tạo
   SkillMatch. KIỂM TRA config.yaml -> supports_skill.auto_accept phải là
   false — nếu code phát hiện giá trị true thì raise lỗi rõ ràng, không
   được tự động chạy tiếp với auto_accept bật.

Viết 1 test case cố tình cho LLM đề xuất một skill không có thật (vd. tên
ngẫu nhiên không liên quan giáo dục), xác nhận closed_loop_lookup loại
đúng case này trước khi coi Task hoàn thành.

Xong khi: test case bịa ở trên bị loại đúng, và chạy thử trên vài học
phần thật cho ra file CSV review có đủ 2 cột label để đối chiếu.
```

---

## Task 7 — M6: KG loader + merge 3 luồng

```
Đọc AGENT.md mục 4 (Provenance) trước khi code.

Việc cần làm — hoàn thiện pipeline/m6_kg_loader.py và
pipeline/cypher/load_all.cypher:
1. normalize_ids(): chuẩn hóa snake_case, kiểu dữ liệu, không khoảng
   trắng thừa.
2. merge_two_streams(): merge node HocPhan (từ Luồng B) với skill edges
   (từ Luồng A/C) theo crawl_course_key. NẾU key không khớp -> ghi log lỗi
   rõ ràng, KHÔNG tự tạo node HocPhan mới để né lỗi.
3. export_csv(): mỗi node type / edge type ra 1 file CSV riêng, format
   tương thích neo4j-admin import, đặt đúng thư mục
   data/processed/csv/nodes/ và /edges/.
4. Mọi edge TEACHES_SKILL/SUPPORTS_SKILL trong CSV bắt buộc có đủ cột:
   retrieval_score hoặc esco_match_score, validation_confidence,
   evidence_ids, ocr_quality (hoặc field_provenance nếu từ Luồng C). Thiếu
   cột nào thì raise lỗi khi export, không export thiếu.
5. Viết load_all.cypher: Block 1 constraints/index, Block 2 load 8 loại
   node, Block 3 load edge cấu trúc, Block 4 load edge kỹ năng — dùng
   MERGE cho tất cả, không dùng CREATE.
6. load_to_neo4j(): chạy cypher theo đúng thứ tự 4 block, dùng driver
   neo4j chính thức, transaction theo batch hợp lý (không load hàng trăm
   nghìn dòng trong 1 transaction).

Xong khi: nạp thử vào Neo4j local với dữ liệu mẫu từ Task 1+3 (và 4 nếu
có), không có node HocPhan trùng crawl_course_key, query thử
`MATCH ()-[r:TEACHES_SKILL]->() RETURN r LIMIT 5` trả về edge có đủ tất cả
cột provenance yêu cầu.
```

---

## Task 8 — Validation toàn hệ thống

```
Đọc lại toàn bộ AGENT.md và PIPELINE_BUILD_GUIDE.md mục 6 (Checklist tổng)
trước khi làm Task này — đây là bước rà soát cuối, không phải viết thêm
tính năng mới.

Việc cần làm:
1. Viết scripts/validate_all.py chạy qua từng mục trong checklist
   PIPELINE_BUILD_GUIDE.md mục 6, in báo cáo PASS/FAIL cho từng mục:
   - Không field llm_inferred nào thiếu provenance/chưa review.
   - Không ESCO URI nào ngoài esco_data/.
   - Không HocPhan trùng crawl_course_key.
   - Đếm số dòng log zero_reason / low_confidence_discarded /
     llm_proposed_no_esco_match, in ra để người xem xét thủ công (không tự
     kết luận đây là lỗi hay không).
2. Chạy full 3 luồng trên toàn bộ dữ liệu thật hiện có, lưu báo cáo số
   liệu tổng (số học phần mỗi luồng, số edge mỗi loại) vào
   logs/validation_report_{ngày}.json.

Xong khi: validate_all.py chạy hết không lỗi crash, báo cáo cuối cùng được
người phụ trách xem qua và xác nhận không có pattern lỗi hệ thống nào bị
bỏ sót.
```