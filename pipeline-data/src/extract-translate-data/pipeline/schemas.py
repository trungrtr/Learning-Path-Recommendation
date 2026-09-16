"""
Toàn bộ Pydantic model của pipeline, gộp một file (thay vì tách theo module)
vì các schema tham chiếu chéo nhau nhiều (SkillEvidence dùng lại field của
CourseL2, SkillMatch kế thừa provenance của SkillEvidence...).

Xem AGENT.md mục 4 (Provenance) trước khi thêm field mới cho các model
liên quan tới skill edge.
"""

from pydantic import BaseModel, Field
from typing import Literal


# ---------- Luồng A: Đề cương học phần ----------


class HocPhanDeCuong(BaseModel):
    ma_hoc_phan: str | None = None
    ma_in: str | None = None
    ten_vi: str | None = None
    ten_en: str | None = None
    so_tin_chi_tong: float | None = None
    mo_ta_tom_tat: str | None = None


class MucTieuHocPhan(BaseModel):
    ma_muc_tieu: str | None = None
    loai_muc_tieu: Literal["KIEN_THUC", "KY_NANG", "TU_CHU_TRACH_NHIEM"] | None = None
    noi_dung: str
    so_ctdt: list[str] = Field(default_factory=list)


class Clo(BaseModel):
    ma_cdr_goc: str | None = None
    noi_dung: str
    pi_so: list[str] = Field(default_factory=list)
    muc_do: str | None = None


class BaiHoc(BaseModel):
    so_thu_tu: str | None = None
    ten_bai: str
    noi_dung_tom_tat: str | None = None
    gio_truc_tiep: float | None = None
    gio_truc_tuyen: float | None = None
    gio_tu_hoc: float | None = None
    hinh_thuc_day_hoc: list[str] = Field(default_factory=list)
    ma_clo: list[str] = Field(default_factory=list)


class SyllabusL1(BaseModel):
    """SD_{ma_hoc_phan}_{seq}.json — output M2 layer 1, mỗi file MD một bản ghi."""
    ma_hoc_phan: str
    hoc_phan: HocPhanDeCuong
    muc_tieu_hoc_phan: list[MucTieuHocPhan] | None = None
    clo: list[Clo] | None = None
    bai_hoc: list[BaiHoc] | None = None
    field_provenance: dict[str, Literal["extracted", "reference_copied", "llm_inferred"]] = Field(default_factory=dict)


class SyllabusL2(BaseModel):
    """COURSE_{ma_hoc_phan}.json — output M2 layer 2, canonical merge từ nhiều L1."""
    ma_hoc_phan: str
    crawl_course_key: str
    content_hash: str
    hoc_phan: HocPhanDeCuong
    muc_tieu_hoc_phan: list[MucTieuHocPhan] | None = None
    clo: list[Clo] | None = None
    bai_hoc: list[BaiHoc] | None = None
    field_provenance: dict[str, Literal["extracted", "reference_copied", "llm_inferred"]] = Field(default_factory=dict)


# ---------- Luồng B: CTDT ----------

class QuanHeHocPhan(BaseModel):
    loai: Literal["TIEN_QUYET", "HOC_TRUOC"]
    ma_hoc_phan: str | None = None
    ten_hoc_phan: str | None = None


class HocPhanCtdt(BaseModel):
    ma_hoc_phan: str | None = None
    ten_hoc_phan: str | None = None
    so_tin_chi_tong: float | None = None
    hoc_ky_goi_y: int | None = None
    quan_he: list[QuanHeHocPhan] | None = None


class NhomHocPhan(BaseModel):
    ten_nhom: str | None = None
    loai_nhom: Literal["BAT_BUOC", "TU_CHON"] | None = None
    so_tin_chi_yeu_cau: float | None = None
    hoc_phan: list[HocPhanCtdt] | None = None


class ChuongTrinhDaoTao(BaseModel):
    ma_ctdt: str | None = None
    ten_ctdt: str | None = None
    bac_dao_tao: str | None = None
    phien_ban: str | None = None


class CtdtSchema(BaseModel):
    """CTDT_{ma_ctdt}.json — output M2B, trực tiếp."""
    ma_ctdt: str
    crawl_course_key: str
    chuong_trinh_dao_tao: ChuongTrinhDaoTao
    nhom_hoc_phan: list[NhomHocPhan] | None = None



