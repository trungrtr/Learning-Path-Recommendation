"""Build a versioned ESCO subset for the skill-mapping pipeline."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_ESCO_ZIP = PROJECT_DIR.parents[1] / "raw" / "ESCO dataset - v1.2.1 - classification - en - csv.zip"
DEFAULT_OUTPUT_DIR = PROJECT_DIR.parents[1] / "esco_data"

def _read_from_zip(zip_path: Path, filename: str) -> pd.DataFrame:
    if not zip_path.is_file():
        raise FileNotFoundError(f"Missing ESCO zip file: {zip_path}")
    import zipfile
    with zipfile.ZipFile(zip_path) as z:
        with z.open(filename) as f:
            frame = pd.read_csv(f, dtype=str, keep_default_na=False)
    frame.columns = [column.strip() for column in frame.columns]
    for column in frame.columns:
        frame[column] = frame[column].map(lambda value: value.strip())
    return frame


def _require_columns(frame: pd.DataFrame, path: Path, columns: set[str]) -> None:
    missing = columns.difference(frame.columns)
    if missing:
        raise ValueError(f"{path.name} is missing columns: {sorted(missing)}")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _write_csv(frame: pd.DataFrame, path: Path, sort_by: list[str]) -> None:
    frame = frame.drop_duplicates().sort_values(sort_by, kind="mergesort")
    frame.to_csv(path, index=False, encoding="utf-8", lineterminator="\n")


def _domain_label(occupation_codes: set[str]) -> tuple[str, str]:
    """Label provenance conservatively; selected occupations are IT roles."""
    if occupation_codes and all(code.startswith(("13", "25", "35")) for code in occupation_codes):
        return "in_domain", "linked to the selected IT occupations"
    return "out_of_domain", "linked occupation is outside the configured IT occupation groups"


import csv

def build_dataset(esco_zip: Path, output_dir: Path, version: str = "v1", summary_csv_path: Path = None) -> dict:
    if summary_csv_path is None:
        summary_csv_path = PROJECT_DIR.parents[1] / "summary_30nghe_v5_final.csv"

    occupations = _read_from_zip(esco_zip, "occupations_en.csv")
    relations = _read_from_zip(esco_zip, "occupationSkillRelations_en.csv")
    skills = _read_from_zip(esco_zip, "skills_en.csv")

    _require_columns(occupations, Path("occupations_en.csv"), {"conceptUri", "code"})
    _require_columns(relations, Path("occupationSkillRelations_en.csv"), {"occupationUri", "skillUri"})
    _require_columns(skills, Path("skills_en.csv"), {"conceptUri"})

    code_to_uri = dict(zip(occupations['code'], occupations['conceptUri']))
    
    merged_occupations_list = []
    merged_relations_list = []
    
    with open(summary_csv_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader) # skip header
        for row in reader:
            if not row: continue
            code_str = row[0]
            codes = [c.strip() for c in code_str.split(',') if c.strip()]
            
            orig_uris = [code_to_uri[c] for c in codes if c in code_to_uri]
            if not orig_uris:
                continue
                
            new_uri = f"http://data.europa.eu/esco/occupation/custom-{hashlib.md5(code_str.encode()).hexdigest()}"
            
            orig_occs = occupations[occupations['conceptUri'].isin(orig_uris)]
            
            def _get_first(col):
                if col in orig_occs and not orig_occs[col].dropna().empty:
                    return str(orig_occs[col].dropna().iloc[0])
                return ""
                
            def _join_text(col):
                if col in orig_occs:
                    # filter out empty strings and join
                    vals = [str(x).strip() for x in orig_occs[col].dropna() if str(x).strip()]
                    return " | ".join(vals)
                return ""
            
            merged_occupations_list.append({
                "conceptType": _get_first('conceptType'),
                "conceptUri": new_uri,
                "iscoGroup": _get_first('iscoGroup'),
                "preferredLabel": row[1],
                "job_title_vi": row[2],
                "altLabels": _join_text('altLabels'),
                "hiddenLabels": _join_text('hiddenLabels'),
                "status": _get_first('status'),
                "modifiedDate": _get_first('modifiedDate'),
                "regulatedProfessionNote": _join_text('regulatedProfessionNote'),
                "scopeNote": _join_text('scopeNote'),
                "definition": _join_text('definition'),
                "inScheme": _get_first('inScheme'),
                "description": _join_text('description'),
                "code": code_str,
                "naceCode": _get_first('naceCode')
            })
            
            orig_rels = relations[relations['occupationUri'].isin(orig_uris)]
            skill_groups = orig_rels.groupby('skillUri')
            
            for skill_uri, group in skill_groups:
                if 'essential' in group['relationType'].values:
                    rel_type = 'essential'
                else:
                    rel_type = 'optional'
                
                skill_type = group['skillType'].iloc[0]
                merged_relations_list.append({
                    "occupationUri": new_uri,
                    "skillUri": skill_uri,
                    "relationType": rel_type,
                    "skillType": skill_type
                })

    selected_occupations = pd.DataFrame(merged_occupations_list)
    selected_relations = pd.DataFrame(merged_relations_list)

    if selected_occupations.empty:
        raise ValueError(f"{summary_csv_path.name} does not contain selected occupation URIs")

    skill_uris = set(selected_relations["skillUri"])
    skill_uris.discard("")
    selected_skills = skills[skills["conceptUri"].isin(skill_uris)].copy()
    missing_skills = skill_uris.difference(selected_skills["conceptUri"])
    if missing_skills:
        raise ValueError(f"Relation skills missing from skills.csv: {sorted(missing_skills)}")

    occupation_codes_by_skill = (
        selected_relations.assign(skillUri=selected_relations["skillUri"])
        .merge(selected_occupations[["conceptUri", "code"]], left_on="occupationUri", right_on="conceptUri", how="left")
        .groupby("skillUri")["code"]
        .apply(lambda values: set(values[values != ""]))
        .to_dict()
    )
    labels = selected_skills["conceptUri"].map(
        lambda uri: _domain_label(occupation_codes_by_skill.get(uri, set()))
    )
    selected_skills["uniskill_domain"] = labels.map(lambda value: value[0])
    selected_skills["domain_reason"] = labels.map(lambda value: value[1])

    output_dir.mkdir(parents=True, exist_ok=True)
    occupations_out = output_dir / "occupations.csv"
    skills_out = output_dir / "skills.csv"
    relations_out = output_dir / "relations.csv"
    
    # Ensure column order matches insertion order
    if not selected_occupations.empty:
        col_order = ["conceptType", "conceptUri", "iscoGroup", "preferredLabel", "job_title_vi", "altLabels", "hiddenLabels", "status", "modifiedDate", "regulatedProfessionNote", "scopeNote", "definition", "inScheme", "description", "code", "naceCode"]
        selected_occupations = selected_occupations[[c for c in col_order if c in selected_occupations.columns]]
        
    _write_csv(selected_occupations, occupations_out, ["conceptUri"])
    _write_csv(selected_skills, skills_out, ["conceptUri"])
    _write_csv(selected_relations, relations_out, ["occupationUri", "skillUri", "relationType", "skillType"])

    outputs = [occupations_out, skills_out, relations_out]
    manifest = {
        "version": version,
        "filtered_at": date.today().isoformat(),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": f"ESCO bulk download plus {summary_csv_path.name}",
        "source_files": {
            summary_csv_path.name: _sha256(summary_csv_path),
            esco_zip.name: _sha256(esco_zip)
        },
        "filter_rule": f"Keep the occupations in {summary_csv_path.name} and all related ESCO skills.",
        "keys": {"occupation": "conceptUri", "skill": "conceptUri", "relation": ["occupationUri", "skillUri", "relationType", "skillType"]},
        "domain_rule": "in_domain when every linked selected occupation has an ISCO code starting with 13, 25, or 35; otherwise out_of_domain.",
        "counts": {
            "occupation_count": int(len(selected_occupations)),
            "skill_count": int(len(selected_skills)),
            "relation_count": int(len(selected_relations)),
        },
        "outputs": {path.name: {"sha256": _sha256(path), "bytes": path.stat().st_size} for path in outputs},
    }
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    _validate_output(output_dir, manifest)
    return manifest


def _validate_output(output_dir: Path, manifest: dict) -> None:
    occupations = pd.read_csv(output_dir / "occupations.csv", dtype=str, keep_default_na=False)
    skills = pd.read_csv(output_dir / "skills.csv", dtype=str, keep_default_na=False)
    relations = pd.read_csv(output_dir / "relations.csv", dtype=str, keep_default_na=False)
    occupation_uris = set(occupations["conceptUri"])
    skill_uris = set(skills["conceptUri"])
    if not set(relations["occupationUri"]).issubset(occupation_uris):
        raise ValueError("Validation failed: relation references an unknown occupation")
    if not set(relations["skillUri"]).issubset(skill_uris):
        raise ValueError("Validation failed: relation references an unknown skill")
    relation_keys = relations[["occupationUri", "skillUri", "relationType", "skillType"]]
    if relation_keys.duplicated().any():
        raise ValueError("Validation failed: duplicate relation key")
    for filename, expected in manifest["outputs"].items():
        if _sha256(output_dir / filename) != expected["sha256"]:
            raise ValueError(f"Validation failed: checksum mismatch for {filename}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the versioned filtered ESCO dataset")
    parser.add_argument("--esco-zip", type=Path, default=DEFAULT_ESCO_ZIP)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--summary-csv", type=Path, default=None)
    parser.add_argument("--version", default="v1")
    args = parser.parse_args()
    manifest = build_dataset(args.esco_zip, args.output_dir, args.version, args.summary_csv)
    print(json.dumps(manifest["counts"], indent=2))


if __name__ == "__main__":
    main()