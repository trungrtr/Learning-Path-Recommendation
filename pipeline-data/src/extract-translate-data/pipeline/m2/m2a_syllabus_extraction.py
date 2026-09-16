"""
M2A – Trích xuất cấu trúc Đề cương từ .raw.md bằng langextract (Google).

Luồng:
  1. Đọc file .md từ data/interim/md/
  2. Gọi langextract.extract() với model Gemini → trích xuất các thực thể
  3. Map kết quả vào Pydantic SyllabusL1
  4. Lưu thành data/interim/extracted/syllabus/{stem}_L1.json

Idempotent: skip nếu _L1.json đã tồn tại và content_hash không đổi.
NULL policy: field không có trong source → null, cấm LLM bịa.
"""

import os
import sys
import json
import re
from pathlib import Path

import langextract as lx
from bs4 import BeautifulSoup

sys.path.append(str(Path(__file__).parent.parent.parent))

from shared.logger import get_logger
from shared.file_io import read_yaml_config, get_content_hash

logger = get_logger("m2a_syllabus_extraction")


# ─── Few-shot examples ──────────────────────────────────────
# Một ví dụ mẫu dựa trên đề cương thật (đã được user sửa tay)
# để hướng dẫn langextract trích xuất đúng pattern.

EXAMPLE_TEXT = """
## ĐỀ CƯƠNG CHI TIẾT HỌC PHẦN

1. Thông tin về học phần

<table><tr><td>Tên học phần (Tiếng Việt)</td><td>Lập trình an toàn</td></tr><tr><td>Tên học phần (Tiếng Anh)</td><td>Secure Programming</td></tr><tr><td>Mã học phần</td><td>IT6168</td></tr><tr><td>Số tín chỉ: TS(LT;ThH/TN;TL/BTL;ĐAMH;TT)</td><td>3(2;1;0;0;0;0)</td></tr></table>

3. Mô tả tóm tắt học phần

Học phần cung cấp cho sinh viên kiến thức về các kỹ thuật lập trình an toàn nhằm bảo vệ chương trình khỏi các lỗ hổng bảo mật.

4. Mục tiêu học phần

- Về kiến thức: Trình bày được các nguyên tắc lập trình an toàn, các lỗ hổng phổ biến và cách phòng tránh.
- Về kỹ năng: Nhận diện và sửa lỗi bảo mật; lập trình an toàn khi xử lý bộ nhớ, đầu vào, và truy cập tài nguyên.
- Về năng lực tự chủ và trách nhiệm: Tuân thủ nguyên tắc bảo mật trong quá trình phát triển phần mềm.

5. Chuẩn đầu ra (CĐR) của học phần
<table><tr><td>MãCĐR của HP</td><td>Nội dung CĐR của HP</td><td>Mã Tiêu chí đánh giá</td><td>Mức độ(I/T/U)</td></tr><tr><td>L1</td><td>Vận dụng các khái niệm, nguyên tắc, quy trình lập trình an toàn trong lập trình để xác định lỗi và kiểm soát dữ liệu</td><td>PI 5.2</td><td>T</td></tr><tr><td>L2</td><td>Sử dụng được các kỹ thuật phòng thủ và bảo vệ tài nguyên hệ thống trong lập trình</td><td>PI 5.2</td><td>T</td></tr></table>

6. Quy định dạy - học và đánh giá

<table><tr><td>Bài</td><td>Tên bài học</td><td>Trực tiếp</td><td>Trực tuyến</td><td>Hình thức</td><td>Mã CLO</td></tr><tr><td>1</td><td>Tổng quan về lập trình an toàn</td><td>6</td><td>0</td><td>LT</td><td>L1</td></tr><tr><td>2</td><td>Quản lý bộ nhớ</td><td>6</td><td>0</td><td>LT</td><td>L1</td></tr><tr><td>3</td><td>Xử lý dữ liệu vào/ra và chống injection</td><td>6</td><td>0</td><td>LT</td><td>L1</td></tr></table>
""".strip()

EXAMPLE_EXTRACTIONS = [
    lx.data.Extraction(
        extraction_class="hoc_phan",
        extraction_text="Lập trình an toàn",
        attributes={
            "ma_hoc_phan": "IT6168",
            "ten_vi": "Lập trình an toàn",
            "ten_en": "Secure Programming",
            "so_tin_chi_tong": "3",
            "mo_ta_tom_tat": "Học phần cung cấp cho sinh viên kiến thức về các kỹ thuật lập trình an toàn nhằm bảo vệ chương trình khỏi các lỗ hổng bảo mật.",
        },
    ),
    lx.data.Extraction(
        extraction_class="muc_tieu",
        extraction_text="Trình bày được các nguyên tắc lập trình an toàn",
        attributes={
            "ma_muc_tieu": "G1",
            "loai_muc_tieu": "KIEN_THUC",
            "noi_dung": "Trình bày được các nguyên tắc lập trình an toàn, các lỗ hổng phổ biến và cách phòng tránh.",
        },
    ),
    lx.data.Extraction(
        extraction_class="muc_tieu",
        extraction_text="Nhận diện và sửa lỗi bảo mật",
        attributes={
            "ma_muc_tieu": "G2",
            "loai_muc_tieu": "KY_NANG",
            "noi_dung": "Nhận diện và sửa lỗi bảo mật; lập trình an toàn khi xử lý bộ nhớ, đầu vào, và truy cập tài nguyên.",
        },
    ),
    lx.data.Extraction(
        extraction_class="muc_tieu",
        extraction_text="Tuân thủ nguyên tắc bảo mật",
        attributes={
            "ma_muc_tieu": "G3",
            "loai_muc_tieu": "TU_CHU_TRACH_NHIEM",
            "noi_dung": "Tuân thủ nguyên tắc bảo mật trong quá trình phát triển phần mềm.",
        },
    ),
    lx.data.Extraction(
        extraction_class="clo",
        extraction_text="Vận dụng các khái niệm, nguyên tắc, quy trình lập trình an toàn",
        attributes={
            "ma_cdr_goc": "L1",
            "noi_dung": "Vận dụng các khái niệm, nguyên tắc, quy trình lập trình an toàn trong lập trình để xác định lỗi và kiểm soát dữ liệu",
            "pi_so": "PI 5.2",
            "muc_do": "T",
        },
    ),
    lx.data.Extraction(
        extraction_class="clo",
        extraction_text="Sử dụng được các kỹ thuật phòng thủ",
        attributes={
            "ma_cdr_goc": "L2",
            "noi_dung": "Sử dụng được các kỹ thuật phòng thủ và bảo vệ tài nguyên hệ thống trong lập trình",
            "pi_so": "PI 5.2",
            "muc_do": "T",
        },
    ),
    lx.data.Extraction(
        extraction_class="bai_hoc",
        extraction_text="Tổng quan về lập trình an toàn",
        attributes={
            "so_thu_tu": "1",
            "ten_bai": "Tổng quan về lập trình an toàn",
            "gio_truc_tiep": "6",
            "gio_truc_tuyen": "0",
            "hinh_thuc_day_hoc": "LT",
            "ma_clo": "L1",
        },
    ),
    lx.data.Extraction(
        extraction_class="bai_hoc",
        extraction_text="Quản lý bộ nhớ",
        attributes={
            "so_thu_tu": "2",
            "ten_bai": "Quản lý bộ nhớ",
            "gio_truc_tiep": "6",
            "gio_truc_tuyen": "0",
            "hinh_thuc_day_hoc": "LT",
            "ma_clo": "L1",
        },
    ),
    lx.data.Extraction(
        extraction_class="bai_hoc",
        extraction_text="Xử lý dữ liệu vào/ra và chống injection",
        attributes={
            "so_thu_tu": "3",
            "ten_bai": "Xử lý dữ liệu vào/ra và chống injection",
            "ma_clo": "L1",
        },
    ),
]


EXAMPLE_TEXT_2 = """
## ĐỀ CƯƠNG CHI TIẾT HỌC PHẦN

4. Mục tiêu học phần

Học phần trang bị cho sinh viên các kiến thức nền tảng về các kỹ thuật truyền thông số và mô phỏng để từ đó sinh viên có thể áp dụng khảo sát, xây dựng sơ đồ và đánh giá chất lượng tham số của hệ thống truyền thông số.
""".strip()

EXAMPLE_EXTRACTIONS_2 = [
    lx.data.Extraction(
        extraction_class="muc_tieu",
        extraction_text="Học phần trang bị cho sinh viên các kiến thức nền tảng về các kỹ thuật truyền thông số",
        attributes={
            "ma_muc_tieu": "G1",
            "loai_muc_tieu": "KY_NANG",
            "noi_dung": "Học phần trang bị cho sinh viên các kiến thức nền tảng về các kỹ thuật truyền thông số và mô phỏng để từ đó sinh viên có thể áp dụng khảo sát, xây dựng sơ đồ và đánh giá chất lượng tham số của hệ thống truyền thông số.",
        },
    ),
]


EXAMPLE_TEXT_3 = """
## ĐỀ CƯƠNG CHI TIẾT HỌC PHẦN

4. Mục tiêu học phần

<table><tr><td>Mục tiêu</td><td>Mô tả mục tiêu</td><td>CĐR của CTĐT (SO)</td></tr><tr><td>Kiến thức (G1)</td><td>Trang bị cho sinh viên kiến thức về cấu tạo, nguyên lý hoạt động, trao đổi thông tin giữa các bộ phận của máy tính và ngôn ngữ lập trình hợp ngữ trên họ vi xử lý 80x86 của Intel.</td><td>PI 1.1</td></tr><tr><td>Kỹ năng (G2)</td><td>Phân tích, thiết kế, cài đặt, kiểm thử các chương trình viết bằng hợp ngữ.</td><td>PI 1.2</td></tr></table>
""".strip()

EXAMPLE_EXTRACTIONS_3 = [
    lx.data.Extraction(
        extraction_class="muc_tieu",
        extraction_text="Kiến thức (G1)",
        attributes={
            "ma_muc_tieu": "G1",
            "loai_muc_tieu": "KIEN_THUC",
            "noi_dung": "Trang bị cho sinh viên kiến thức về cấu tạo, nguyên lý hoạt động, trao đổi thông tin giữa các bộ phận của máy tính và ngôn ngữ lập trình hợp ngữ trên họ vi xử lý 80x86 của Intel.",
        },
    ),
    lx.data.Extraction(
        extraction_class="muc_tieu",
        extraction_text="Kỹ năng (G2)",
        attributes={
            "ma_muc_tieu": "G2",
            "loai_muc_tieu": "KY_NANG",
            "noi_dung": "Phân tích, thiết kế, cài đặt, kiểm thử các chương trình viết bằng hợp ngữ.",
        },
    ),
]


EXAMPLE_TEXT_4 = """
## ĐỀ CƯƠNG CHI TIẾT HỌC PHẦN

4. Mục tiêu học phần

Học phần này nhằm trang bị cho sinh viên:

\- (MT1): Trình bày được các khái niệm cơ bản, nguyên lý hoạt động của các thuật toán học máy phổ biến (phân cụm, phân loại, phát hiện bất thường).

\- (MT2): Vận dụng được các kỹ thuật học máy để giải quyết các bài toán trong an ninh mạng.
""".strip()

EXAMPLE_EXTRACTIONS_4 = [
    lx.data.Extraction(
        extraction_class="muc_tieu",
        extraction_text="(MT1): Trình bày được các khái niệm cơ bản",
        attributes={
            "ma_muc_tieu": "MT1",
            "loai_muc_tieu": "KIEN_THUC",
            "noi_dung": "Trình bày được các khái niệm cơ bản, nguyên lý hoạt động của các thuật toán học máy phổ biến (phân cụm, phân loại, phát hiện bất thường).",
        },
    ),
    lx.data.Extraction(
        extraction_class="muc_tieu",
        extraction_text="(MT2): Vận dụng được các kỹ thuật học máy",
        attributes={
            "ma_muc_tieu": "MT2",
            "loai_muc_tieu": "KY_NANG",
            "noi_dung": "Vận dụng được các kỹ thuật học máy để giải quyết các bài toán trong an ninh mạng.",
        },
    ),
]


def _build_examples() -> list[lx.data.ExampleData]:
    """Tạo few-shot examples cho langextract."""
    return [
        lx.data.ExampleData(
            text=EXAMPLE_TEXT,
            extractions=EXAMPLE_EXTRACTIONS,
        ),
        lx.data.ExampleData(
            text=EXAMPLE_TEXT_2,
            extractions=EXAMPLE_EXTRACTIONS_2,
        ),
        lx.data.ExampleData(
            text=EXAMPLE_TEXT_3,
            extractions=EXAMPLE_EXTRACTIONS_3,
        ),
        lx.data.ExampleData(
            text=EXAMPLE_TEXT_4,
            extractions=EXAMPLE_EXTRACTIONS_4,
        )
    ]


def _load_prompt() -> str:
    """Đọc prompt mô tả task trích xuất."""
    prompt_path = Path(__file__).parent.parent / "prompts" / "extract.txt"
    return prompt_path.read_text(encoding="utf-8")


def _clean_str(val) -> str | None:
    if val is None:
        return None
    v = str(val).strip()
    if v.lower() in ("null", "none", "", "n/a"):
        return None
    return v


def _extract_course_metadata(md_text: str, source_stem: str) -> dict[str, str | None]:
    """Đọc mã và tên Anh trực tiếp từ bảng thông tin học phần trong source."""
    metadata: dict[str, str | None] = {
        "ma_hoc_phan": None,
        "ten_vi": None,
        "ten_en": None,
    }

    soup = BeautifulSoup(md_text, "html.parser")
    for row in soup.find_all("tr"):
        cells = row.find_all(["td", "th"])
        if len(cells) < 2:
            continue

        label = re.sub(r"\s+", " ", cells[0].get_text(" ", strip=True)).casefold()
        value = _clean_str(cells[1].get_text(" ", strip=True))
        if "mã học phần" in label or "ma hoc phan" in label:
            metadata["ma_hoc_phan"] = value
        elif "tên học phần (tiếng anh)" in label or "ten hoc phan (tieng anh)" in label:
            metadata["ten_en"] = value
        elif "tên học phần (tiếng việt)" in label or "ten hoc phan (tieng viet)" in label:
            metadata["ten_vi"] = value

    if not metadata["ma_hoc_phan"]:
        plain_text = re.sub(r"\s+", " ", soup.get_text(" ", strip=True))
        code_match = re.search(
            r"(?:mã|ma)\s*học\s*phần\s*[:\-]?\s*([A-Za-z]{2}\d{4})",
            plain_text,
            re.IGNORECASE,
        )
        if code_match:
            metadata["ma_hoc_phan"] = code_match.group(1).upper()

    code_match = re.search(r"\b[A-Za-z]{2,}\d{3,}\b", source_stem)
    if not metadata["ma_hoc_phan"] and code_match:
        metadata["ma_hoc_phan"] = code_match.group(0).upper()

    return metadata


def _extractions_to_syllabus_dict(
    extractions: list, source_stem: str, source_text: str = ""
) -> dict:
    """Chuyển đổi kết quả langextract thành dict theo schema SyllabusL1."""
    # Chỉ lấy extractions có grounding (char_interval != None)
    grounded = [e for e in extractions if e.char_interval]
    logger.info(f"Grounded extractions: {len(grounded)}/{len(extractions)}")

    source_metadata = _extract_course_metadata(source_text, source_stem)
    hoc_phan = {}
    muc_tieu_list = []
    clo_list = []
    bai_hoc_list = []

    for ext in grounded:
        attrs = ext.attributes or {}

        if ext.extraction_class == "hoc_phan":
            hoc_phan = {
                "ma_hoc_phan": _clean_str(attrs.get("ma_hoc_phan")),
                "ten_vi": _clean_str(attrs.get("ten_vi")),
                "ten_en": _clean_str(attrs.get("ten_en")),
                "so_tin_chi_tong": _safe_float(attrs.get("so_tin_chi_tong")),
                "mo_ta_tom_tat": _clean_str(attrs.get("mo_ta_tom_tat")),
            }

        elif ext.extraction_class == "muc_tieu":
            loai = _clean_str(attrs.get("loai_muc_tieu"))
            if loai and loai not in ("KIEN_THUC", "KY_NANG", "TU_CHU_TRACH_NHIEM"):
                loai = None  # không hợp lệ → null
            muc_tieu_list.append({
                "ma_muc_tieu": _clean_str(attrs.get("ma_muc_tieu")),
                "loai_muc_tieu": loai,
                "noi_dung": _clean_str(attrs.get("noi_dung")) or ext.extraction_text,
                "so_ctdt": _split_list(attrs.get("so_ctdt")),
            })

        elif ext.extraction_class == "clo":
            clo_list.append({
                "ma_cdr_goc": _clean_str(attrs.get("ma_cdr_goc")),
                "noi_dung": _clean_str(attrs.get("noi_dung")) or ext.extraction_text,
                "pi_so": _split_list(attrs.get("pi_so")),
                "muc_do": _clean_str(attrs.get("muc_do")),
            })

        elif ext.extraction_class == "bai_hoc":
            bai_hoc_list.append({
                "so_thu_tu": _clean_str(attrs.get("so_thu_tu")),
                "ten_bai": _clean_str(attrs.get("ten_bai")) or ext.extraction_text,
                "noi_dung_tom_tat": _clean_str(attrs.get("noi_dung_tom_tat")),
                "ma_clo": _split_list(attrs.get("ma_clo")),
            })

    # Mã học phần trong source là authoritative; không cho LLM thay thế mã.
    for field, value in source_metadata.items():
        if value and (field == "ma_hoc_phan" or not hoc_phan.get(field)):
            hoc_phan[field] = value

    ma_hp = hoc_phan.get("ma_hoc_phan") or source_stem.split("_")[0]
    hoc_phan["ma_hoc_phan"] = ma_hp

    return {
        "ma_hoc_phan": ma_hp,
        "source_course_code": source_metadata.get("ma_hoc_phan"),
        "source_file": source_stem,
        "hoc_phan": hoc_phan if hoc_phan else {
            "ma_hoc_phan": ma_hp,
            "ten_vi": None, "ten_en": None,
            "so_tin_chi_tong": None, "mo_ta_tom_tat": None,
        },
        "muc_tieu_hoc_phan": muc_tieu_list or None,
        "clo": clo_list or None,
        "bai_hoc": bai_hoc_list or None,
    }


def _safe_float(val) -> float | None:
    if val is None:
        return None
    try:
        return float(str(val).replace(",", "."))
    except (ValueError, TypeError):
        return None


def _split_list(val) -> list[str]:
    if val is None:
        return []
    if isinstance(val, list):
        return val
    return [s.strip() for s in str(val).split(",") if s.strip()]


API_KEYS = []
CURRENT_KEY_INDEX = 0

def init_api_keys():
    global API_KEYS
    keys = []
    for i in range(1, 10):
        key_raw = os.getenv(f"GEMINI_API_KEY{i}")
        if key_raw:
            keys.append(key_raw.strip("'\""))
    if not keys:
        # Fallback to single key if numbered keys aren't found
        key_raw = os.getenv("GEMINI_API_KEY")
        if key_raw:
            keys.append(key_raw.strip("'\""))
    API_KEYS = keys

CURRENT_MODEL = "gemini-2.0-flash"

def extract_single(md_text: str, md_name: str, md_stem: str) -> dict | None:
    """Trích xuất 1 file .md → dict (SyllabusL1-compatible)."""
    global CURRENT_KEY_INDEX
    global CURRENT_MODEL
    
    if not API_KEYS:
        init_api_keys()
        
    if not API_KEYS:
        logger.error("Missing GEMINI_API_KEY in environment")
        return None

    prompt = _load_prompt()
    examples = _build_examples()

    logger.info(f"Calling langextract on {md_name} ({len(md_text)} chars) using {CURRENT_MODEL}...")

    # Allow more attempts in case we need to rotate keys AND models
    for attempt in range(len(API_KEYS) * 2):
        api_key = API_KEYS[CURRENT_KEY_INDEX]
        
        try:
            result = lx.extract(
                text_or_documents=md_text,
                prompt_description=prompt,
                examples=examples,
                model_id=CURRENT_MODEL,
                api_key=api_key,
                extraction_passes=1,
                max_workers=1,
            )
            
            if not result or not result.extractions:
                logger.error(f"No extractions returned for {md_name}")
                return None
                
            logger.info(f"Got {len(result.extractions)} extractions for {md_name}")
            return _extractions_to_syllabus_dict(result.extractions, md_stem, md_text)
            
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str or "503" in error_str:
                logger.warning(f"Key index {CURRENT_KEY_INDEX} exhausted/unavailable. Switching key.")
                CURRENT_KEY_INDEX = (CURRENT_KEY_INDEX + 1) % len(API_KEYS)
                continue
            elif "404" in error_str or "400" in error_str or "not found" in error_str.lower() or "invalid" in error_str.lower() or "not supported" in error_str.lower():
                if CURRENT_MODEL == "gemini-2.0-flash":
                    logger.warning(f"Model gemini-2.0-flash failed ({e}). Switching to gemini-3.1-flash-lite.")
                    CURRENT_MODEL = "gemini-3.1-flash-lite"
                    continue
                else:
                    logger.exception(f"langextract error for {md_name} with {CURRENT_MODEL}: {e}")
                    return None
            else:
                logger.exception(f"langextract error for {md_name} with {CURRENT_MODEL}: {e}")
                return None
                
    logger.error(f"All API keys and models exhausted/unavailable for {md_name}.")
    return None


def process_batch():
    """Xử lý toàn bộ file .md trong thư mục interim/md/."""
    config = read_yaml_config("config.yaml")
    model_id = config["models"]["gemini_extraction"]

    md_dir = Path(config["paths"]["markdown"])
    out_dir = Path(config["paths"]["extracted"])
    out_dir.mkdir(parents=True, exist_ok=True)

    md_files = sorted(md_dir.glob("*.md"))
    total = len(md_files)
    done = skip = fail = 0

    for idx, md_path in enumerate(md_files, 1):
        if "_EN_" in md_path.name:
            logger.info(f"[{idx}/{total}] SKIP (English): {md_path.name}")
            skip += 1
            continue
            
        stem = md_path.stem.replace(".raw", "")
        # Lưu toàn bộ JSON của M2A vào thư mục hoc_phan
        hoc_phan_dir = out_dir / "hoc_phan"
        hoc_phan_dir.mkdir(parents=True, exist_ok=True)
        out_path = hoc_phan_dir / f"{stem}_L1.json"

        # Idempotent: skip nếu đã có
        logger.info(f"[{idx}/{total}] Extracting: {md_path.name}")
        
        try:
            md_text = md_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            logger.error(f"[{idx}/{total}] Lỗi: File không còn tồn tại: {md_path.name}")
            fail += 1
            continue

        source_hash = get_content_hash(md_text)
        if out_path.exists():
            try:
                existing = json.loads(out_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                existing = None
            if isinstance(existing, dict) and existing.get("content_hash") == source_hash:
                logger.info(f"[{idx}/{total}] SKIP (unchanged): {stem}")
                skip += 1
                continue

        result_dict = extract_single(md_text, md_path.name, stem)
        if not result_dict:
            fail += 1
            continue

        # Thêm content_hash để hỗ trợ idempotency
        result_dict["content_hash"] = source_hash

        # Lưu file tổng hợp vào hoc_phan/
        out_path.write_text(
            json.dumps(result_dict, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        
        done += 1
        logger.info(f"[{idx}/{total}] SAVED: {out_path.name}")

    logger.info(f"=== M2A DONE: {done} extracted, {skip} skipped, {fail} failed ===")


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parents[4] / ".env")
    process_batch()
