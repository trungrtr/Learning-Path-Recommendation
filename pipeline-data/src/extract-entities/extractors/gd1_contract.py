import json
import logging
from pathlib import Path
from typing import Dict, List, Any
from core.models import (
    ChuongTrinhDaoTaoNode, NhomHocPhanNode, HocPhanNode, 
    MucTieuHocPhanNode, CLONode, BaiNode, Relationship
)
from .base import BaseExtractor
from core.config import CONTRACT_CTDT_DIR, CONTRACT_HOCPHAN_DIR

logger = logging.getLogger(__name__)

def _get_records(file_path: Path) -> List[dict]:
    try:
        data = json.loads(file_path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data.get("records", [])
        elif isinstance(data, list):
            return data
    except Exception:
        pass
    return []

class GD1ContractExtractor(BaseExtractor):
    def __init__(self):
        self.nodes = {
            "ChuongTrinhDaoTao": [],
            "NhomHocPhan": [],
            "HocPhan": [],
            "MucTieuHocPhan": [],
            "CLO": [],
            "Bai": []
        }
        self.relationships = {
            "HAS_COURSE": [],
            "BELONGS_TO": [],
            "HAS_CLO": [],
            "HAS_OBJECTIVE": [],
            "HAS_LESSON": [],
            "SUPPORTS_CLO": [],
            "PREREQUISITE": [],
            "PREVIOUS_COURSE": []
        }
        self.fallback_hoc_phan = {}
        
    def extract_nodes(self) -> Dict[str, List[Any]]:
        return self.nodes

    def extract_relationships(self) -> Dict[str, List[Relationship]]:
        return self.relationships

    def run(self):
        self._parse_ctdt()
        self._parse_hoc_phan()

    def _parse_ctdt(self):
        if not CONTRACT_CTDT_DIR.exists():
            logger.warning(f"Dir not found: {CONTRACT_CTDT_DIR}")
            return
            
        nhom_set = set() # Avoid duplicates
        for ctdt_dir in CONTRACT_CTDT_DIR.iterdir():
            if not ctdt_dir.is_dir():
                continue
            for json_file in ctdt_dir.glob("CTDT_*.json"):
                data = json.loads(json_file.read_text(encoding="utf-8"))
                prog = data.get("program", {})
                ma_ctdt = prog.get("ma_ctdt")
                if not ma_ctdt:
                    continue
                    
                # Node CTDT
                self.nodes["ChuongTrinhDaoTao"].append(
                    ChuongTrinhDaoTaoNode(
                        ma_ctdt=ma_ctdt,
                        ten_ctdt=prog.get("ten_ctdt", ""),
                        bac_dao_tao=prog.get("bac_dao_tao", ""),
                        phien_ban=prog.get("phien_ban", "")
                    )
                )
                
                # NhomHocPhan and CTDT courses
                for course in data.get("courses", []):
                    ma_hp = course.get("ma_hoc_phan")
                    if not ma_hp:
                        continue
                    if ma_hp.endswith("_BS"):
                        ma_hp = ma_hp[:-3]
                        
                    # Save fallback info for HocPhan if missing from hoc_phan dir
                    mems = course.get("memberships", [])
                    if mems:
                        mem = mems[0]
                        if ma_hp not in self.fallback_hoc_phan:
                            self.fallback_hoc_phan[ma_hp] = {
                                "ten_vi": mem.get("ten_hoc_phan", ""),
                                "ten_en": mem.get("ten_hoc_phan_en", ""),
                                "so_tin_chi_tong": mem.get("so_tin_chi", 0.0),
                                "hoc_ky_goi_y": mem.get("hoc_ky_goi_y", ""),
                                "loai_hoc_phan": mem.get("loai_nhom", "")
                            }
                        
                    # (ChuongTrinhDaoTao)-[:HAS_COURSE]->(HocPhan)
                    self.relationships["HAS_COURSE"].append(
                        Relationship(source_id=ma_ctdt, target_id=ma_hp, type="HAS_COURSE")
                    )
                    
                    for mem in course.get("memberships", []):
                        nhom_id = f"{ma_ctdt}_{mem.get('nhom_id', '')}"
                        if nhom_id not in nhom_set:
                            nhom_set.add(nhom_id)
                            self.nodes["NhomHocPhan"].append(
                                NhomHocPhanNode(
                                    group_id=nhom_id,
                                    ten_nhom_vi=mem.get("nhom_id", ""), 
                                    ten_nhom_en=mem.get("nhom_id_en", ""),
                                    loai_nhom=mem.get("loai_nhom", "")
                                )
                            )
                        # (HocPhan)-[:BELONGS_TO]->(NhomHocPhan)
                        self.relationships["BELONGS_TO"].append(
                            Relationship(source_id=ma_hp, target_id=nhom_id, type="BELONGS_TO")
                        )

    def _parse_hoc_phan(self):
        if not CONTRACT_HOCPHAN_DIR.exists():
            logger.warning(f"Dir not found: {CONTRACT_HOCPHAN_DIR}")
            return
            
        for hp_dir in CONTRACT_HOCPHAN_DIR.iterdir():
            if not hp_dir.is_dir():
                continue
            hp_dir_name = hp_dir.name
            ma_hp = hp_dir_name[:-3] if hp_dir_name.endswith("_BS") else hp_dir_name
            
            # 1. HocPhan
            hp_file = hp_dir / f"{hp_dir_name}__hoc_phan.json"
            if hp_file.exists():
                hp_data = json.loads(hp_file.read_text(encoding="utf-8"))
                
                so_tin_chi_tong = float(hp_data.get("so_tin_chi_tong") or 0.0)
                hoc_ky_goi_y = str(hp_data.get("hoc_ky_goi_y", hp_data.get("hoc_ky_du_kien", "")))
                loai_hoc_phan = str(hp_data.get("loai_hoc_phan", ""))
                
                memberships = hp_data.get("ctdt_memberships", [])
                if memberships and isinstance(memberships, list):
                    if so_tin_chi_tong == 0.0:
                        so_tin_chi_tong = float(memberships[0].get("so_tin_chi", 0.0))
                    if not hoc_ky_goi_y:
                        hoc_ky_goi_y = str(memberships[0].get("hoc_ky_goi_y", ""))
                    if not loai_hoc_phan:
                        loai_hoc_phan = str(memberships[0].get("loai_nhom", ""))
                        
                self.nodes["HocPhan"].append(
                    HocPhanNode(
                        ma_hoc_phan=ma_hp,
                        ten_vi=hp_data.get("ten_vi", ""),
                        ten_en=hp_data.get("ten_en", "") or hp_data.get("ten_vi_en", ""),
                        so_tin_chi_tong=so_tin_chi_tong,
                        mo_ta_tom_tat_vi=hp_data.get("mo_ta_tom_tat", ""),
                        mo_ta_tom_tat_en=hp_data.get("mo_ta_tom_tat_en", ""),
                        hoc_ky_goi_y=hoc_ky_goi_y,
                        loai_hoc_phan=loai_hoc_phan
                    )
                )
                
                # Tien quyet, hoc truoc
                for tq in hp_data.get("dieu_kien_tien_quyet", []):
                    if tq.endswith("_BS"): tq = tq[:-3]
                    self.relationships["PREREQUISITE"].append(
                        Relationship(source_id=ma_hp, target_id=tq, type="PREREQUISITE", properties={"is_explicitly_empty": "false", "source": "extract"})
                    )
                for ht in hp_data.get("dieu_kien_hoc_truoc", []):
                    if ht.endswith("_BS"): ht = ht[:-3]
                    self.relationships["PREVIOUS_COURSE"].append(
                        Relationship(source_id=ma_hp, target_id=ht, type="PREVIOUS_COURSE", properties={"is_explicitly_empty": "false", "source": "extract"})
                    )

            # 2. MucTieu
            mt_file = hp_dir / f"{hp_dir_name}__muc_tieu.json"
            if mt_file.exists():
                mt_list = _get_records(mt_file)
                for mt in mt_list:
                    ma_mt = mt.get("ma_muc_tieu", "")
                    if not ma_mt: continue
                    mt_id = f"{ma_hp}_{ma_mt}"
                    
                    noi_dung_vi = mt.get("noi_dung", "")
                    noi_dung_en = mt.get("noi_dung_en", "")
                        
                    self.nodes["MucTieuHocPhan"].append(
                        MucTieuHocPhanNode(
                            mucTieu_id=mt_id,
                            loai_muc_tieu=mt.get("loai_muc_tieu", ""),
                            ma_muc_tieu=ma_mt,
                            noi_dung_vi=noi_dung_vi,
                            noi_dung_en=noi_dung_en
                        )
                    )
                    self.relationships["HAS_OBJECTIVE"].append(
                        Relationship(source_id=ma_hp, target_id=mt_id, type="HAS_OBJECTIVE")
                    )

            # 3. CLO
            clo_file = hp_dir / f"{hp_dir_name}__clo.json"
            if clo_file.exists():
                clo_list = _get_records(clo_file)
                for clo in clo_list:
                    ma_clo = clo.get("ma_cdr_goc", "") or clo.get("ma_clo", "")
                    if not ma_clo: continue
                    clo_id = f"{ma_hp}_{ma_clo}"
                    muc_do_val = clo.get("muc_do")
                    if isinstance(muc_do_val, str):
                        muc_do_val = [muc_do_val]
                    elif not muc_do_val:
                        muc_do_val = []

                    self.nodes["CLO"].append(
                        CLONode(
                            clo_id=clo_id,
                            ma_cdr_goc=ma_clo,
                            noi_dung_vi=clo.get("noi_dung", ""),
                            noi_dung_en=clo.get("noi_dung_en", ""),
                            pi_so=clo.get("pi_so") or clo.get("chuan_da_ra_ctdt", []),
                            muc_do=muc_do_val
                        )
                    )
                    self.relationships["HAS_CLO"].append(
                        Relationship(source_id=ma_hp, target_id=clo_id, type="HAS_CLO")
                    )

            # 4. Bai
            bai_file = hp_dir / f"{hp_dir_name}__bai_hoc.json"
            if bai_file.exists():
                bai_list = _get_records(bai_file)
                for idx, bai in enumerate(bai_list):
                    so_thu_tu = bai.get("so_thu_tu") or (idx + 1)
                    lesson_id = f"{ma_hp}_L{so_thu_tu}"
                    self.nodes["Bai"].append(
                        BaiNode(
                            lesson_id=lesson_id,
                            so_thu_tu=int(so_thu_tu),
                            ten_bai_vi=bai.get("ten_bai", ""),
                            ten_bai_en=bai.get("ten_bai_en", ""),
                            noi_dung_tom_tat_vi=bai.get("noi_dung", "") or bai.get("noi_dung_tom_tat", ""),
                            noi_dung_tom_tat_en=bai.get("noi_dung_en", "") or bai.get("noi_dung_tom_tat_en", "")
                        )
                    )
                    self.relationships["HAS_LESSON"].append(
                        Relationship(source_id=ma_hp, target_id=lesson_id, type="HAS_LESSON")
                    )
                    for clo in bai.get("dap_ung_cdr", []):
                        clo_id = f"{ma_hp}_{clo}"
                        self.relationships["SUPPORTS_CLO"].append(
                            Relationship(source_id=lesson_id, target_id=clo_id, type="SUPPORTS_CLO")
                        )

        # Inject missing courses using fallback data
        extracted_ma_hp = {hp.ma_hoc_phan for hp in self.nodes["HocPhan"]}
        for ma_hp, info in self.fallback_hoc_phan.items():
            if ma_hp not in extracted_ma_hp:
                self.nodes["HocPhan"].append(
                    HocPhanNode(
                        ma_hoc_phan=ma_hp,
                        ten_vi=info.get("ten_vi", ""),
                        ten_en=info.get("ten_en", ""),
                        so_tin_chi_tong=float(info.get("so_tin_chi_tong") or 0.0),
                        mo_ta_tom_tat_vi="",
                        mo_ta_tom_tat_en="",
                        hoc_ky_goi_y=str(info.get("hoc_ky_goi_y", "")),
                        loai_hoc_phan=str(info.get("loai_hoc_phan", ""))
                    )
                )
