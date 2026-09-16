import json
import csv
from pathlib import Path

def extract_missing_courses():
    CTDT_DIR = Path(r"d:\NCKH_2026\src\pipeline-data\contract\ctdt")
    HOCPHAN_DIR = Path(r"d:\NCKH_2026\src\pipeline-data\contract\hoc_phan")
    OUT_DIR = Path(r"d:\NCKH_2026\src\pipeline-data\data_missing")

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    missing_hp = {}
    nhom_hp = {}
    has_course = []
    belongs_to = []

    for ctdt_folder in CTDT_DIR.iterdir():
        if not ctdt_folder.is_dir(): continue
        for json_file in ctdt_folder.glob("CTDT_*.json"):
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            ma_ctdt = data.get("ma_ctdt")
            if not ma_ctdt: continue
            
            for course in data.get("courses", []):
                ma_hp_raw = course.get("ma_hoc_phan")
                if not ma_hp_raw: continue
                
                # Check if the course directory exists in hoc_phan
                hp_json = HOCPHAN_DIR / ma_hp_raw / f"{ma_hp_raw}__hoc_phan.json"
                if hp_json.exists():
                    continue
                    
                # It's missing
                ma_hp_clean = ma_hp_raw[:-3] if ma_hp_raw.endswith("_BS") else ma_hp_raw
                
                # extract info from memberships
                mems = course.get("memberships", [])
                if mems:
                    mem = mems[0]
                    if ma_hp_clean not in missing_hp:
                        missing_hp[ma_hp_clean] = {
                            "ma_hoc_phan": ma_hp_clean,
                            "ten_vi": mem.get("ten_hoc_phan", ""),
                            "ten_en": mem.get("ten_hoc_phan_en", ""),
                            "so_tin_chi_tong": mem.get("so_tin_chi", 0.0),
                            "hoc_ky_goi_y": mem.get("hoc_ky_goi_y", ""),
                            "loai_hoc_phan": mem.get("loai_nhom", "")
                        }
                    
                    # Relations
                    has_course.append({"source_id": ma_ctdt, "target_id": ma_hp_clean, "type": "HAS_COURSE"})
                    
                    for m in mems:
                        nhom_id = f"{ma_ctdt}_{m.get('nhom_id', '')}"
                        if nhom_id not in nhom_hp:
                            nhom_hp[nhom_id] = {
                                "group_id": nhom_id,
                                "ten_nhom_vi": m.get("nhom_id", ""),
                                "ten_nhom_en": m.get("nhom_id_en", ""),
                                "loai_nhom": m.get("loai_nhom", "")
                            }
                        # Add relationship only if not duplicate
                        rel = {"source_id": ma_hp_clean, "target_id": nhom_id, "type": "BELONGS_TO"}
                        if rel not in belongs_to:
                            belongs_to.append(rel)

    # Write CSVs
    def write_csv(filename, fieldnames, data_list):
        with open(OUT_DIR / filename, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data_list)

    write_csv("Missing_HocPhan.csv", ["ma_hoc_phan", "ten_vi", "ten_en", "so_tin_chi_tong", "hoc_ky_goi_y", "loai_hoc_phan"], list(missing_hp.values()))
    write_csv("Missing_NhomHocPhan.csv", ["group_id", "ten_nhom_vi", "ten_nhom_en", "loai_nhom"], list(nhom_hp.values()))
    write_csv("Missing_rel_HAS_COURSE.csv", ["source_id", "target_id", "type"], has_course)
    write_csv("Missing_rel_BELONGS_TO.csv", ["source_id", "target_id", "type"], belongs_to)

    print(f"Extracted {len(missing_hp)} missing courses.")
    print(f"Extracted {len(nhom_hp)} groups related to missing courses.")
    print(f"Extracted {len(has_course)} HAS_COURSE relationships.")
    print(f"Extracted {len(belongs_to)} BELONGS_TO relationships.")
    print(f"Output saved to: {OUT_DIR}")

if __name__ == "__main__":
    extract_missing_courses()
