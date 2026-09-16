import os
import sys
import json
import random
from pathlib import Path
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
api_keys = []
key = os.getenv("GEMINI_API_KEY")
if key: api_keys.append(key.strip("'\""))
for i in range(1, 10):
    key = os.getenv(f"GEMINI_API_KEY{i}")
    if key: api_keys.append(key.strip("'\""))

if not api_keys:
    print("No API keys found!")
    sys.exit(1)

current_key_idx = 0
def get_model():
    genai.configure(api_key=api_keys[current_key_idx])
    return genai.GenerativeModel('gemini-3.1-flash-lite', generation_config={"response_mime_type": "application/json"})

model = get_model()

def call_gemini_with_retry(prompt):
    global current_key_idx, model
    for _ in range(len(api_keys) * 2):
        try:
            return model.generate_content(prompt)
        except Exception as e:
            if "429" in str(e) or "ResourceExhausted" in str(e) or "503" in str(e):
                current_key_idx = (current_key_idx + 1) % len(api_keys)
                model = get_model()
            else:
                raise e
    raise Exception("All API keys exhausted")
CONTRACT_DIR = Path(__file__).resolve().parent.parent / "contract" / "hoc_phan"

def impute_missing_data():
    for course_dir in CONTRACT_DIR.iterdir():
        if not course_dir.is_dir():
            continue
        
        course_code = course_dir.name
        hoc_phan_file = course_dir / f"{course_code}__hoc_phan.json"
        bai_hoc_file = course_dir / f"{course_code}__bai_hoc.json"
        muc_tieu_file = course_dir / f"{course_code}__muc_tieu.json"
        clo_file = course_dir / f"{course_code}__clo.json"

        hoc_phan_data = {}
        # 1. Check and fix __hoc_phan.json
        if hoc_phan_file.exists():
            with open(hoc_phan_file, 'r', encoding='utf-8') as f:
                hoc_phan_data = json.load(f)
            
            if not hoc_phan_data.get("mo_ta_tom_tat"):
                print(f"[{course_code}] Missing mo_ta_tom_tat. Generating...", flush=True)
                course_name = hoc_phan_data.get("ten_vi", course_code)
                prompt = f"""
                Bạn là chuyên gia giáo dục đại học. Hãy viết một đoạn mô tả tóm tắt (khoảng 3-4 câu) cho môn học mang tên "{course_name}".
                Trả về JSON định dạng: {{"mo_ta_tom_tat": "nội dung..."}}
                """
                response = call_gemini_with_retry(prompt)
                try:
                    res_json = json.loads(response.text)
                    hoc_phan_data["mo_ta_tom_tat"] = res_json.get("mo_ta_tom_tat", "")
                    with open(hoc_phan_file, 'w', encoding='utf-8') as f:
                        json.dump(hoc_phan_data, f, ensure_ascii=False, indent=2)
                except Exception as e:
                    print(f"[{course_code}] Failed to generate mo_ta_tom_tat: {e}", flush=True)

        # 2. Check and fix __bai_hoc.json
        if bai_hoc_file.exists():
            with open(bai_hoc_file, 'r', encoding='utf-8') as f:
                bai_hoc_data = json.load(f)
            
            records = bai_hoc_data.get("records", [])
            
            lessons_to_fix = []
            for idx, bh in enumerate(records):
                if not bh.get("noi_dung_tom_tat") or not bh.get("ma_clo"):
                    lessons_to_fix.append((idx, bh))
            
            if lessons_to_fix:
                print(f"[{course_code}] Fixing {len(lessons_to_fix)} lessons with missing content/CLO...", flush=True)
                course_name = hoc_phan_data.get("ten_vi", course_code) if hoc_phan_file.exists() else course_code
                
                # split into batches of 15 to avoid massive prompts
                batch_size = 15
                for i in range(0, len(lessons_to_fix), batch_size):
                    batch = lessons_to_fix[i:i+batch_size]
                    batch_info = [{"id": idx, "ten_bai": bh.get("ten_bai")} for idx, bh in batch]
                    prompt = f"""
                    Bạn là giảng viên thiết kế bài giảng môn "{course_name}". Dưới đây là danh sách bài học bị thiếu mô tả nội dung.
                    Hãy viết cho mỗi bài học 1 đoạn nội dung tóm tắt (2-3 câu). 
                    Đồng thời chọn ngẫu nhiên 1-2 mã CLO hợp lý (trong các mã: L1, L2, L3, L4).
                    
                    Đầu vào:
                    {json.dumps(batch_info, ensure_ascii=False)}
                    
                    Trả về JSON array chứa kết quả (phải giữ nguyên id gốc):
                    [
                        {{"id": 0, "noi_dung_tom_tat": "nội dung...", "ma_clo": ["L1", "L2"]}},
                        ...
                    ]
                    """
                    try:
                        response = call_gemini_with_retry(prompt)
                        res_array = json.loads(response.text)
                        for item in res_array:
                            idx = item["id"]
                            # Also ensure the item isn't somehow out of bounds
                            if idx < len(records):
                                if not records[idx].get("noi_dung_tom_tat"):
                                    records[idx]["noi_dung_tom_tat"] = item.get("noi_dung_tom_tat", "")
                                if not records[idx].get("ma_clo"):
                                    records[idx]["ma_clo"] = item.get("ma_clo", ["L1"])
                                    if not isinstance(records[idx]["ma_clo"], list):
                                        records[idx]["ma_clo"] = [records[idx]["ma_clo"]]
                        
                        bai_hoc_data["records"] = records
                        with open(bai_hoc_file, 'w', encoding='utf-8') as f:
                            json.dump(bai_hoc_data, f, ensure_ascii=False, indent=2)
                    except Exception as e:
                        print(f"[{course_code}] Failed to generate bai_hoc data: {e}", flush=True)

        # 3. Check and fix __muc_tieu.json and __clo.json
        mt_records = []
        if muc_tieu_file.exists():
            with open(muc_tieu_file, 'r', encoding='utf-8') as f:
                mt_data = json.load(f)
                mt_records = mt_data.get("records", [])
        
        clo_records = []
        if clo_file.exists():
            with open(clo_file, 'r', encoding='utf-8') as f:
                clo_data = json.load(f)
                clo_records = clo_data.get("records", [])
                
        if not mt_records or not clo_records:
            print(f"[{course_code}] Missing muc_tieu or clo. Generating...", flush=True)
            course_name = hoc_phan_data.get("ten_vi", course_code) if hoc_phan_file.exists() else course_code
            prompt = f"""
            Bạn là giảng viên thiết kế môn học "{course_name}".
            Hãy sinh ra:
            1. Danh sách 3 Mục tiêu môn học: 1 Kiến thức, 1 Kỹ năng, 1 Tự chủ trách nhiệm.
            2. Danh sách 4 Chuẩn đầu ra (CLO) tương ứng.
            
            Trả về JSON:
            {{
                "muc_tieu": [
                    {{"ma_muc_tieu": "G1", "loai_muc_tieu": "KIEN_THUC", "noi_dung": "...", "so_ctdt": []}},
                    {{"ma_muc_tieu": "G2", "loai_muc_tieu": "KY_NANG", "noi_dung": "...", "so_ctdt": []}},
                    {{"ma_muc_tieu": "G3", "loai_muc_tieu": "TU_CHU_TRACH_NHIEM", "noi_dung": "...", "so_ctdt": []}}
                ],
                "clo": [
                    {{"ma_cdr_goc": "L1", "noi_dung": "...", "pi_so": [], "muc_do": "T"}},
                    {{"ma_cdr_goc": "L2", "noi_dung": "...", "pi_so": [], "muc_do": "T"}},
                    {{"ma_cdr_goc": "L3", "noi_dung": "...", "pi_so": [], "muc_do": "T"}},
                    {{"ma_cdr_goc": "L4", "noi_dung": "...", "pi_so": [], "muc_do": "T"}}
                ]
            }}
            """
            try:
                response = call_gemini_with_retry(prompt)
                res_json = json.loads(response.text)
                
                if not mt_records and res_json.get("muc_tieu"):
                    with open(muc_tieu_file, 'w', encoding='utf-8') as f:
                        json.dump({"records": res_json["muc_tieu"], "source_hash": ""}, f, ensure_ascii=False, indent=2)
                        
                if not clo_records and res_json.get("clo"):
                    with open(clo_file, 'w', encoding='utf-8') as f:
                        json.dump({"records": res_json["clo"], "source_hash": ""}, f, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"[{course_code}] Failed to generate muc_tieu/clo: {e}", flush=True)

if __name__ == "__main__":
    impute_missing_data()
    print("Done imputation.")
