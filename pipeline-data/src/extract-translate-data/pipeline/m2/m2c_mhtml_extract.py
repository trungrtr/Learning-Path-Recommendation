"""
M2C MHTML Extraction

Converts MHTML files from data/raw/5_mhtml to Markdown files in data/raw/1_markdown.
This allows M2A to process them via LLM.
"""

import sys
import email
from email import policy
from pathlib import Path
from bs4 import BeautifulSoup

sys.path.append(str(Path(__file__).parent.parent.parent))

from shared.logger import get_logger
from shared.file_io import read_yaml_config

logger = get_logger("m2c_mhtml_extract")

import json
import re
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parents[4] / ".env")
from pipeline.m2.m2a_syllabus_extraction import extract_single
from shared.file_io import get_content_hash

def mhtml_extract():
    """Extract HTML from MHTML files, convert to plain text, and extract to JSON via LLM."""
    config = read_yaml_config("config.yaml")
    
    # Resolving paths
    mhtml_dir = Path(config["paths"]["mhtml"])
    out_dir = Path(config["paths"]["extracted"]) / "hoc_phan_bo_sung"
    
    out_dir.mkdir(parents=True, exist_ok=True)
    
    if not mhtml_dir.exists():
        logger.warning(f"Thư mục {mhtml_dir} không tồn tại.")
        return
        
    mhtml_files = list(mhtml_dir.glob("*.mhtml"))
    total = len(mhtml_files)
    processed = 0
    skipped = 0
    errors = 0
    
    logger.info(f"Bắt đầu trích xuất {total} file MHTML...")
    
    for idx, file_path in enumerate(mhtml_files, 1):
        if "_EN_" in file_path.name:
            logger.info(f"[{idx}/{total}] SKIP (English): {file_path.name}")
            skipped += 1
            continue
            
        stem = file_path.stem
        out_file = out_dir / f"{stem}_L1.json"
        
        logger.info(f"[{idx}/{total}] Extracting: {file_path.name}")
        
        try:
            with open(file_path, "rb") as f:
                msg = email.message_from_bytes(f.read())
                
            html_content = None
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == "text/html":
                    html_content = part.get_payload(decode=True).decode('utf-8', errors='replace')
                    break
                    
            if not html_content:
                logger.error(f"[{idx}/{total}] Lỗi: Không tìm thấy nội dung text/html trong {file_path.name}")
                errors += 1
                continue
                
            # Parse HTML → plain text theo logic của user
            soup = BeautifulSoup(html_content, "html.parser")
            container = soup.find("div", class_="main-content") or soup.body

            info = {}
            chuong_trinh = []

            for row in container.find_all("tr"):
                cells = row.find_all("td", recursive=False)
                if len(cells) < 2:
                    continue
                label_cell, value_cell = cells[0], cells[1]

                label_classes = label_cell.get("class") or []
                if "k-table-view" not in label_classes:
                    continue

                label = label_cell.get_text(" ", strip=True)

                nested_table = value_cell.find("table")
                if nested_table is not None:
                    for r in nested_table.find_all("tr", class_="kTableRow"):
                        tds = r.find_all("td")
                        if len(tds) < 3 or tds[0].get("colspan"):
                            continue
                        ten_muc = tds[1].get_text(" ", strip=True)
                        noi_dung = tds[2].get_text(" ", strip=True)
                        if ten_muc:
                            chuong_trinh.append(f"{ten_muc}: {noi_dung}" if noi_dung else ten_muc)
                    nested_table.extract()
                    continue

                value = value_cell.get_text(" ", strip=True)
                if label:
                    info[label] = value

            if chuong_trinh:
                deduped = []
                for x in chuong_trinh:
                    if not deduped or deduped[-1] != x:
                        deduped.append(x)
                info["Noi dung chuong trinh (danh sach)"] = deduped

            text = json.dumps(info, ensure_ascii=False, indent=2)
            source_hash = get_content_hash(text.strip())

            # Trực tiếp map sang SyllabusL1 schema mà không cần dùng LLM
            ma_hp = info.get("Mã in") or info.get("Mã học phần") or stem.split("_")[0]
            so_tc = info.get("Số tín chỉ", "")
            try:
                so_tc_float = float(so_tc)
            except ValueError:
                so_tc_float = None

            bai_hoc_list = []
            for i, bai in enumerate(info.get("Noi dung chuong trinh (danh sach)", [])):
                bai_hoc_list.append({
                    "so_thu_tu": str(i + 1),
                    "ten_bai": bai,
                    "noi_dung_tom_tat": None,
                    "ma_clo": []
                })

            muc_tieu_list = []
            clo_list = None
            
            # Gọi LLM để bổ sung mục tiêu (đủ 3 loại) và CLO (tối thiểu 2) nếu thiếu
            ten_hp = info.get("Tên học phần", "")
            mo_ta = info.get("Mô tả", "")
            bai_hocs = [bai["ten_bai"] for bai in bai_hoc_list]
            
            prompt = f"""
Bạn là một chuyên gia thiết kế chương trình đào tạo đại học.
Dựa vào các thông tin sau của một học phần:
- Tên học phần: {ten_hp}
- Mô tả: {mo_ta}
- Danh sách bài học: {json.dumps(bai_hocs, ensure_ascii=False)}
- Mục tiêu ban đầu (nếu có): {info.get("Mục tiêu", "")}

Hãy sinh ra:
1. Danh sách Mục tiêu học phần: đảm bảo phải có đủ 3 loại mục tiêu (KIEN_THUC, KY_NANG, TU_CHU_TRACH_NHIEM).
2. Danh sách Chuẩn đầu ra (CLO): tối thiểu 2 CLO.
Lưu ý: Các nội dung sinh ra phải được suy luận chặt chẽ từ thông tin đầu vào.

Trả về kết quả ở định dạng JSON với cấu trúc chính xác như sau:
{{
  "muc_tieu": [
    {{
      "ma_muc_tieu": "G1",
      "loai_muc_tieu": "KIEN_THUC",
      "noi_dung": "...",
      "so_ctdt": []
    }},
    {{
      "ma_muc_tieu": "G2",
      "loai_muc_tieu": "KY_NANG",
      "noi_dung": "...",
      "so_ctdt": []
    }},
    {{
      "ma_muc_tieu": "G3",
      "loai_muc_tieu": "TU_CHU_TRACH_NHIEM",
      "noi_dung": "...",
      "so_ctdt": []
    }}
  ],
  "clo": [
    {{
      "ma_cdr_goc": "L1",
      "noi_dung": "...",
      "pi_so": [],
      "muc_do": "T"
    }}
  ]
}}
Chỉ trả về chuỗi JSON, không có markdown formatting hay text nào khác.
"""
            try:
                from shared.llm_client import call_gemini
                llm_model = config.get("models", {}).get("gemini_extraction", "gemini-3.5-flash-lite")
                llm_resp = call_gemini(prompt, llm_model)
                
                # Làm sạch markdown json
                json_str = llm_resp.strip()
                if json_str.startswith("```"):
                    import re
                    json_str = re.sub(r'^```[^\n]*\n', '', json_str)
                    json_str = re.sub(r'\n```$', '', json_str)
                    
                generated_data = json.loads(json_str)
                
                if "muc_tieu" in generated_data:
                    muc_tieu_list = generated_data["muc_tieu"]
                if "clo" in generated_data:
                    clo_list = generated_data["clo"]
                    
                logger.info(f"[{idx}/{total}] Đã sinh thành công mục tiêu và CLO bằng LLM.")
            except Exception as e:
                logger.error(f"[{idx}/{total}] Lỗi khi sinh mục tiêu/CLO bằng LLM: {e}")
                # Fallback to simple extraction
                if info.get("Mục tiêu"):
                    muc_tieu_list.append({
                        "ma_muc_tieu": "G1",
                        "loai_muc_tieu": "KIEN_THUC",
                        "noi_dung": info.get("Mục tiêu"),
                        "so_ctdt": []
                    })

            result_dict = {
                "ma_hoc_phan": ma_hp,
                "source_course_code": ma_hp,
                "source_file": file_path.name,
                "hoc_phan": {
                    "ma_hoc_phan": ma_hp,
                    "ten_vi": info.get("Tên học phần"),
                    "ten_en": None,
                    "so_tin_chi_tong": so_tc_float,
                    "mo_ta_tom_tat": info.get("Mô tả")
                },
                "muc_tieu_hoc_phan": muc_tieu_list if muc_tieu_list else None,
                "clo": clo_list if clo_list else None,
                "bai_hoc": bai_hoc_list if bai_hoc_list else None,
            }

            result_dict["content_hash"] = source_hash

            # Write to output file
            with open(out_file, "w", encoding="utf-8") as out_f:
                json.dump(result_dict, out_f, ensure_ascii=False, indent=2)
                
            logger.info(f"[{idx}/{total}] THÀNH CÔNG: Đã lưu {out_file.name}")
            processed += 1
            
        except Exception as e:
            logger.exception(f"[{idx}/{total}] Lỗi không xác định khi xử lý {file_path.name}: {e}")
            errors += 1
            
    logger.info(f"Hoàn tất M2C MHTML Extraction. Processed: {processed}, Skipped: {skipped}, Errors: {errors}")

if __name__ == "__main__":
    mhtml_extract()
