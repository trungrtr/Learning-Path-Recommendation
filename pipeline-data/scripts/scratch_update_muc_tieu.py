import json
import os
import sys
from pathlib import Path

# Add src to path so we can import from shared
src_dir = Path(__file__).resolve().parent.parent / "src" / "extract-translate-data"
sys.path.append(str(src_dir))

from shared.llm_client import call_gemini



def process():
    base_dir = Path(__file__).resolve().parent.parent / "contract" / "hoc_phan"
    for hp_dir in base_dir.iterdir():
        if not hp_dir.is_dir() or "_BS" not in hp_dir.name:
            continue
            
        hoc_phan_file = hp_dir / f"{hp_dir.name}__hoc_phan.json"
        muc_tieu_file = hp_dir / f"{hp_dir.name}__muc_tieu.json"
        
        if not hoc_phan_file.exists() or not muc_tieu_file.exists():
            continue
            
        with open(hoc_phan_file, 'r', encoding='utf-8') as f:
            hp_data = json.load(f)
            
        with open(muc_tieu_file, 'r', encoding='utf-8') as f:
            mt_data = json.load(f)
            
        # Check if it's already properly split
        if len(mt_data) == 3 and all(m.get('loai_muc_tieu') for m in mt_data):
            print(f"Skipping {hp_dir.name}, already 3 objectives.")
            continue
            
        print(f"Processing {hp_dir.name}...")
        
        ma_hp = hp_data.get("ma_hoc_phan", "")
        ten = hp_data.get("ten_vi", "")
        mo_ta = hp_data.get("mo_ta_tom_tat", "")
        
        prompt = f"""
Dưới đây là thông tin của một học phần:
Mã học phần: {ma_hp}
Tên học phần (VN): {ten}
Mô tả tóm tắt: {mo_ta}

Nhiệm vụ của bạn là dựa vào mô tả tóm tắt này, hãy sinh ra phần MỤC TIÊU HỌC PHẦN gồm 3 loại:
1. Kiến thức (KIEN_THUC) - G1
2. Kỹ năng (KY_NANG) - G2
3. Thái độ / Tự chủ chịu trách nhiệm (TU_CHU_TRACH_NHIEM) - G3

Yêu cầu output: 
Chỉ xuất ra ĐÚNG định dạng JSON array sau, không kèm bất kỳ giải thích nào, không dùng markdown block code:
[
  {{
    "ma_muc_tieu": "G1",
    "loai_muc_tieu": "KIEN_THUC",
    "noi_dung": "...",
    "so_ctdt": [],
    "noi_dung_en": "..."
  }},
  {{
    "ma_muc_tieu": "G2",
    "loai_muc_tieu": "KY_NANG",
    "noi_dung": "...",
    "so_ctdt": [],
    "noi_dung_en": "..."
  }},
  {{
    "ma_muc_tieu": "G3",
    "loai_muc_tieu": "TU_CHU_TRACH_NHIEM",
    "noi_dung": "...",
    "so_ctdt": [],
    "noi_dung_en": "..."
  }}
]

Nhớ dịch nội dung sang tiếng Anh cho trường "noi_dung_en".
"""
        
        try:
            # Using standard flash model
            response = call_gemini(prompt, model="gemini-3.6-flash")
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.endswith("```"):
                response = response[:-3]
            response = response.strip()
            
            new_mt_data = json.loads(response)
            
            # Keep the source hash from the first item
            source_hash = mt_data[0].get("source_hash") if mt_data and isinstance(mt_data, list) else None
            
            for item in new_mt_data:
                if source_hash:
                    item["source_hash"] = source_hash
            
            with open(muc_tieu_file, 'w', encoding='utf-8') as f:
                json.dump(new_mt_data, f, ensure_ascii=False, indent=2)
                
            print(f"Successfully updated {hp_dir.name}")
        except Exception as e:
            print(f"Error processing {hp_dir.name}: {e}")

if __name__ == "__main__":
    process()
