# Thiết kế công đoạn canonicalization

## 0. Điều kiện tiên quyết (đã bổ sung vào schema v2)
Trước khi canonicalize, mỗi JSON đã trích xuất phải có:
- `source_document.crawl_course_key` — key gom nhóm file cùng 1 học phần
- `source_document.source_document_id` — id duy nhất của lần extract
- `content_hash` ở chapter/lesson — để phát hiện dòng trùng do lỗi convert MHTML→Markdown

Nếu 1 trong 3 field trên còn null → **không merge**, đẩy sang hàng đợi "needs manual tagging".

## 1. Pipeline tổng quan

```
Extracted JSON (nhiều document/course)
        │
        ▼
[1] GROUP BY crawl_course_key
        │
        ▼
[2] DEDUP nội bộ mỗi nhóm (content_hash)
        │
        ▼
[3] RESOLVE course-level fields (course_code, name, credits, dept...)
        │
        ▼
[4] RECONCILE children (description / clos / chapters / lessons)
        │
        ▼
[5] ASSIGN canonical id (course_id, chapter_id, lesson_id, clo_id)
        │
        ▼
[6] GHI merge_conflicts + merge_meta
        │
        ▼
Canonical JSON (1 file / course) + conflict log (để review thủ công)
```

## 2. Chi tiết từng bước

### [1] Group
`group_key = crawl_course_key` (không dùng course_code vì course_code có thể bị OCR/convert sai lệch giữa các lần crawl).

### [2] Dedup nội bộ
Trong cùng 1 `crawl_course_key`, có thể có nhiều source_document (crawl lại nhiều lần) → chapters/lessons trùng do lỗi MHTML.
- So khớp bằng `content_hash` (exact dup) → giữ 1, bỏ phần còn lại.
- Nếu hash khác nhưng `title` normalize giống + `order_index` giống → coi là near-dup, đánh dấu `status: needs_review` thay vì tự động xoá.

### [3] Resolve course-level fields
Với mỗi field (course_code, name_vi, name_en, credits.*, department, knowledge_block, education_level):
- Nếu tất cả source_document cho cùng giá trị → set thẳng, không log conflict.
- Nếu khác nhau:
  - Áp `resolution_strategy` mặc định: **most_recent** (theo `extraction_timestamp`) cho các field text/tên; **most_complete** (giá trị không null, dài hơn) cho credits/hours.
  - Ghi vào `course.merge_conflicts[]` dù đã tự resolve, để có audit trail.
  - Nếu 2 giá trị khác nhau nhưng đều "complete" như nhau (không phân được) → `status: needs_review`, không auto-resolve.

### [4] Reconcile children
- **description**: 1 course chỉ có 1 description canonical → nếu nhiều source có text khác nhau, chọn bản dài nhất/mới nhất, log conflict, giữ source_refs đầy đủ.
- **clos**: match theo `clo_code` (nếu có) hoặc theo `content` normalize + `order_index`. Không match được → giữ riêng, gắn cờ `needs_review`.
- **chapters**: match theo `chapter_code` trước, fallback theo `title normalize + order_index`. Merge `allocated_hours` theo most_complete.
- **lessons**: match theo `lesson_code` trước, fallback theo `(chapter match + title normalize + order_index)`. Xử lý `parent_lesson_temp_id`: nếu quyết định flat sequential → bỏ hẳn field này khi sinh JSON canonical (không map sang `parent_lesson_id`), chỉ dựa `order_index` trong chapter.

### [5] Assign canonical id
- `course_id = "C_" + slug(course_code)` (ổn định, dễ debug) hoặc UUID nếu cần tránh đụng độ khi course_code sai.
- `chapter_id`, `lesson_id`, `clo_id` sinh theo `course_id + "_" + order_index` để id có ý nghĩa và dễ trace ngược khi đọc CSV import Neo4j.

### [6] Output
- 1 file JSON canonical / course (theo schema v2).
- 1 file `conflict_log.jsonl` riêng, mỗi dòng 1 conflict có `status: needs_review` — dùng để review thủ công trước khi đẩy vào Neo4j.
- `merge_meta.unresolved_conflict_count > 0` → pipeline nên chặn auto-import CSV, bắt review trước.

## 3. Việc cần bạn xác nhận trước khi code merge thật
1. `parent_lesson_temp_id` — bỏ hẳn (flat) hay giữ (có phân cấp thật)?
2. `course_id` sinh theo slug(course_code) hay UUID?
3. CLO ↔ chapter/lesson: map thủ công lúc extract (thêm `related_chapter_refs_temp_id` đã đề xuất trong v2) hay để trống, suy luận ở tầng sau?
4. Ngưỡng "gần giống" cho near-dup title (fuzzy match) — dùng threshold nào (vd Levenshtein ratio > 0.9)?
