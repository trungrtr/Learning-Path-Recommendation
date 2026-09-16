"""
M3B — CTDT translation: translate string fields from normalized CTDT records.

Strategy:
  1. Collect  — scan all normalized CTDT JSON files, gather unique Vietnamese strings
               per field category (ten_ctdt, ten_nhom, ten_hoc_phan, enum labels).
  2. Translate — send ONE batched LLM call per chunk (≤ BATCH_SIZE unique strings),
               using a semantics-aware prompt that enforces standard CS/academic terms.
  3. Persist  — merge results into a persistent translation table (vi_to_en_ctdt.json)
               so reruns only translate NEW strings (incremental / idempotent).
  4. Apply    — inject *_en fields into each normalized CTDT record and write the
               bilingual output to data/7_translated_entities/ctdt/.

Fields translated:
  • chuong_trinh_dao_tao.ten_ctdt       → ten_ctdt_en
  • chuong_trinh_dao_tao.bac_dao_tao    → bac_dao_tao_en
  • nhom_hoc_phan[].ten_nhom (parsed)   → ten_nhom_base_en
  • nhom_hoc_phan[].loai_nhom (enum)    → loai_nhom_en      (static, no LLM)
  • hoc_phan[].ten_hoc_phan             → ten_hoc_phan_en
  • quan_he[].loai (enum)               → loai_quan_he_en   (static, no LLM)

Fields NOT translated (kept as-is):
  • ma_ctdt, ma_hoc_phan, ma_in, phien_ban — codes, not text
  • so_tin_chi_*, hoc_ky_goi_y            — numeric
  • JSON structure keys                    — always Vietnamese in the pipeline

call_gemini is imported lazily (late import) because it raises NotImplementedError
until the real Gemini wrapper is wired in shared/llm_client.py.
"""

from __future__ import annotations

import copy
import json
import logging
import re
from pathlib import Path
from typing import Any

from shared.file_io import get_content_hash, read_json, read_yaml_config, write_json
from shared.logger import get_logger

logger = get_logger("m3b_translate_ctdt")

# ─────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────

# Maximum unique strings per LLM call — keeps prompt size bounded.
BATCH_SIZE: int = 200

# Enum → English: resolved statically, never sent to the LLM.
ENUM_LOAI_NHOM: dict[str, str] = {
    "BAT_BUOC": "Required",
    "TU_CHON":  "Elective",
}

ENUM_LOAI_QUAN_HE: dict[str, str] = {
    "TIEN_QUYET": "Prerequisite",
    "HOC_TRUOC":  "Prior Study",
}

# Compiled once for ten_nhom parsing (mirrors normalize_ctdt._TEN_NHOM_RE)
_TEN_NHOM_BASE_RE = re.compile(
    r'^(?:[IVX]+\.\d+\.\s+)?'          # optional section prefix e.g. "I.1. "
    r'(.+?)'                            # base name (non-greedy)
    r'\s+\u2014\s+[\d.]+\s+t\u00edn ch\u1ec9'  # " — 13.0 tín chỉ"
    r'(?:\s*-\s*.*)?$',                 # optional sub-group suffix
)

# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def _extract_ten_nhom_base(ten_nhom: str) -> str | None:
    """Return the semantic base name from a raw ten_nhom string.

    "I.1. Lý luận chính trị - Pháp luật — 13.0 tín chỉ"
    → "Lý luận chính trị - Pháp luật"

    Falls back to the full stripped string if pattern doesn't match.
    """
    s = ten_nhom.strip()
    m = _TEN_NHOM_BASE_RE.match(s)
    return m.group(1).strip() if m else (s or None)


def _t(table: dict[str, str], vi: str | None, field: str = "") -> str | None:
    """Look up *vi* in *table*; log a debug warning on cache miss."""
    if vi is None:
        return None
    en = table.get(vi.strip())
    if en is None:
        logger.debug("No translation for %r (field=%s)", vi, field)
    return en


def _chunked(lst: list, n: int):
    """Yield successive n-sized chunks from *lst*."""
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


# ─────────────────────────────────────────────
# LLM prompt + call
# ─────────────────────────────────────────────

_PROMPT_PREAMBLE = """\
Translate the following Vietnamese university curriculum strings to English.
Rules:
1. Use standard English academic / CS terminology where an established term exists.
   Examples: "Linear Algebra" not "Linear Algebraics";
             "Data Structures and Algorithms" not "Data Structure and Algorithm".
2. Preserve conjunctions — Vietnamese often drops "và"; add "and" in English.
   Example: "Xác suất thống kê" → "Probability and Statistics".
3. Use gerund/adjective forms for knowledge-block names, not noun stacks.
   Example: "Kiến thức cơ sở của Nhóm ngành" → "Discipline-Group Foundation Courses".
4. Do NOT translate proper nouns or Vietnamese-specific political subjects literally.
   "Triết học Mác-Lênin" → "Marxist-Leninist Philosophy" (NOT "Marx-Lenin Philosophy").
   "Tư tưởng Hồ Chí Minh" → "Ho Chi Minh Thought" (standard academic term).
5. Keep translations concise: ≤ 6 words for course names, ≤ 5 words for block names.
6. Return ONLY a JSON object mapping each Vietnamese key to its English translation.
   No explanations, no alternatives, no markdown code fences.
Example:
{"Hệ thống thông tin": "Information Systems", "Đại số tuyến tính": "Linear Algebra"}
"""


def _build_prompt(strings: list[str]) -> str:
    payload = {s: "" for s in strings}
    return _PROMPT_PREAMBLE + "\nInput:\n" + json.dumps(payload, ensure_ascii=False)


def _call_llm(strings: list[str], model: str) -> dict[str, str]:
    """Translate *strings* via Gemini; return {vi: en} mapping.

    Raises:
        NotImplementedError — if call_gemini is not yet wired up.
        RuntimeError        — if the LLM response cannot be parsed as a dict.
    """
    from shared.llm_client import call_gemini  # late import (may raise NotImplementedError)

    raw = call_gemini(_build_prompt(strings), model).strip()

    # Strip accidental markdown fences
    if raw.startswith("```"):
        raw = raw.split("```", 2)[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.rsplit("```", 1)[0].strip()

    parsed = json.loads(raw)
    if not isinstance(parsed, dict):
        raise RuntimeError(f"LLM returned non-dict JSON: {type(parsed)}")
    return {k: v for k, v in parsed.items() if isinstance(k, str) and isinstance(v, str)}


# ─────────────────────────────────────────────
# String collection (Step 1)
# ─────────────────────────────────────────────

def collect_unique_strings(ctdt_files: list[Path]) -> set[str]:
    """Walk normalized CTDT JSON files and collect unique Vietnamese strings
    that require LLM translation (enum fields are excluded — handled statically)."""
    strings: set[str] = set()

    for path in ctdt_files:
        try:
            record = read_json(path)
        except Exception as exc:
            logger.warning("Cannot read %s: %s", path, exc)
            continue

        data = record.get("data", {}) if isinstance(record, dict) else {}
        if "meta" in data:
            for field in ("ten_ctdt", "bac_dao_tao"):
                value = data.get("meta", {}).get(field)
                if isinstance(value, str) and value.strip():
                    strings.add(value.strip())
            for group in data.get("nhom_flat", []) or []:
                value = group.get("ten_nhom_base")
                if isinstance(value, str) and value.strip():
                    strings.add(value.strip())
            for course in data.get("hoc_phan_flat", []) or []:
                value = course.get("ten_hoc_phan")
                if isinstance(value, str) and value.strip():
                    strings.add(value.strip())
            continue

        ctdt_info = data.get("chuong_trinh_dao_tao", {})

        # Program-level fields
        for field in ("ten_ctdt", "bac_dao_tao"):
            val = ctdt_info.get(field)
            if val and isinstance(val, str):
                strings.add(val.strip())

        # Group and course names
        for nhom in data.get("nhom_hoc_phan", []) or []:
            ten_nhom_raw = nhom.get("ten_nhom")
            if ten_nhom_raw and isinstance(ten_nhom_raw, str):
                base = _extract_ten_nhom_base(ten_nhom_raw)
                if base:
                    strings.add(base)

            for hp in nhom.get("hoc_phan", []) or []:
                name = hp.get("ten_hoc_phan")
                if name and isinstance(name, str):
                    strings.add(name.strip())

    return strings


# ─────────────────────────────────────────────
# Translation table (Step 2 + 3)
# ─────────────────────────────────────────────

def load_translation_table(table_path: Path) -> dict[str, str]:
    """Load the persistent translation table from disk (or return {})."""
    if table_path.exists():
        try:
            data = read_json(table_path)
            if isinstance(data, dict):
                return data
        except Exception as exc:
            logger.warning("Could not load translation table %s: %s", table_path, exc)
    return {}


def translate_missing(
    strings: set[str],
    table: dict[str, str],
    model: str,
) -> dict[str, str]:
    """Translate strings absent from *table*; update and return *table*.

    Falls back gracefully when call_gemini is not yet implemented — logs a
    warning and stops further chunks (translation_status will show "llm_unavailable"
    for any string that was not already in the table).
    """
    missing = sorted(s for s in strings if s not in table)
    if not missing:
        logger.info(
            "All %d strings already in translation table — LLM skipped.", len(strings)
        )
        return table

    total_chunks = -(-len(missing) // BATCH_SIZE)  # ceiling division
    logger.info(
        "Translating %d new strings in %d chunk(s) via model %s",
        len(missing), total_chunks, model,
    )

    for i, chunk in enumerate(_chunked(missing, BATCH_SIZE), start=1):
        logger.info("  Chunk %d/%d  (%d strings)…", i, total_chunks, len(chunk))
        try:
            result = _call_llm(chunk, model)
            table.update(result)
            for s in chunk:
                if s not in result:
                    logger.warning("LLM did not return translation for: %r", s)
        except NotImplementedError:
            logger.warning(
                "shared.llm_client.call_gemini is not yet implemented — "
                "CTDT translation skipped from chunk %d onward. "
                "Wire up shared/llm_client.py to enable production translation.",
                i,
            )
            break
        except json.JSONDecodeError as exc:
            logger.error("LLM response could not be parsed as JSON (chunk %d): %s", i, exc)
            raise
        except Exception as exc:
            logger.error("LLM call failed for chunk %d: %s", i, exc)
            raise

    return table


# ─────────────────────────────────────────────
# Apply translations (Step 4)
# ─────────────────────────────────────────────

def apply_translations(
    record: dict[str, Any],
    table: dict[str, str],
) -> dict[str, Any]:
    """Return a deep-copied record with *_en fields injected at every translatable field.

    Original Vietnamese fields are preserved unchanged.
    Enum fields (loai_nhom, loai) are resolved from static dicts — not from *table*.
    """
    out = copy.deepcopy(record)
    data: dict[str, Any] = out.get("data", {})

    if "meta" in data:
        meta = data.get("meta", {})
        meta["ten_ctdt_en"] = _t(table, meta.get("ten_ctdt"), "ten_ctdt")
        meta["bac_dao_tao_en"] = _t(table, meta.get("bac_dao_tao"), "bac_dao_tao")

        for group in data.get("nhom_flat", []) or []:
            group["ten_nhom_base_en"] = _t(
                table, group.get("ten_nhom_base"), "ten_nhom_base"
            )
            group["loai_nhom_en"] = ENUM_LOAI_NHOM.get(group.get("loai_nhom", ""))

        for course in data.get("hoc_phan_flat", []) or []:
            course["ten_hoc_phan_en"] = _t(
                table, course.get("ten_hoc_phan"), "ten_hoc_phan"
            )

        for relation in data.get("quan_he_flat", []) or []:
            relation["loai_quan_he_en"] = ENUM_LOAI_QUAN_HE.get(
                relation.get("loai_quan_he", "")
            )

        out["translation_status"] = "translated"
        out["translation_table_hash"] = get_content_hash(
            json.dumps(sorted(table.keys()), ensure_ascii=False)
        )
        return out

    # ── chuong_trinh_dao_tao ──────────────────────────────────────────────────
    ctdt_info: dict[str, Any] = data.get("chuong_trinh_dao_tao", {})
    if isinstance(ctdt_info, dict):
        ctdt_info["ten_ctdt_en"]    = _t(table, ctdt_info.get("ten_ctdt"),    "ten_ctdt")
        ctdt_info["bac_dao_tao_en"] = _t(table, ctdt_info.get("bac_dao_tao"), "bac_dao_tao")

    # ── nhom_hoc_phan ─────────────────────────────────────────────────────────
    for nhom in data.get("nhom_hoc_phan", []) or []:
        # Base name (extracted from raw ten_nhom)
        ten_nhom_raw: str | None = nhom.get("ten_nhom")
        base_vi = _extract_ten_nhom_base(ten_nhom_raw) if ten_nhom_raw else None
        nhom["ten_nhom_base_en"] = _t(table, base_vi, "ten_nhom_base") if base_vi else None

        # Enum: loai_nhom — static mapping only
        nhom["loai_nhom_en"] = ENUM_LOAI_NHOM.get(nhom.get("loai_nhom", ""))

        # ── hoc_phan ──────────────────────────────────────────────────────────
        for hp in nhom.get("hoc_phan", []) or []:
            hp["ten_hoc_phan_en"] = _t(table, hp.get("ten_hoc_phan"), "ten_hoc_phan")

            # ── quan_he ───────────────────────────────────────────────────────
            for qh in hp.get("quan_he", []) or []:
                qh["loai_quan_he_en"] = ENUM_LOAI_QUAN_HE.get(qh.get("loai", ""))

    # ── metadata ──────────────────────────────────────────────────────────────
    out["translation_status"] = "translated"
    out["translation_table_hash"] = get_content_hash(
        json.dumps(sorted(table.keys()), ensure_ascii=False)
    )

    return out


# ─────────────────────────────────────────────
# Public batch entry point
# ─────────────────────────────────────────────

def translate_ctdt_batch(config_path: str = "config.yaml") -> int:
    """Translate all normalized CTDT files.  Returns number of files written.

    Idempotent: files already present in output_root are skipped (unless the
    translation table changed — delete the output file to force retranslation).
    """
    config = read_yaml_config(config_path)

    input_root  = Path(config["paths"].get("normalized", "data/normalized_entities")) / "ctdt"
    output_root = Path(config["paths"].get("translated_entities", "data/7_translated_entities")) / "ctdt"
    table_path  = output_root / "vi_to_en_ctdt.json"
    model       = config["models"]["gemini_translation"]

    ctdt_files = sorted(input_root.glob("*.json"))
    if not ctdt_files:
        logger.warning("No normalized CTDT files found in %s", input_root)
        return 0

    logger.info("Found %d normalized CTDT file(s) in %s", len(ctdt_files), input_root)

    # Step 1 — load persistent translation table
    table = load_translation_table(table_path)
    logger.info("Loaded %d existing translations from table", len(table))

    # Step 2 — collect unique strings (excluding enums)
    unique_strings = collect_unique_strings(ctdt_files)
    logger.info("Collected %d unique translatable strings", len(unique_strings))

    # Step 3 — translate missing strings + update table
    table = translate_missing(unique_strings, table, model)

    # Step 4 — persist updated table
    write_json(table_path, table)
    logger.info("Translation table saved → %s (%d entries)", table_path, len(table))

    # Step 5 — apply translations and write bilingual output
    count = 0
    for path in ctdt_files:
        out_path = output_root / path.name
        if out_path.exists():
            logger.debug("Already translated, skipping: %s", path.name)
            continue
        try:
            record = read_json(path)
            if not isinstance(record, dict):
                logger.warning("Unexpected record format in %s — skipping", path.name)
                continue
            bilingual = apply_translations(record, table)
            write_json(out_path, bilingual)
            count += 1
            logger.info("Written → %s", out_path.name)
        except Exception as exc:
            logger.error("Failed to translate %s: %s", path.name, exc)

    logger.info("M3B CTDT translation complete: %d file(s) written.", count)
    return count


# ─────────────────────────────────────────────
# CLI — quick inspection / dev testing
# ─────────────────────────────────────────────

if __name__ == "__main__":
    import pprint
    import sys

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s — %(message)s")

    if len(sys.argv) == 2 and Path(sys.argv[1]).suffix == ".json":
        # Single-file mode: apply existing table (or stub) and print first nhom.
        path = Path(sys.argv[1])
        record = read_json(path)

        table_candidate = path.parent / "vi_to_en_ctdt.json"
        table = load_translation_table(table_candidate)
        if not table:
            # Build a stub so structure can be inspected without a real LLM call.
            stubs = collect_unique_strings([path])
            table = {s: f"[PENDING] {s}" for s in stubs}
            logger.info("No table found — using stub translations (%d strings)", len(stubs))

        result = apply_translations(record, table)
        print("\n=== chuong_trinh_dao_tao ===")
        pprint.pp(result["data"]["chuong_trinh_dao_tao"])
        print("\n=== nhom_hoc_phan[0] ===")
        pprint.pp(result["data"]["nhom_hoc_phan"][0])
        sys.exit(0)

    n = translate_ctdt_batch()
    print(f"Done — {n} CTDT record(s) translated.")
