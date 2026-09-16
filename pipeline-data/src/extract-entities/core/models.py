from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class ChuongTrinhDaoTaoNode:
    ma_ctdt: str
    ten_ctdt: str
    bac_dao_tao: str
    phien_ban: str

@dataclass
class NhomHocPhanNode:
    group_id: str
    ten_nhom_vi: str
    ten_nhom_en: str
    loai_nhom: str

@dataclass
class HocPhanNode:
    ma_hoc_phan: str
    ten_vi: str
    ten_en: str
    so_tin_chi_tong: float
    mo_ta_tom_tat_vi: str
    mo_ta_tom_tat_en: str
    hoc_ky_goi_y: str
    loai_hoc_phan: str

@dataclass
class MucTieuHocPhanNode:
    mucTieu_id: str
    loai_muc_tieu: str
    ma_muc_tieu: str
    noi_dung_vi: str
    noi_dung_en: str

@dataclass
class CLONode:
    clo_id: str
    ma_cdr_goc: str
    noi_dung_vi: str
    noi_dung_en: str
    pi_so: List[str]
    muc_do: List[str]

@dataclass
class BaiNode:
    lesson_id: str
    so_thu_tu: int
    ten_bai_vi: str
    ten_bai_en: str
    noi_dung_tom_tat_vi: str
    noi_dung_tom_tat_en: str

@dataclass
class KyNangESCONode:
    skill_uri: str
    concept_type: str
    skill_type: str
    reuse_level: str
    preferred_label: str
    alternative_labels: List[str]
    hidden_labels: List[str]
    status: str
    modified_date: str
    scope_note: str
    definition: str
    in_scheme: List[str]
    description: str
    uniskill_domain: str
    domain_reason: str

@dataclass
class ConceptTagNode:
    normalized: str
    text: str
    loai: str

@dataclass
class NgheNghiepESCONode:
    occupation_uri: str
    preferred_label: str
    alternative_labels: List[str]
    description: str
    scope_note: str = ""
    hidden_labels: List[str] = field(default_factory=list)

@dataclass
class Relationship:
    source_id: str
    target_id: str
    type: str
    properties: dict = field(default_factory=dict)
