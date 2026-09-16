# DATA QUALITY LAYER (TẦNG 3) - Hướng Dẫn Sửa Đổi Mô Tả Môn Học

## 📋 Mục Lục
1. [Tổng Quan](#tổng-quan)
2. [Cấu Trúc Thư Mục](#cấu-trúc-thư-mục)
3. [Quy Trình Sửa Đổi](#quy-trình-sửa-đổi)
4. [Template Sửa Đổi](#template-sửa-đổi)
5. [Checklist Chất Lượng](#checklist-chất-lượng)
6. [Ví Dụ Thực Tế](#ví-dụ-thực-tế)
7. [Tracking & Audit](#tracking--audit)

---

## 🎯 Tổng Quan

### Mục Đích
- **Cải thiện dữ liệu input** để reranker match ESCO skills chính xác hơn
- **Không thay đổi dữ liệu gốc** (original course data)
- **Phát triển liên tục** mô tả môn dựa trên rejection rate

### Nguyên Tắc
```
Semantic Integrity > Raw Quantity
Chất lượng match > Số lượng skills
```

### Khi Nào Cần Sửa Đổi?
- Rejection rate > 30% (ít nhất 30% candidates < 0.35)
- Missed important skills (kỹ năng quan trọng bị bỏ sót)
- Mô tả môn quá chung chung, mơ hồ
- Reranker match score thấp nhất so với các môn cùng loại

---

## 📁 Cấu Trúc Thư Mục

```
data_quality_layer/
├── README.md                          ← File này
├── OPERATIONS_GUIDE.md                ← Hướng dẫn vận hành pipeline
├── CHANGELOG.md                       ← Lịch sử sửa đổi
│
├── enhanced_data/                     ← Dữ liệu đã cải thiện
│   ├── foundational_enhanced.json     ← Mô tả enhanced cho FOUNDATIONAL
│   ├── core_enhanced.json             ← Mô tả enhanced cho CORE
│   ├── specialized_enhanced.json      ← Mô tả enhanced cho SPECIALIZED
│   └── merged_enhanced.json           ← Tổng hợp tất cả
│
├── templates/                         ← Mẫu sửa đổi
│   ├── enhancement_template.md        ← Template cải thiện
│   ├── course_description_template.md ← Template mô tả chi tiết
│   └── learning_outcomes_template.md  ← Template learning outcomes
│
├── logs/                              ← Nhật ký thay đổi
│   ├── modification_log.csv           ← Log chi tiết từng sửa đổi
│   └── quality_metrics.csv            ← Metrics cải thiện
│
├── backups/                           ← Backup dữ liệu gốc
│   ├── original_courses_backup.json   ← Backup dữ liệu gốc
│   └── v1_enhanced_backup.json        ← Backup version cũ
│
└── scripts/                           ← Scripts helper
    ├── enhance_descriptions.py        ← Script cải thiện tự động
    ├── validate_quality.py            ← Script validate chất lượng
    ├── merge_enhanced_data.py         ← Script merge dữ liệu
    └── compare_performance.py         ← Script so sánh khi trước/sau
```

---

## 🔄 Quy Trình Sửa Đổi

### BƯỚC 1: Xác Định Môn Cần Sửa Đổi

```bash
# Chạy script phân tích
python scripts/validate_quality.py --threshold 0.85 --output analysis.json

# Output: Danh sách môn có rejection rate cao
Foundational - "Lập trình cơ bản": 47% reject
Foundational - "Toán đại số": 52% reject
Specialized - "Machine Learning": 8% reject (OK)
```

**Tiêu chí ưu tiên:**
1. Rejection rate > 40% → **PRIORITY A** (phải sửa)
2. Rejection rate 30-40% → **PRIORITY B** (nên sửa)
3. Rejection rate < 20% → **PRIORITY C** (optional)

### BƯỚC 2: Backup Dữ Liệu Gốc

```bash
# Backup automatic lần đầu
cp /path/to/original/courses.json backups/original_courses_backup.json

# Nếu đã có backup, tạo snapshot mới
cp backups/original_courses_backup.json backups/v$(date +%Y%m%d_%H%M%S)_backup.json
```

### BƯỚC 3: Cải Thiện Mô Tả (Manual Process)

Mở file template: `templates/course_description_template.md`

Cho mỗi môn cần sửa:

```markdown
# Cải Thiện Mô Tả Môn Học

## 1. THÔNG TIN CƠ BẢN
- ID Môn: [course_id]
- Tên Môn: [course_name]
- Loại: [FOUNDATIONAL/CORE/SPECIALIZED]
- Rejection Rate Hiện Tại: [X%]

## 2. MÔ TẢ HIỆN TẬI (GỐC - KHÔNG SỬA)
```
[Copy mô tả gốc ở đây]
```

## 3. MÔ TẢ CẢI THIỆN (SAU SỬA ĐỔI)
```
[Viết mô tả chi tiết ở đây]
```

## 4. CHI TIẾT CẢI THIỆN
- [x] Thêm keywords cụ thể
- [x] Mở rộng content description
- [x] Thêm learning outcomes
- [x] Thêm practical examples/projects
- [x] Thêm prerequisites & related skills

## 5. EXPECTED IMPACT
- Expected Rejection Rate Sau: [Y%]
- Expected New Skills: [Z]
```

### BƯỚC 4: Lưu Dữ Liệu Enhanced

Lưu vào file tương ứng:
```json
// enhanced_data/foundational_enhanced.json
{
  "course_id": "CS101",
  "course_name": "Lập Trình Python Cơ Bản",
  "course_type": "FOUNDATIONAL",
  "original_description": "Giới thiệu về lập trình...",
  "enhanced_description": "Lập trình Python cơ bản với emphasis trên...",
  "enhancements": [
    "Added specific Python topics: variables, loops, functions",
    "Added soft skills: problem solving, teamwork, communication",
    "Added practical projects and learning outcomes"
  ],
  "modified_date": "2024-09-08",
  "modified_by": "expert_reviewer",
  "priority": "A",
  "expected_rejection_rate_before": 47,
  "expected_rejection_rate_after": 18
}
```

### BƯỚC 5: Validate & Merge

```bash
# Validate quality
python scripts/validate_quality.py --input enhanced_data/foundational_enhanced.json

# Merge tất cả enhanced data
python scripts/merge_enhanced_data.py --output enhanced_data/merged_enhanced.json
```

### BƯỚC 6: Test Với Reranker

```bash
# Run reranker với enhanced data
python -c "
from reranker import Reranker
import json

r = Reranker()

# Load enhanced data
with open('enhanced_data/foundational_enhanced.json') as f:
    courses = json.load(f)

# Test
for course in courses:
    original_score = r.rank(course['original_description'], skills)
    enhanced_score = r.rank(course['enhanced_description'], skills)
    print(f\"{course['course_name']}: {original_score:.2f} -> {enhanced_score:.2f}\")
"
```

---

## 📄 Template Sửa Đổi

### Template 1: Mô Tả Chi Tiết Cơ Bản

```markdown
# [Tên Môn]

## Giới thiệu
[Giới thiệu chung về môn, tại sao quan trọng]

## Nội Dung Chính
Môn học bao gồm các chủ đề sau:

### 1. [Chủ Đề 1]
- Khái niệm: [chi tiết]
- Ứng dụng: [thực tế]
- Kỹ năng liên quan: [skills]

### 2. [Chủ Đề 2]
- ...

## Learning Outcomes
Sau khóa học, sinh viên sẽ có khả năng:
- [ ] [Outcome 1 - cụ thể, measurable]
- [ ] [Outcome 2 - cụ thể, measurable]
- [ ] [Outcome 3 - cụ thể, measurable]

## Kỹ Năng Phát Triển
- **Hard Skills**: [list]
- **Soft Skills**: [list]

## Dự Án & Bài Tập
- Dự án 1: [mô tả]
- Bài tập nhóm: [mô tả]
- Thực hành tính toán: [mô tả]

## Prerequisites
- [Kiến thức yêu cầu]
- [Kỹ năng cơ bản]

## Related Skills (ESCO)
- Problem Solving
- Communication
- Critical Thinking
- [...]
```

### Template 2: Learning Outcomes Chuẩn

```markdown
## Learning Outcomes (Chi Tiết)

### Level 1: Knowledge (Hiểu Biết)
- SV có thể giải thích khái niệm...
- SV hiểu nguyên lý hoạt động của...

### Level 2: Skills (Kỹ Năng)
- SV có thể viết code để...
- SV có thể phân tích dữ liệu sử dụng...

### Level 3: Competence (Thành Thạo)
- SV có thể giải quyết vấn đề thực tế bằng...
- SV có thể thiết kế & implement một dự án nhỏ...

### Soft Skills
- Collaboration: làm việc nhóm trong các bài tập nhóm
- Communication: trình bày kết quả & defend code decisions
- Problem-Solving: phân tích bài toán & đề xuất giải pháp
```

### Template 3: Enhancement Checklist

```markdown
## Enhancement Checklist

### Phần 1: Mô Tả Chi Tiết
- [ ] Mô tả cơ bản (1-2 dòng) rõ ràng
- [ ] Nội dung chính (3-5 chủ đề) được liệt kê cụ thể
- [ ] Mỗi chủ đề có khái niệm + ứng dụng + kỹ năng liên quan
- [ ] Độ dài mô tả tăng lên ít nhất 50%

### Phần 2: Learning Outcomes
- [ ] Ít nhất 5-8 learning outcomes cụ thể, measurable
- [ ] Phân biệt level: Knowledge → Skills → Competence
- [ ] Sử dụng action verbs: explain, apply, analyze, design, implement

### Phần 3: Practical Elements
- [ ] Có ít nhất 2-3 dự án/bài tập cụ thể
- [ ] Dự án có mô tả input/output rõ ràng
- [ ] Bao gồm cả bài tập cá nhân & nhóm

### Phần 4: Soft Skills
- [ ] Liệt kê hard skills cụ thể (tools, languages)
- [ ] Liệt kê soft skills phát triển (collaboration, communication)
- [ ] Liên kết mỗi outcome với skills cụ thể

### Phần 5: Context & Relevance
- [ ] Giải thích tại sao môn này quan trọng
- [ ] Liên kết với career paths
- [ ] Liên kết với các môn tiên quyết & môn liên quan
```

---

## ✅ Checklist Chất Lượng

### Trước Khi Submit Enhancement

```
□ Dữ liệu gốc được backup đầy đủ
□ Tên file follow naming convention: [course_id]_enhanced.json
□ Metadata đầy đủ: modified_date, modified_by, priority
□ Mô tả cải thiện có ít nhất 200% chiều dài gốc
□ Learning outcomes cụ thể, measurable (SMART goals)
□ Không copy-paste từ bất kỳ nguồn nào không có attribution
□ Kiểm tra typos, formatting

□ JSON valid (no syntax errors)
□ Tất cả required fields đủ
□ Mô tả không chứa PII (personal info)
□ Enhancement track record đầy đủ

Người review: ___________
Ngày: ___________
```

---

## 📊 Ví Dụ Thực Tế

### Ví Dụ 1: FOUNDATIONAL - "Lập Trình Python"

#### Dữ Liệu Gốc
```
ID: CS101
Tên: Lập Trình Python Cơ Bản
Mô tả: "Giới thiệu về lập trình. Học các khái niệm cơ bản. Bài 1-15"
Rejection Rate: 47%
Rejected Skills: Critical Thinking (0.28), Communication (0.32), Teamwork (0.25)
```

#### Dữ Liệu Cải Thiện
```
ID: CS101
Tên: Lập Trình Python Cơ Bản
Mô tả (Cải Thiện):

"Môn học cơ bản về lập trình sử dụng ngôn ngữ Python cho người mới bắt đầu.
Sinh viên sẽ nắm vững các khái niệm lập trình cốt lõi và viết được các 
chương trình Python thực tế.

NƯỚC CHÍNH:

1. CƠ BẢN PYTHON
   - Cú pháp, biến, kiểu dữ liệu (int, float, str, bool)
   - Toán tử và biểu thức
   - Input/Output cơ bản
   Kỹ năng: Computational Thinking, Syntax Understanding

2. LUỒNG ĐIỀU KHIỂN
   - Conditional statements (if-else)
   - Vòng lặp (for, while)
   - Break, continue, nested loops
   Kỹ năng: Problem Decomposition, Logic Building

3. HÀM & MODULARIZATION
   - Định nghĩa hàm, tham số, return values
   - Variable scope (local vs global)
   - Tái sử dụng code
   Kỹ năng: Code Reusability, Abstraction

4. CẤUTRÚC DỮ LIỆU
   - Lists, Tuples, Dictionaries, Sets
   - Slicing, indexing, iteration
   - Nested data structures
   Kỹ năng: Data Structure Knowledge, Algorithm Thinking

5. XỬ LÝ NỀU THÍCH (EXCEPTION HANDLING)
   - Try-except-else-finally
   - Raising exceptions
   - Custom error messages
   Kỹ năng: Error Management, Debugging

6. TẬP TIN & I/O
   - Đọc/ghi file (text, CSV)
   - File operations
   Kỹ năng: File Management, Data Processing

LEARNING OUTCOMES:
Sau khóa học, sinh viên sẽ:
✓ Viết được chương trình Python 100+ dòng code để giải quyết vấn đề
✓ Phân tích bài toán & phân rã thành các bước nhỏ (problem decomposition)
✓ Sử dụng debugger & print statements để tìm lỗi hiệu quả
✓ Làm việc nhóm trong các bài tập nhóm, chia sẻ code & feedback
✓ Trình bày logic & defend các quyết định lập trình
✓ Viết code sạch, dễ đọc, có comments rõ ràng

DỰ ÁN & BÀI TẬP:
1. Dự án nhóm: Xây dựng máy tính đơn giản
   → Phát triển kỹ năng: Teamwork, Communication, Problem-solving
   
2. Bài tập cá nhân: Phân tích dữ liệu CSV
   → Phát triển kỹ năng: Data Analysis, Critical Thinking
   
3. Thực hành mini-project: Chat bot đơn giản
   → Phát triển kỹ năng: NLP basics, User Interaction

HARD SKILLS: Python, OOP Basics, Debugging, File I/O
SOFT SKILLS: Communication, Teamwork, Critical Thinking, Problem-Solving
"

Expected Results:
- Rejection Rate: 47% → 18% ✓
- Accepted Skills: 8 → 16 ✓
```

#### Kết Quả Sau Re-rank
```
Before Enhancement:
- Total Candidates: 50
- Accepted (>0.85): 8 (16%)
- Rejected (<0.35): 24 (47%)

After Enhancement:
- Total Candidates: 50
- Accepted (>0.85): 16 (32%)
- Rejected (<0.35): 9 (18%)

New Skills Accepted:
+ Communication: 0.32 → 0.82 ✓
+ Teamwork: 0.25 → 0.79 ✓
+ Critical Thinking: 0.28 → 0.81 ✓
+ Problem Solving: 0.41 → 0.86 ✓
```

---

## 📋 Tracking & Audit

### File: logs/modification_log.csv

```csv
course_id,course_name,course_type,original_rejection_rate,enhanced_rejection_rate,improvement_pct,new_skills_count,modified_date,modified_by,priority,notes
CS101,Lập Trình Python Cơ Bản,FOUNDATIONAL,47,18,62%,8,2024-09-08,expert_reviewer,A,"Added learning outcomes & practical projects"
CS102,Toán Đại Số,FOUNDATIONAL,52,22,58%,6,2024-09-08,expert_reviewer,A,"Enhanced with concrete examples"
CS201,Machine Learning,SPECIALIZED,8,6,-25%,-2,2024-09-07,expert_reviewer,C,"Already good, minor tweaks"
```

### File: logs/quality_metrics.csv

```csv
date,total_courses,foundational_avg_rejection,core_avg_rejection,specialized_avg_rejection,total_new_skills,overall_improvement_pct
2024-09-01,69,48%,12%,9%,0,0%
2024-09-08,69,22%,11%,8%,34,54%
```

---

## 🚀 Tóm Tắt Quy Trình

```
1. RUN ANALYSIS
   └─> Xác định môn cần sửa (rejection rate > 30%)

2. BACKUP DATA
   └─> Backup dữ liệu gốc vào backups/

3. ENHANCE DESCRIPTIONS
   └─> Sửa đổi mô tả môn sử dụng templates

4. SAVE ENHANCED DATA
   └─> Lưu vào enhanced_data/[type]_enhanced.json

5. VALIDATE & MERGE
   └─> Validate quality + merge tất cả data

6. TEST WITH RERANKER
   └─> Run reranker test để xác nhận improvement

7. LOG CHANGES
   └─> Ghi log vào modification_log.csv

8. DEPLOY
   └─> Cập nhật vào production pipeline
```

---

## ❓ FAQ

**Q: Dữ liệu cải thiện sẽ lưu ở đâu?**
A: Trong thư mục `enhanced_data/`, không ảnh hưởng dữ liệu gốc.

**Q: Nếu cải thiện nhưng rejection rate không giảm?**
A: Có thể môn học thực sự không khớp ESCO skills → Xem xét điều chỉnh nội dung môn, không phải hạ threshold.

**Q: Khi nào deploy cải thiện vào production?**
A: Sau khi test với reranker & xác nhận improvement. Xem `OPERATIONS_GUIDE.md`.

**Q: Có thể sửa đổi lại sau khi deploy không?**
A: Có, hãy backup version cũ trước, sau đó sửa đổi như bình thường.