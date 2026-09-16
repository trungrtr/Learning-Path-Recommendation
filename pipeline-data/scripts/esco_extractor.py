"""
esco_extractor.py
=================
Module trích xuất dữ liệu 30 nghề IT từ bộ ESCO v1.2.1.

Đầu vào:
  - ESCO_dataset_-_v1_2_1_-_classification_-_en_-_csv.zip   (ESCO gốc)
  - 30_roles_summary.csv                                      (danh sách 30 nghề)

Đầu ra (tuỳ hàm):
  - DataFrame / dict nghề, kỹ năng, quan hệ nghề-kỹ năng
  - File CSV / JSON xuất kết quả

Cách dùng nhanh:
  from esco_extractor import ESCOExtractor
  ex = ESCOExtractor("ESCO_...zip", "30_roles_summary.csv")
  ex.load()
  df_occ   = ex.get_occupations()
  df_skills = ex.get_skills()
  df_rel   = ex.get_relations()
  ex.export_all("output/")
"""

from __future__ import annotations

import json
import logging
import zipfile
from pathlib import Path
from typing import Optional

import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# ── Tên file bên trong ZIP ────────────────────────────────────────────────────
_F_OCC   = "occupations_en.csv"
_F_SK    = "skills_en.csv"
_F_REL   = "occupationSkillRelations_en.csv"

# ── Cột cần dùng ──────────────────────────────────────────────────────────────
_OCC_COLS = ["conceptUri", "code", "preferredLabel", "altLabels",
             "description", "definition", "iscoGroup"]
_SK_COLS  = ["conceptUri", "preferredLabel", "skillType",
             "reuseLevel", "description", "definition", "altLabels"]
_REL_COLS = ["occupationUri", "occupationLabel", "relationType",
             "skillType", "skillUri", "skillLabel"]


# ─────────────────────────────────────────────────────────────────────────────
class ESCOExtractor:
    """
    Trích xuất dữ liệu ESCO cho 30 nghề IT định sẵn.

    Parameters
    ----------
    esco_zip   : đường dẫn tới file ZIP ESCO v1.2.1
    roles_csv  : đường dẫn tới file 30_roles_summary.csv
    """

    def __init__(self, esco_zip: str, roles_csv: str) -> None:
        self.esco_zip  = Path(esco_zip)
        self.roles_csv = Path(roles_csv)

        # ── DataFrames nội bộ (sau khi load()) ───────────────────────────────
        self._roles: Optional[pd.DataFrame]     = None   # 30 roles gốc
        self._occ:   Optional[pd.DataFrame]     = None   # occupations đã lọc
        self._sk:    Optional[pd.DataFrame]     = None   # skills đã lọc
        self._rel:   Optional[pd.DataFrame]     = None   # relations đã lọc
        self._loaded: bool                      = False

    # ─────────────────────────────────────────────────────────────────────────
    # 1. LOAD
    # ─────────────────────────────────────────────────────────────────────────
    def load(self) -> "ESCOExtractor":
        """
        Đọc toàn bộ dữ liệu cần thiết vào bộ nhớ.
        Gọi hàm này trước bất kỳ hàm get_* nào.
        """
        log.info("Đọc danh sách 30 nghề từ %s", self.roles_csv)
        self._roles = self._read_roles()

        target_codes = self._get_target_codes()
        log.info("Tìm thấy %d mã ESCO duy nhất cần lọc", len(target_codes))

        log.info("Đọc occupations từ ZIP …")
        self._occ = self._read_occupations(target_codes)
        log.info("  → %d nghề khớp", len(self._occ))

        # URI của các nghề đã khớp → lọc relations
        occ_uris = set(self._occ["conceptUri"])

        log.info("Đọc occupationSkillRelations từ ZIP …")
        self._rel = self._read_relations(occ_uris)
        log.info("  → %d quan hệ (essential + optional)", len(self._rel))

        # URI kỹ năng xuất hiện trong relations → lọc skills
        skill_uris = set(self._rel["skillUri"])

        log.info("Đọc skills từ ZIP …")
        self._sk = self._read_skills(skill_uris)
        log.info("  → %d kỹ năng duy nhất", len(self._sk))

        self._loaded = True
        log.info("Load hoàn tất.")
        return self

    # ─────────────────────────────────────────────────────────────────────────
    # 2. GET – trả về DataFrame
    # ─────────────────────────────────────────────────────────────────────────
    def get_roles(self) -> pd.DataFrame:
        """
        DataFrame 30 nghề từ file roles_csv, kèm cột `matchedUri`
        (URI ESCO tương ứng, NaN nếu không tìm thấy).
        """
        self._check_loaded()
        uri_map = (
            self._occ
            .set_index("code")["conceptUri"]
            .to_dict()
        )
        df = self._roles.copy()
        df["matched_uri"] = df["ESCO Code"].astype(str).map(uri_map)
        df["matched_in_esco"] = df["matched_uri"].notna()
        return df

    def get_occupations(self) -> pd.DataFrame:
        """
        DataFrame các nghề ESCO đã lọc (25 nghề khớp mã).

        Cột:
          code | preferredLabel | altLabels | description | definition
          iscoGroup | conceptUri
          + job_title_vi  (tên tiếng Việt từ roles_csv)
          + job_title_en  (tên gốc trong roles_csv)
        """
        self._check_loaded()
        roles_map = (
            self._roles
            .drop_duplicates(subset="ESCO Code")
            .set_index("ESCO Code")
            [["Your Job Title", "Vietnamese"]]
            .rename(columns={"Your Job Title": "job_title_en",
                             "Vietnamese":     "job_title_vi"})
        )
        df = self._occ.copy()
        df = df.merge(roles_map, left_on="code", right_index=True, how="left")
        return df.reset_index(drop=True)

    def get_skills(self) -> pd.DataFrame:
        """
        DataFrame toàn bộ kỹ năng liên quan đến 30 nghề.

        Cột:
          conceptUri | preferredLabel | skillType | reuseLevel
          description | definition | altLabels
        """
        self._check_loaded()
        return self._sk.reset_index(drop=True)

    def get_relations(self) -> pd.DataFrame:
        """
        DataFrame quan hệ nghề ↔ kỹ năng.

        Cột:
          occupationUri | occupationLabel | relationType
          skillType | skillUri | skillLabel
          + occupation_code   (mã ESCO của nghề)
          + job_title_vi      (tên tiếng Việt)
        """
        self._check_loaded()
        code_map = self._occ.set_index("conceptUri")["code"].to_dict()
        vi_map   = (
            self._roles
            .drop_duplicates(subset="ESCO Code")
            .set_index("ESCO Code")["Vietnamese"]
            .to_dict()
        )
        df = self._rel.copy()
        df["occupation_code"] = df["occupationUri"].map(code_map)
        df["job_title_vi"]    = df["occupation_code"].map(vi_map)
        return df.reset_index(drop=True)

    # ─────────────────────────────────────────────────────────────────────────
    # 3. SUMMARY – thống kê nhanh
    # ─────────────────────────────────────────────────────────────────────────
    def summary(self) -> pd.DataFrame:
        """
        Bảng thống kê số kỹ năng essential / optional theo từng nghề.

        Returns
        -------
        DataFrame với cột:
          occupation_code | occupationLabel | job_title_vi
          essential_count | optional_count | total_skills
        """
        self._check_loaded()
        rel = self.get_relations()
        pivot = (
            rel.groupby(["occupation_code", "occupationLabel",
                         "job_title_vi", "relationType"])
            .size()
            .unstack(fill_value=0)
            .reset_index()
        )
        for col in ["essential", "optional"]:
            if col not in pivot.columns:
                pivot[col] = 0
        pivot["total_skills"] = pivot["essential"] + pivot["optional"]
        return pivot.rename(columns={
            "essential": "essential_count",
            "optional":  "optional_count",
        }).sort_values("total_skills", ascending=False)

    def get_occupation_detail(
        self,
        code: str,
        relation_type: Optional[str] = None,
    ) -> dict:
        """
        Chi tiết đầy đủ của một nghề theo mã ESCO.

        Parameters
        ----------
        code          : mã ESCO, vd "2511.20"
        relation_type : "essential" | "optional" | None (lấy cả hai)

        Returns
        -------
        dict với keys: occupation, skills, relations
        """
        self._check_loaded()
        code = str(code)

        occ_row = self._occ[self._occ["code"] == code]
        if occ_row.empty:
            raise ValueError(f"Không tìm thấy nghề với mã: {code}")
        occ_uri = occ_row.iloc[0]["conceptUri"]

        rel = self.get_relations()
        rel = rel[rel["occupationUri"] == occ_uri]
        if relation_type:
            rel = rel[rel["relationType"] == relation_type]

        skill_uris  = set(rel["skillUri"])
        skills_df   = self._sk[self._sk["conceptUri"].isin(skill_uris)]

        return {
            "occupation": occ_row.iloc[0].to_dict(),
            "relations":  rel.to_dict(orient="records"),
            "skills":     skills_df.to_dict(orient="records"),
        }

    # ─────────────────────────────────────────────────────────────────────────
    # 4. EXPORT
    # ─────────────────────────────────────────────────────────────────────────
    def export_all(
        self,
        output_dir: str = "output",
        fmt: str = "csv",
    ) -> list[Path]:
        """
        Xuất toàn bộ DataFrames ra thư mục.

        Parameters
        ----------
        output_dir : thư mục đích (tự tạo nếu chưa có)
        fmt        : "csv" hoặc "json"

        Returns
        -------
        Danh sách đường dẫn file đã tạo.
        """
        self._check_loaded()
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)

        tables = {
            "occupations": self.get_occupations(),
            "skills":      self.get_skills(),
            "relations":   self.get_relations(),
            "summary":     self.summary(),
            "roles_mapped": self.get_roles(),
        }

        paths: list[Path] = []
        for name, df in tables.items():
            if fmt == "json":
                p = out / f"{name}.json"
                df.to_json(p, orient="records", force_ascii=False, indent=2)
            else:
                p = out / f"{name}.csv"
                df.to_csv(p, index=False, encoding="utf-8-sig")
            log.info("  Đã xuất: %s (%d dòng)", p, len(df))
            paths.append(p)

        log.info("Export xong → %s", out.resolve())
        return paths

    def export_per_occupation(
        self,
        output_dir: str = "output/per_occupation",
        fmt: str = "json",
    ) -> list[Path]:
        """
        Mỗi nghề xuất thành 1 file riêng chứa đầy đủ occupation + skills +
        relations (tiện load vào graph DB hoặc vector store).
        """
        self._check_loaded()
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)

        paths: list[Path] = []
        for _, row in self._occ.iterrows():
            code   = row["code"]
            label  = row["preferredLabel"].replace("/", "-").replace(" ", "_")
            detail = self.get_occupation_detail(code)

            if fmt == "json":
                p = out / f"{code}_{label}.json"
                p.write_text(
                    json.dumps(detail, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
            else:
                p = out / f"{code}_{label}.csv"
                pd.DataFrame(detail["relations"]).to_csv(
                    p, index=False, encoding="utf-8-sig"
                )

            paths.append(p)

        log.info("Xuất %d file nghề → %s", len(paths), out.resolve())
        return paths

    # ─────────────────────────────────────────────────────────────────────────
    # PRIVATE HELPERS
    # ─────────────────────────────────────────────────────────────────────────
    def _check_loaded(self) -> None:
        if not self._loaded:
            raise RuntimeError("Chưa gọi load(). Hãy gọi extractor.load() trước.")

    def _read_roles(self) -> pd.DataFrame:
        df = pd.read_csv(self.roles_csv, dtype=str)
        df.columns = df.columns.str.strip()
        df["ESCO Code"] = df["ESCO Code"].str.strip()
        return df

    def _get_target_codes(self) -> set[str]:
        return set(self._roles["ESCO Code"].dropna().unique())

    def _read_occupations(self, target_codes: set[str]) -> pd.DataFrame:
        existing_cols = self._zip_columns(_F_OCC)
        cols = [c for c in _OCC_COLS if c in existing_cols]

        with zipfile.ZipFile(self.esco_zip) as z:
            with z.open(_F_OCC) as f:
                df = pd.read_csv(f, usecols=cols, dtype=str)

        df["code"] = df["code"].str.strip()
        return df[df["code"].isin(target_codes)].copy()

    def _read_relations(self, occ_uris: set[str]) -> pd.DataFrame:
        existing_cols = self._zip_columns(_F_REL)
        cols = [c for c in _REL_COLS if c in existing_cols]

        chunks = []
        with zipfile.ZipFile(self.esco_zip) as z:
            with z.open(_F_REL) as f:
                reader = pd.read_csv(f, usecols=cols, dtype=str,
                                     chunksize=20_000)
                for chunk in reader:
                    filtered = chunk[chunk["occupationUri"].isin(occ_uris)]
                    if not filtered.empty:
                        chunks.append(filtered)

        return pd.concat(chunks, ignore_index=True) if chunks else pd.DataFrame(columns=cols)

    def _read_skills(self, skill_uris: set[str]) -> pd.DataFrame:
        existing_cols = self._zip_columns(_F_SK)
        cols = [c for c in _SK_COLS if c in existing_cols]

        chunks = []
        with zipfile.ZipFile(self.esco_zip) as z:
            with z.open(_F_SK) as f:
                reader = pd.read_csv(f, usecols=cols, dtype=str,
                                     chunksize=20_000)
                for chunk in reader:
                    filtered = chunk[chunk["conceptUri"].isin(skill_uris)]
                    if not filtered.empty:
                        chunks.append(filtered)

        return pd.concat(chunks, ignore_index=True) if chunks else pd.DataFrame(columns=cols)

    def _zip_columns(self, filename: str) -> list[str]:
        """Trả về danh sách cột của 1 file CSV trong ZIP (chỉ đọc header)."""
        with zipfile.ZipFile(self.esco_zip) as z:
            with z.open(filename) as f:
                return pd.read_csv(f, nrows=0).columns.tolist()


# ─────────────────────────────────────────────────────────────────────────────
# CLI demo
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="ESCO 30-role extractor")
    parser.add_argument("--zip",    default="ESCO_dataset_-_v1_2_1_-_classification_-_en_-_csv.zip")
    parser.add_argument("--roles",  default="30_roles_summary.csv")
    parser.add_argument("--out",    default="output")
    parser.add_argument("--fmt",    default="csv", choices=["csv", "json"])
    parser.add_argument("--per-occ", action="store_true",
                        help="Xuất thêm file riêng cho từng nghề (JSON)")
    args = parser.parse_args()

    ex = ESCOExtractor(args.zip, args.roles)
    ex.load()

    print("\n=== SUMMARY ===")
    print(ex.summary().to_string(index=False))

    ex.export_all(args.out, fmt=args.fmt)

    if args.per_occ:
        ex.export_per_occupation(f"{args.out}/per_occupation", fmt="json")
