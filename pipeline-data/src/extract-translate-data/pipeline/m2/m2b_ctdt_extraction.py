"""M2B CTDT extraction (Rule-based, không LLM)"""

import os
import re
import sys
from pathlib import Path
from pydantic import ValidationError

sys.path.append(str(Path(__file__).parent.parent.parent))

from pipeline.schemas import (
    CtdtSchema, ChuongTrinhDaoTao, NhomHocPhan, HocPhanCtdt, QuanHeHocPhan
)
from shared.file_io import read_json, write_json, get_content_hash, read_yaml_config
from shared.logger import get_logger

logger = get_logger("m2_extraction")

def parse_ctdt_markdown(content: str, file_name: str) -> CtdtSchema | None:
    ma_ctdt = None
    ten_ctdt = None
    bac_dao_tao = None
    
    lines = content.split('\n')
    
    # 1. Parse Metadata
    for line in lines:
        if '- **Mã ngành:**' in line:
            ma_ctdt = line.split('**Mã ngành:**')[1].strip()
        elif '- **Tên ngành:**' in line:
            ten_ctdt = line.split('**Tên ngành:**')[1].strip()
        elif '- **Hệ đào tạo:**' in line:
            bac_dao_tao = line.split('**Hệ đào tạo:**')[1].strip()
            
    if not ma_ctdt:
        match = re.search(r'CTDT_(\w+)', file_name)
        if match:
            ma_ctdt = match.group(1)
        else:
            logger.error(f"Không tìm thấy ma_ctdt cho file {file_name}")
            return None
            
    chuong_trinh_dao_tao = ChuongTrinhDaoTao(
        ma_ctdt=ma_ctdt,
        ten_ctdt=ten_ctdt,
        bac_dao_tao=bac_dao_tao,
        phien_ban="v1"
    )
    
    nhom_hoc_phan_list = []
    
    current_h2 = ""
    current_h3 = ""
    current_loai_nhom = "BAT_BUOC"
    current_nhom = None
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith('## '):
            current_h2 = line[3:].strip()
            current_h3 = ""
            current_loai_nhom = "BAT_BUOC"
        elif line.startswith('### '):
            current_h3 = line[4:].strip()
            if 'bắt buộc' in current_h3.lower():
                current_loai_nhom = "BAT_BUOC"
            else:
                current_loai_nhom = "TU_CHON"
                
        elif line.startswith('| STT'):
            ten_nhom = current_h2
            if current_h3:
                ten_nhom = f"{current_h2} - {current_h3}"
                
            so_tin_chi_yeu_cau = None
            tc_match = re.search(r'(\d+\.?\d*)\s*tín chỉ', ten_nhom.lower())
            if tc_match:
                so_tin_chi_yeu_cau = float(tc_match.group(1))
                
            current_nhom = NhomHocPhan(
                ten_nhom=ten_nhom,
                loai_nhom=current_loai_nhom,
                so_tin_chi_yeu_cau=so_tin_chi_yeu_cau,
                hoc_phan=[]
            )
            nhom_hoc_phan_list.append(current_nhom)
            
            i += 1 # skip | STT |...
            i += 1 # skip |---|...
            
            while i < len(lines) and lines[i].strip().startswith('|'):
                row_line = lines[i].strip()
                parts = [p.strip() for p in row_line.split('|')]
                if len(parts) >= 8:
                    ma_hp = parts[2]
                    ten_hp = parts[3]
                    try:
                        tc = float(parts[4]) if parts[4] else None
                    except ValueError:
                        tc = None
                    try:
                        hk = int(parts[5]) if parts[5] else None
                    except ValueError:
                        hk = None
                        
                    tq_str = parts[6]
                    ht_str = parts[7]
                    
                    quan_he = []
                    for req in [x.strip() for x in tq_str.split(',') if x.strip()]:
                        quan_he.append(QuanHeHocPhan(loai="TIEN_QUYET", ma_hoc_phan=req, ten_hoc_phan=None))
                    for req in [x.strip() for x in ht_str.split(',') if x.strip()]:
                        quan_he.append(QuanHeHocPhan(loai="HOC_TRUOC", ma_hoc_phan=req, ten_hoc_phan=None))
                        
                    hp_obj = HocPhanCtdt(
                        ma_hoc_phan=ma_hp,
                        ten_hoc_phan=ten_hp,
                        so_tin_chi_tong=tc,
                        hoc_ky_goi_y=hk,
                        quan_he=quan_he
                    )
                    current_nhom.hoc_phan.append(hp_obj)
                i += 1
            continue
        i += 1
        
    return CtdtSchema(
        ma_ctdt=ma_ctdt,
        crawl_course_key=f"CTDT_{ma_ctdt}",
        chuong_trinh_dao_tao=chuong_trinh_dao_tao,
        nhom_hoc_phan=nhom_hoc_phan_list
    )

def ctdt_extract():
    """Trích xuất từ raw/ctdt sang interim/extracted/ctdt."""
    config = read_yaml_config("config.yaml")
    raw_dir = Path(config["paths"]["ctdt"])
    out_dir = Path(config["paths"]["extracted"]) / "ctdt"
    conflict_dir = Path("logs/conflicts")
    
    out_dir.mkdir(parents=True, exist_ok=True)
    conflict_dir.mkdir(parents=True, exist_ok=True)
    
    if not raw_dir.exists():
        logger.warning(f"Không tìm thấy thư mục {raw_dir}")
        return
        
    processed_count = 0
    skipped_count = 0
    error_count = 0
    
    for file_path in raw_dir.glob("*.md"):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                
            content_hash = get_content_hash(content)
            
            ma_ctdt_guess = file_path.stem
            match = re.search(r'CTDT_(\w+)', file_path.name)
            if match: ma_ctdt_guess = match.group(1)
            out_file = out_dir / f"CTDT_{ma_ctdt_guess}.json"
            
            if out_file.exists():
                try:
                    existing_data = read_json(out_file)
                    if existing_data.get("_content_hash") == content_hash:
                        logger.info(f"Skip {file_path.name} do không thay đổi (hash match).")
                        skipped_count += 1
                        continue
                except Exception:
                    pass # file lỗi thì ghi đè
            
            schema_obj = parse_ctdt_markdown(content, file_path.name)
            if schema_obj:
                out_file = out_dir / f"CTDT_{schema_obj.ma_ctdt}.json"
                out_data = schema_obj.model_dump()
                out_data["_content_hash"] = content_hash
                write_json(out_file, out_data)
                logger.info(f"Thành công {file_path.name} -> {out_file.name}")
                processed_count += 1
            else:
                logger.error(f"Parser không đọc được {file_path.name}")
                error_count += 1
                
        except ValidationError as ve:
            logger.error(f"Lỗi Validation ở {file_path.name}")
            write_json(conflict_dir / f"{file_path.name}_error.json", {"file": str(file_path), "error": ve.errors()})
            error_count += 1
        except Exception as e:
            logger.exception(f"Lỗi không xác định với {file_path.name}: {e}")
            error_count += 1
            
    logger.info(f"Hoàn tất M2B CTDT. Processed: {processed_count}, Skipped: {skipped_count}, Errors: {error_count}")

if __name__ == "__main__":
    ctdt_extract()
