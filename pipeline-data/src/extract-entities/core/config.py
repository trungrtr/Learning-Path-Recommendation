import os
from pathlib import Path

# Thư mục gốc của project pipeline-data
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

# ── INPUT PATHS ──────────────────────────────────────────────────────────────
# 1. Contract data (GĐ1)
CONTRACT_DIR = BASE_DIR / "contract"
CONTRACT_CTDT_DIR = CONTRACT_DIR / "ctdt"
CONTRACT_HOCPHAN_DIR = CONTRACT_DIR / "hoc_phan"

# 2. ESCO data (GĐ2)
ESCO_ZIP_PATH = BASE_DIR / "raw" / "ESCO dataset - v1.2.1 - classification - en - csv.zip"
# File skills và roles đã xử lý trong esco_data
ESCO_SKILLS_CSV = BASE_DIR / "esco_data" / "skills.csv"
ESCO_ROLES_CSV = BASE_DIR / "esco_data" / "roles_mapped.csv" 

# 3. Mappings (GĐ3)
M4_DIR = BASE_DIR / "src" / "esco-skill-mapping" / "data" / "data_teaches_B"
M5_DIR = BASE_DIR / "src" / "esco-skill-mapping" / "data" / "data_support_skill"
ESCO_META_PATH = BASE_DIR / "src" / "esco-skill-mapping" / "data" / "esco_filtered" / "v1" / "faiss" / "esco_metadata.json"

# ── OUTPUT PATHS ─────────────────────────────────────────────────────────────
CSV_OUTPUT_DIR = BASE_DIR / "final_kg_export"

# ── NEO4J CONFIGS ────────────────────────────────────────────────────────────
ARRAY_SEP = ";" # Ký tự phân cách cho mảng (vd: pi_so)
