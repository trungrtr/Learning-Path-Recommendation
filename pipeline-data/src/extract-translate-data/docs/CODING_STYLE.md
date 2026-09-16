# CODING STYLE — Pipeline NCKH

Áp dụng cho toàn bộ code trong repo này. Mục tiêu: người viết code lần đầu
xem lại sau 3 tháng vẫn hiểu ngay — không cần đoán.

---

## 1. Hàm: một hàm làm đúng một việc

**Nguyên tắc**: nếu phải dùng "và" để mô tả hàm làm gì → tách ra.

```python
# ❌ Sai — hàm làm 3 việc, không biết lỗi xảy ra ở đâu
def process(md_path, ocr_quality, output_dir):
    text = open(md_path).read()
    result = lx.extract(text, ...)
    SyllabusL1.model_validate(result)
    with open(output_dir / "out.json", "w") as f:
        json.dump(result, f)

# ✅ Đúng — tách rõ: đọc / trích xuất / validate / ghi
def read_markdown(md_path: Path) -> str:
    """Đọc file .md, ưu tiên .reviewed.md nếu có, fallback .raw.md."""
    reviewed = md_path.with_suffix(".reviewed.md")
    return reviewed.read_text() if reviewed.exists() else md_path.read_text()

def extract_syllabus(text: str, ocr_quality: OcrQuality) -> SyllabusL1:
    """Gọi langextract -> trả về SyllabusL1 đã validate Pydantic."""
    ...

def save_l1(record: SyllabusL1, output_dir: Path) -> Path:
    """Ghi SD_{ma_hoc_phan}.json, trả về đường dẫn file đã ghi."""
    ...
```

---

## 2. Đặt tên: đọc xong tên biết ngay làm gì

**Hàm**: động từ + danh từ, không viết tắt trừ khi cực kỳ phổ biến.  
**Biến**: danh từ mô tả nội dung, không dùng `tmp`, `data`, `result`, `x`.  
**Boolean**: bắt đầu bằng `is_`, `has_`, `should_`.

```python
# ❌ Sai
def proc(p, q):
    tmp = open(p).read()
    res = lx.extract(tmp, ...)
    return res

# ✅ Đúng
def extract_syllabus_from_file(md_path: Path, ocr_quality: OcrQuality) -> SyllabusL1:
    markdown_text = md_path.read_text(encoding="utf-8")
    extracted_data = _call_langextract(markdown_text)
    return _validate_and_attach_quality(extracted_data, ocr_quality)

# Boolean rõ ràng
is_reviewed = reviewed_path.exists()
has_extraction_result = bool(result.extractions)
should_skip = content_hash == previous_hash
```

---

## 3. Type hint: bắt buộc ở mọi hàm public

Type hint = documentation không bao giờ lỗi thời. IDE tự nhắc, agent tự
sửa đúng kiểu.

```python
# ❌ Thiếu type hint — agent không biết `ocr_quality` là dict hay object
def layer1_extract(md_path, ocr_quality):
    ...

# ✅ Đầy đủ type hint — tự giải thích
def layer1_extract(md_path: Path, ocr_quality: OcrQuality) -> SyllabusL1:
    ...

# Với list, dict, Optional cũng ghi rõ
def layer2_merge(records: list[SyllabusL1]) -> SyllabusL2: ...
def load_config(path: Path) -> dict[str, Any]: ...
def find_reviewed_path(raw_path: Path) -> Path | None: ...
```

---

## 4. Comment: giải thích TẠI SAO, không giải thích CÁI GÌ

Code đã nói "cái gì" — comment nói lý do tồn tại của quyết định đó.

```python
# ❌ Comment thừa — đọc code cũng biết
# Đọc file markdown
text = md_path.read_text()

# ❌ Comment thừa — đọc code cũng biết
# Set max_char_buffer = 200_000
max_char_buffer = 200_000

# ✅ Comment có giá trị — giải thích lý do không hiển nhiên
# Default langextract là 1_000 ký tự/chunk → syllabus 30k chars bị cắt 30 mảnh,
# CLO section mất context. Đặt 200_000 để toàn bộ đề cương đi trong 1 call.
max_char_buffer = 200_000

# ✅ Giải thích business rule, không phải syntax
# ocr_quality của L2 lấy mức xấu nhất vì pipeline downstream (M4)
# dùng flag này để quyết định có tin kết quả extract không.
worst_quality = _pick_worst_ocr_quality(l1_records)
```

---

## 5. Docstring: ngắn, đủ, không lặp code

Format: dòng đầu = **tóm tắt 1 câu**. Nếu cần thêm: giải thích behavior
không hiển nhiên, KHÔNG liệt kê lại tên tham số (đã có type hint rồi).

```python
# ❌ Quá dài, lặp type hint
def classify_flag(metrics: QualityMetrics, config: dict) -> str:
    """Phân loại chất lượng OCR.
    
    Args:
        metrics: QualityMetrics object chứa các chỉ số.
        config: Dict chứa config với các threshold.
    Returns:
        str: Một trong 'OK', 'NEEDS_REVIEW', 'REJECT'.
    """

# ✅ Đủ ý, không rác
def classify_flag(metrics: QualityMetrics, config: dict) -> Literal["OK", "NEEDS_REVIEW", "REJECT"]:
    """Áp ngưỡng từ config.yaml -> trả về cờ OCR.
    
    Thứ tự ưu tiên: REJECT > NEEDS_REVIEW > OK — một file chỉ cần thỏa
    1 điều kiện REJECT là bị loại dù các chỉ số khác đạt.
    Ngưỡng KHÔNG hardcode trong hàm này, đọc từ config["ocr_quality"].
    """
```

---

## 6. Xử lý lỗi: thất bại phải ồn ào, không được im lặng

```python
# ❌ Nuốt lỗi — không biết tại sao hàng trăm file ra kết quả trống
def extract_syllabus(text: str) -> dict:
    try:
        result = lx.extract(text, ...)
        return result.extractions[0].data
    except Exception:
        return {}

# ✅ Log đủ thông tin để debug, skip file lỗi nhưng không crash batch
def extract_syllabus(text: str, source_file: Path) -> SyllabusL1 | None:
    try:
        result = lx.extract(text, ...)
        if not result.extractions:
            logger.warning("no_extraction", extra={"file": str(source_file)})
            return None
        raw = result.extractions[0].data
        return SyllabusL1.model_validate(raw)
    except ValidationError as exc:
        # Pydantic lỗi = schema không khớp — ghi file conflict để review tay
        _write_conflict_log(source_file, exc)
        logger.error("schema_validation_failed", extra={
            "file": str(source_file),
            "errors": exc.error_count(),
        })
        return None
```

---

## 7. Không hardcode — mọi số đều từ config

```python
# ❌ Threshold nằm trong code — muốn tune phải sửa code, re-deploy
if rerank_score > 0.75:
    tier = "HIGH"
elif rerank_score > 0.45:
    tier = "MED"

# ✅ Đọc từ config — tune bằng config.yaml, không đụng code
high_threshold = config["teaches_skill"]["rerank_score_high"]   # 0.75
low_threshold  = config["teaches_skill"]["rerank_score_low"]    # 0.45

if rerank_score >= high_threshold:
    tier = "HIGH"
elif rerank_score >= low_threshold:
    tier = "MED"
else:
    tier = "low_confidence_discarded"
```

---

## 8. I/O ở đầu và cuối hàm — logic ở giữa không đụng file

Hàm "thuần logic" (không đọc/ghi file) dễ test hơn, dễ hiểu hơn.

```python
# ❌ Logic và I/O trộn lẫn — không test được classify_flag mà không tạo file
def process_file(md_path: Path) -> None:
    text = open(md_path).read()
    ratio = count_garbled(text) / len(text)
    if ratio > 0.3:
        open("logs/reject.txt", "a").write(str(md_path))

# ✅ Tách I/O khỏi logic
def compute_garbled_ratio(text: str) -> float:
    """Thuần logic — test được mà không cần file."""
    garbled = sum(1 for c in text if _is_garbled_char(c))
    return garbled / max(len(text), 1)

def process_file(md_path: Path, logger) -> QualityMetrics:
    """I/O ở đây, gọi hàm logic bên trên."""
    text = md_path.read_text()
    metrics = QualityMetrics(
        garbled_char_ratio=compute_garbled_ratio(text),
        ...
    )
    logger.info("quality_computed", extra={"file": str(md_path), **metrics.model_dump()})
    return metrics
```

---

## 9. Idempotent: chạy lại phải an toàn

Mọi hàm ghi file phải kiểm tra trước — chạy lại không tạo file trùng,
không tính lại API call tốn tiền.

```python
# ❌ Mỗi lần chạy gọi API dù file đã có
def run_m1(pdf_path: Path) -> Path:
    md_path = call_mineru_api(pdf_path)   # tốn tiền mỗi lần
    return md_path

# ✅ Skip nếu output đã tồn tại và hash không đổi
def run_m1(pdf_path: Path, output_dir: Path) -> Path:
    output_path = output_dir / f"{pdf_path.stem}.raw.md"
    if output_path.exists() and _hash_matches(pdf_path, output_path):
        logger.info("skip_existing", extra={"file": str(pdf_path)})
        return output_path
    return _call_mineru_and_save(pdf_path, output_path)
```

---

## 10. List comprehension: chỉ dùng khi đọc một lần hiểu ngay

```python
# ❌ Khó đọc — phải trace xem `s` là gì, điều kiện lồng nhau
skills = [s.uri for s in candidates if s.tier != "low_confidence_discarded" and s.rerank_score > t]

# ✅ Tách ra — mỗi bước tên biến giải thích luôn mục đích
accepted_candidates = [s for s in candidates if s.tier != "low_confidence_discarded"]
high_confidence_skills = [s.uri for s in accepted_candidates if s.rerank_score > threshold]
```

---

## Tóm tắt — yêu cầu agent theo checklist này

Thêm đoạn này vào đầu mỗi Task prompt khi dùng Antigravity/Copilot:

```
Viết code theo CODING_STYLE.md trong repo. Bắt buộc:
- Type hint đầy đủ ở mọi hàm public
- Docstring tóm tắt 1 câu + giải thích điều không hiển nhiên
- Comment giải thích LÝ DO, không giải thích syntax
- Số/threshold đọc từ config.yaml, không hardcode trong code
- Mỗi hàm public làm đúng 1 việc (nếu dùng "và" để mô tả → tách)
- Không `except Exception: pass` — log đủ thông tin, ghi conflict log
- Idempotent: chạy lại phải skip nếu output đã đúng
```
