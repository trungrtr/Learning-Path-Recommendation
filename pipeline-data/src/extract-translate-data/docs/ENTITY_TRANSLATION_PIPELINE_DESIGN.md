# Thiết kế chuẩn hóa và dịch thực thể

## Phạm vi

Thiết kế này chỉ bổ sung cấu trúc dữ liệu cho pipeline mới. Không thay đổi
module, config, output hoặc cách chạy hiện tại.

## Luồng dữ liệu

```text
data/2_extracted_json/
  -> data/normalized_entities/
  -> data/7_translated_entities/vi_en/
  -> data/7_translated_entities/en/
  -> data/8_canonical/
  -> M4/M5/M6
```

Luồng C có thêm bước review:

```text
data/2_extracted_json/hoc_phan_bo_sung/
  -> data/normalized_entities/
  -> data/9_review_queue/supplement/
  -> data/7_translated_entities/
  -> data/8_canonical/mhtml/
```

## Quy ước bản ghi

Mỗi thực thể phải có:

- `entity_id`: ổn định và duy nhất, ví dụ `IT6168:clo:L1`.
- `ma_hoc_phan`: khóa liên kết chính.
- `source_file`: file tạo ra thực thể.
- `source_hash`: hash nội dung nguồn.
- `field_provenance`: `extracted`, `reference_copied` hoặc `llm_inferred`.
- `review_status`: `not_required`, `pending`, `approved` hoặc `rejected`.

Tên file: `{ma_hoc_phan}__{entity_type}.json`.
Mỗi học phần có tối đa một file cho mỗi loại; các thực thể lặp lại dùng một
mảng trong file, không tạo file riêng cho từng mục.

## Nguyên tắc bất biến

1. Không ghi đè `data/raw/1_markdown/` và `data/2_extracted_json/`.
2. Không dịch mã học phần, mã CLO, mã PI, số liệu hoặc khóa JSON.
3. `ten_en` đã có trong nguồn được giữ nguyên; chỉ dịch khi thiếu.
4. Dịch từng field, không gửi cả JSON lớn cho một lần dịch.
5. Chỉ bản ghi đã đạt trạng thái review mới được đưa vào canonical khi field
   đó là `reference_copied` hoặc `llm_inferred`.
6. Mọi bản dịch phải truy ngược được về `entity_id` và `source_hash`.

## Thứ tự triển khai sau này

1. Package `pipeline/m3/` chuẩn hóa một batch nhỏ từ các JSON M2A hiện tại.
2. Kiểm tra khóa và độ đầy đủ mã/tên học phần.
3. Dịch batch nhỏ, đánh giá chất lượng và retry riêng từng field lỗi.
4. Ghép canonical cho Luồng A.
5. Sau khi ổn định mới triển khai bổ sung/review cho Luồng C.

## Package thực thi

- `pipeline/m3/normalize.py`: tách entity từ CTDT, M2A và M2C.
- `pipeline/m3/translate.py`: dịch từng entity qua `shared.llm_client`.
- `pipeline/m3/assemble.py`: ghép bản dịch thành canonical record.
