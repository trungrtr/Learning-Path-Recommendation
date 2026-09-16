# 📂 Cấu trúc thư mục: pipeline-data

> Thư mục dữ liệu dùng chung (Shared Data Directory) giữa các module trong hệ thống (extract-translate-data, esco-skill-mapping).
> Giúp code gọn gàng và không chứa data trung gian không cần thiết.

---

## Tree View

```
pipeline-data/
│
├── raw/                           # ── Input gốc ban đầu ──
│   ├── 1_markdown/                #   Markdown từ MinerU (OCR từ PDF)
│   ├── 4_ctdt/                    #   File CTDT structured
│   └── 5_mhtml/                   #   MHTML saved từ web
│
├── contract/                      # ── Giao tiếp giữa các module ──
│                                  #   File JSON kết xuất từ extract-translate-data (M3)
│                                  #   Dùng làm input cho esco-skill-mapping (M4)
│
├── esco_data/                     # ── Dữ liệu tham chiếu tĩnh ──
│                                  #   Các file CSV taxonomy tải từ ESCO
│                                  #   (skills_en.csv, occupations_en.csv, ...)
│
├── review_queue/                  # ── Hàng đợi chờ duyệt thủ công ──
│   └── supplement/                #   Kết quả suy luận skill từ LLM cần người review
│
└── final_kg_export/               # ── Output cuối cùng ──
                                   #   File CSV Node/Edge để chuẩn bị nạp (MERGE) vào Neo4j

├── src/                           # ── Source Code ──
│   ├── extract-translate-data/    #   Repo xử lý M2/M3
│   └── esco-skill-mapping/        #   Repo xử lý M4/M5/M6
```

---

## Vai trò

Thư mục này đóng vai trò như một **Data Hub**:
1. `extract-translate-data` sẽ đọc từ `raw/` và ghi kết quả (sau khi làm sạch, dịch) vào `contract/`.
2. `esco-skill-mapping` sẽ đọc từ `contract/` (input khóa học) và `esco_data/` (dữ liệu từ điển).
3. Sau khi chạy mapping bằng LLM, `esco-skill-mapping` xuất ra `review_queue/` cho người dùng check.
4. Cuối cùng, kết quả xuất ra `final_kg_export/` để đưa vào Graph Database.
