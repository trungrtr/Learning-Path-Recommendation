# Supports Skill Pipeline (M5 - Foundational & Soft Skill Linking) — Revised

Luồng `supports_skill_pipeline` là một module trí tuệ nhân tạo chuyên biệt để bóc tách các **Kỹ năng bổ trợ, kỹ năng mềm, hoặc kỹ năng nền tảng (Foundational & Soft Skills)**.

Khác với các kỹ năng chuyên môn cứng thường được ghi rõ rành rọt trong đề cương, các kỹ năng bổ trợ (như Tư duy logic, Làm việc nhóm, Giải quyết vấn đề) thường chỉ được đề cập ngầm định (implicitly). Do đó, luồng này sử dụng sức mạnh suy luận của LLM (Large Language Models) kết hợp với các thuật toán tìm kiếm đa kênh để tìm ra chúng.

---

## Công Nghệ Cốt Lõi (Core Technologies)

1. **LLM Reasoning (Suy luận bằng LLM)**:
   - Sử dụng `google-genai` (Gemini 2.5 Flash / Pro).
   - Nhiệm vụ: Đọc toàn bộ ngữ cảnh của khóa học và suy luận ra các "Concept" kỹ năng mềm/nền tảng ẩn dưới bề mặt văn bản. LLM ở đây không map trực tiếp vào ESCO để tránh ảo giác, mà chỉ đóng vai trò "gợi ý ý tưởng".
2. **Multi-Channel Retrieval (Tìm kiếm đa kênh)**:
   - Thay vì chỉ dùng 1 bộ tìm kiếm, hệ thống dùng 3 kênh độc lập để quét từ điển ESCO: **FAISS** (Tìm theo ngữ nghĩa vector), **BM25** (Tìm theo từ khóa thô), và **ESCOXLM-R** (Mô hình tinh chỉnh riêng).
3. **Reciprocal Rank Fusion (RRF)**:
   - Nhiệm vụ: Hợp nhất và xếp hạng lại (Fusion & Ranking) kết quả từ 3 kênh tìm kiếm trên. Ứng viên nào xuất hiện trên cả 3 kênh với thứ hạng cao sẽ được đẩy lên Top 1.

---

## Kiến Trúc 8 Bước (8-Step Pipeline)

Quy trình xử lý hoàn toàn tự động từ việc đọc dữ liệu đến khi xuất file:

### S1 — Preprocessing
Gom toàn bộ văn bản (Mô tả, Mục tiêu, CLO) của một học phần thành một khối ngữ cảnh (Context) duy nhất. Mỗi đoạn văn bản được đóng gói kèm `source_id` để truy vết nguồn gốc phục vụ Layer S6.5.

### S2 — Concept Extraction
Bơm Context vào LLM kèm Prompt chuyên biệt để LLM "rút trích" ra danh sách các khái niệm kỹ năng bổ trợ thô (Raw Concepts).

**[MỚI]** S2 lưu lại thêm 2 trường cho mỗi Raw Concept:
- `source_sentence_id` — câu CLO / đoạn mục tiêu mà LLM dựa vào để suy ra concept này.
- `concept_text_raw` — cụm từ nguyên bản LLM trả về, trước khi chuẩn hóa.

> **Lý do**: Raw Concept trong luồng supports chính là `ConceptTag` candidates — khác với teaches pipeline trích từ mentions kỹ thuật cụ thể, ở đây là các khái niệm nhận thức/hành vi ẩn (VD: *"tư duy hệ thống", "phân tích yêu cầu", "làm việc nhóm"*). Việc lưu `source_sentence_id` cho phép Layer S6.5 tạo HAS_CONCEPT edge kèm evidence đầy đủ.

### S3 — Candidate Retrieval
Mang các Raw Concepts này đi quét trong ESCO database qua 3 kênh (FAISS, BM25, ESCOXLM-R).

### S4 — RRF Fusion
Hợp nhất kết quả từ 3 kênh để lọc bỏ nhiễu.

### S5 — Multi-signal Ranking
Chấm điểm lại các ứng viên dựa trên công thức đa tín hiệu (Tổng hợp điểm RRF + Điểm Model + Điểm Evidence).

### S6 — Auto-Accept & JSON Export
Tự động dán nhãn phê duyệt (Accepted) cho các ứng viên Top K (mặc định K=10) và xuất ra file JSON chuẩn. Output của S6 là danh sách `AcceptedMapping` — cặp (Raw Concept → ESCO URI) kèm `multi_signal_score`.

---

### ✨ [MỚI] S6.5 — Concept Tag Builder

> **Vị trí**: Chạy sau S6 (Auto-Accept), trước S7 (Neo4j Export).  
> **Mục đích**: Chuyển đổi Raw Concepts đã accept thành `ConceptTag` nodes và edges cho Knowledge Graph, phục vụ GNN link prediction.

**Tại sao đặt sau S6, không phải sau S2?**

Raw Concepts ở S2 chưa được xác nhận là hợp lệ. Chỉ sau S6 mới biết concept nào thực sự match được ESCO skill. ConceptTag chỉ được tạo cho **accepted concepts** — tránh đưa noise vào KG.

**Input nhận từ các bước trước:**

| Nguồn | Dữ liệu nhận |
|---|---|
| S2 | `RawConcept` — concept text gốc + `source_sentence_id` |
| S6 | `AcceptedMapping` — cặp (RawConcept → ESCO URI) + `multi_signal_score` |
| Pipeline config | `pipeline_type = "support"` → xác định `role` trên edge |

**Quy trình xử lý bên trong S6.5:**

```
Bước 1 — Normalize & Dedup:
  concept_text_raw → lowercase, strip → check đã tồn tại trong store chưa?
  Nếu có → reuse node, chỉ thêm edge mới

Bước 2 — Tạo ConceptTag node (nếu chưa có):
  ten: concept đã normalize
  loai: "cognitive" | "interpersonal" | "methodological" | "foundational"
         ← phân loại dựa vào ESCO skillType của skill đã match
  embedding: [...]   ← sinh tại S6.5

Bước 3 — Tạo HAS_CONCEPT edge:
  HocPhan(ma) → [HAS_CONCEPT { role:"support", source_sentence_id, signal_score }] → ConceptTag

Bước 4 — Tạo EVIDENCE_FOR edge:
  ConceptTag → [EVIDENCE_FOR { confidence, pipeline_source:"supports_M5" }] → KyNangESCO(uri)
```

**Output của S6.5:**

```
ConceptTagRecord:
  ten: "tư duy hệ thống"
  loai: "methodological"
  embedding: [...]

HAS_CONCEPT edge:
  role: "support"                      ← lấy từ pipeline_type config
  source_sentence_id: "CLO_2"          ← từ S2 RawConcept
  signal_score: 0.76                   ← từ S6 multi_signal_score

EVIDENCE_FOR edge:
  esco_uri: "esco:skill/yyy"
  confidence: 0.76
  pipeline_source: "supports_M5"
```

> **Phân biệt so với teaches pipeline:**  
> Teaches → ConceptTag loại `algorithm/tool/technique` (kỹ thuật cụ thể)  
> Supports → ConceptTag loại `cognitive/interpersonal/methodological` (nhận thức/hành vi)  
> Cùng 1 ConceptTag store — khác nhau ở `loai` và `role` trên HAS_CONCEPT edge.

---

### S7 — Neo4j Export
**[CẬP NHẬT]** Ngoài Cypher cho `SUPPORTS_SKILL` edges như trước, S7 bổ sung sinh thêm Cypher cho:
- `MERGE (c:ConceptTag {ten: ...})` — tạo hoặc reuse ConceptTag node.
- `MERGE (hp)-[:HAS_CONCEPT {role:"support", ...}]->(c)` — edge từ HocPhan sang ConceptTag.
- `MERGE (c)-[:EVIDENCE_FOR {confidence: ...}]->(ks)` — edge từ ConceptTag sang KyNangESCO.

---

## Luồng dữ liệu tổng quan (Updated)

```
Context (CLO + Mục tiêu + Mô tả)
    │
    ▼
S2 — Concept Extraction (LLM suy luận)
    │
    ├── RawConcept + source_sentence_id ──────────────────────────┐
    │                                                              │
    ▼                                                              │
S3 → S4 → S5 — Retrieval & Ranking                                │
    │                                                              │
    ▼                                                              │
S6 — Auto-Accept (Top K)                                           │
    │                                                              │
    ├── AcceptedMapping (RawConcept → ESCO URI) ──────────────────┤
    │                                                              │
    ▼                                                              ▼
S6.5 — Concept Tag Builder ◄─────────────────────────────────────┘
    │
    ├── ConceptTagRecord
    ├── HAS_CONCEPT {role:"support"}
    └── EVIDENCE_FOR
    │
    ▼
S7 — Neo4j Export (SUPPORTS_SKILL + ConceptTag Cypher)
```

---

## Cấu Trúc Đầu Ra (Output Structure) — Updated

```
data/data_support_skill/
├── IT6204/
│   ├── knowledge__structured_thinking.json
│   └── skill__logical_reasoning.json
├── IT6208/
├── _concept_tags/                                     ← [MỚI]
│   └── IT6204__concept_tags.json                      ← ConceptTagRecord + edges
├── _cypher/
│   ├── IT6204__supports.cypher                        ← SUPPORTS_SKILL (cũ)
│   └── IT6204__concept_tags.cypher                    ← ConceptTag + HAS_CONCEPT + EVIDENCE_FOR [MỚI]
└── _review/
```

---

## Hướng Dẫn Cấu Hình (Configuration)

Mọi thông số trọng yếu được quản lý tập trung tại `configs/default_config.yaml`.
- **Cấu hình LLM**: Bạn có thể đổi mô hình (ví dụ từ `gemini-2.5-flash` sang `gemini-2.5-pro` để suy luận sâu hơn) hoặc chỉnh `temperature` (hiện tại set bằng `0.0` để tối ưu tính nhất quán).
- **Top K**: Số lượng kỹ năng bổ trợ tối đa trả về cho một học phần (Mặc định: 10).
- **[MỚI] `concept_tag.enabled`**: Bật/tắt S6.5. Mặc định `true`.
- **[MỚI] `concept_tag.min_signal_score`**: Ngưỡng score tối thiểu để một RawConcept được đưa vào ConceptTag. Mặc định `0.6`.

---

## Cách Chạy (Execution)

```bash
# Đứng tại thư mục esco-skill-mapping/
$env:PYTHONPATH="src"
python src/supports_skill_pipeline/pipeline.py
```
