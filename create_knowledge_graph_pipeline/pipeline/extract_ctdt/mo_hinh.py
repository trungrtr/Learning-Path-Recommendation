"""Pydantic contract for ``ctdt_schema_min.json``."""

from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, field_validator, model_validator


def _clean_text(value: Any) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        return str(value).strip()
    return value.strip()


def _clean_optional_text(value: Any) -> Any:
    if value is None:
        return None
    if not isinstance(value, str):
        value = str(value)
    cleaned = value.strip()
    return cleaned or None


Text = Annotated[str, BeforeValidator(_clean_text)]
OptionalText = Annotated[str | None, BeforeValidator(_clean_optional_text)]


class _CtdtModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class NhomMon(_CtdtModel):
    nhom_id: Text = ""
    ten_nhom: Text = ""
    nhom_cha_id: OptionalText = None
    loai_nhom: Literal["bat_buoc", "tu_chon", "nhom_tong", ""] = ""
    so_tin_chi_yeu_cau: float = 0

    @model_validator(mode="before")
    @classmethod
    def _migrate_legacy_credit_field(cls, value: Any) -> Any:
        if isinstance(value, dict) and "tong_so_tin" in value and "so_tin_chi_yeu_cau" not in value:
            value = dict(value)
            value["so_tin_chi_yeu_cau"] = value.pop("tong_so_tin")
        return value

    @property
    def tong_so_tin(self) -> float:
        return self.so_tin_chi_yeu_cau


class HocPhanCtdt(_CtdtModel):
    ma_hp: Text = ""
    nhom_id: Text = ""
    hoc_ky: int | None = None
    tien_quyet: list[str] = Field(default_factory=list)
    hoc_truoc: list[str] = Field(default_factory=list)

    @field_validator("tien_quyet", "hoc_truoc", mode="before")
    @classmethod
    def _coerce_course_code_list(cls, value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            value = [value]
        if not isinstance(value, list):
            return []
        result: list[str] = []
        seen: set[str] = set()
        for item in value:
            cleaned = _clean_text(item)
            key = cleaned.casefold()
            if cleaned and key not in seen:
                result.append(cleaned)
                seen.add(key)
        return result


class CtdtDocument(_CtdtModel):
    schema_version: Literal["1.0", "1.1", "1.2"] = "1.2"
    stage: Literal["ctdt_llm_extraction"] = "ctdt_llm_extraction"
    ma_ctdt: Text = ""
    ten_nganh: Text = ""
    tong_so_tin_chi: float = 0
    nhom_mon: list[NhomMon] = Field(default_factory=list)
    hoc_phan: list[HocPhanCtdt] = Field(default_factory=list)
