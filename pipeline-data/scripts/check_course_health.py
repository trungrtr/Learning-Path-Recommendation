import json
from pathlib import Path
import csv

def check_courses_health():
    CONTRACT_DIR = Path(__file__).resolve().parent.parent / "contract" / "hoc_phan"
    
    report = []
    
    for course_dir in CONTRACT_DIR.iterdir():
        if not course_dir.is_dir():
            continue
            
        ma_hp = course_dir.name
        
        errors = []
        
        # Check __hoc_phan.json
        hp_file = course_dir / f"{ma_hp}__hoc_phan.json"
        if not hp_file.exists():
            errors.append("Thiếu file __hoc_phan.json")
        else:
            with open(hp_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                mo_ta = data.get("mo_ta_tom_tat")
                if not mo_ta:
                    errors.append("Thiếu mo_ta_tom_tat trong __hoc_phan.json")
                    
        # Check __muc_tieu.json
        mt_file = course_dir / f"{ma_hp}__muc_tieu.json"
        if not mt_file.exists():
            errors.append("Thiếu file __muc_tieu.json")
        else:
            with open(mt_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                records = data.get("records", []) if isinstance(data, dict) else data
                if not records:
                    errors.append("__muc_tieu.json rỗng")
                    
        # Check __clo.json
        clo_file = course_dir / f"{ma_hp}__clo.json"
        if not clo_file.exists():
            errors.append("Thiếu file __clo.json")
        else:
            with open(clo_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                records = data.get("records", []) if isinstance(data, dict) else data
                if not records:
                    errors.append("__clo.json rỗng")
                    
        # Check __bai_hoc.json
        bai_file = course_dir / f"{ma_hp}__bai_hoc.json"
        if not bai_file.exists():
            errors.append("Thiếu file __bai_hoc.json")
        else:
            with open(bai_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                records = data.get("records", []) if isinstance(data, dict) else data
                if not records:
                    errors.append("__bai_hoc.json rỗng")
                else:
                    missing_noi_dung = 0
                    missing_clo = 0
                    for bai in records:
                        if not bai.get("noi_dung_tom_tat") and not bai.get("noi_dung"):
                            missing_noi_dung += 1
                        
                        dap_ung_cdr = bai.get("dap_ung_cdr") or bai.get("ma_clo")
                        if not dap_ung_cdr:
                            missing_clo += 1
                            
                    if missing_noi_dung > 0:
                        errors.append(f"Có {missing_noi_dung}/{len(records)} bài học thiếu nội dung tóm tắt")
                    if missing_clo > 0:
                        errors.append(f"Có {missing_clo}/{len(records)} bài học thiếu ánh xạ CLO (ma_clo rỗng)")
                        
        if errors:
            report.append({
                "ma_hoc_phan": ma_hp,
                "errors": "; ".join(errors)
            })
            
    with open('course_health_report.txt', 'w', encoding='utf-8') as f:
        f.write(f"Phát hiện {len(report)} học phần có lỗi/thiếu thông tin.\n")
        for r in report:
            f.write(f"[{r['ma_hoc_phan']}]: {r['errors']}\n")

if __name__ == '__main__':
    check_courses_health()
