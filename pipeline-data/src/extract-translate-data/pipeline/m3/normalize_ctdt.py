"""
Chuẩn hóa dữ liệu Chương trình đào tạo (CTDT) từ dict crawl.
Chuyển đổi cấu trúc phân cấp thành các bảng phẳng: phan, nhom, hoc_phan, quan_he.
"""

from __future__ import annotations

import json
import re
import unicodedata
from collections import defaultdict, OrderedDict
from pathlib import Path
from typing import Any

_TEN_NHOM_RE = re.compile(
    r'^([IVX]+\.\d+)\.\s+'   # cấp 1: mã phần,   vd "I.2"
    r'(.+?)'                  # cấp 2: tên base   (non-greedy → dừng ở —)
    r'\s+—\s+'                # dấu phân cách em-dash (U+2014)
    r'([\d.]+)\s+tín chỉ'    # số tín chỉ
    r'(?:\s*-\s*(.*))?$'     # phần sub-group (tuỳ chọn)
)
_NHOM_PREFIX_RE = re.compile(r'^[Nn]h[oó]m\s+')


def slugify(s: str) -> str:
    """Chuyển chuỗi có dấu tiếng Việt sang slug ASCII chữ hoa."""
    decomposed = unicodedata.normalize('NFKD', s)
    ascii_only = ''.join(c for c in decomposed if not unicodedata.combining(c))
    slug = re.sub(r'[^A-Za-z0-9]+', '_', ascii_only)
    return slug.strip('_').upper()


def parse_ten_nhom(s: str) -> tuple[str, str, float, str | None]:
    """Tách chuỗi ten_nhom thành 4 trường riêng biệt."""
    m = _TEN_NHOM_RE.match(s.strip())
    if not m:
        return ('?', s.strip(), 0.0, None)

    ma_phan  = m.group(1)
    ten_base = m.group(2).strip()
    so_tc    = float(m.group(3))
    sub_raw  = (m.group(4) or '').strip()

    if not sub_raw:
        return (ma_phan, ten_base, so_tc, None)

    sub_stripped = _NHOM_PREFIX_RE.sub('', sub_raw).strip()
    if re.match(r'^[A-Za-z0-9_]+$', sub_stripped):
        sub_code = sub_stripped.upper()
    else:
        sub_code = slugify(sub_stripped)

    return (ma_phan, ten_base, so_tc, sub_code)


def _make_raw_nhom_id(ma_phan: str, sub_code: str | None) -> str:
    section_slug = ma_phan.replace('.', '_')
    return f'{section_slug}_{sub_code}' if sub_code else section_slug


def _resolve_duplicates(raw_ids: list[str]) -> list[str]:
    freq: dict[str, int] = defaultdict(int)
    for rid in raw_ids:
        freq[rid] += 1

    occurrence: dict[str, int] = defaultdict(int)
    resolved: list[str] = []

    for rid in raw_ids:
        if freq[rid] == 1:
            resolved.append(rid)
        else:
            occurrence[rid] += 1
            suffix = chr(64 + occurrence[rid])
            resolved.append(f'{rid}_{suffix}')

    return resolved


def process_ctdt_record(raw: dict[str, Any], source_file: str) -> dict[str, Any]:
    """
    Nhận dict JSON gốc của CTDT, trả về dict đã được làm phẳng (flat).
    """
    if 'data' in raw and isinstance(raw['data'], dict):
        d = raw['data']
    else:
        d = raw

    ma_ctdt   = str(d.get('ma_ctdt', ''))
    nhoms     = d.get('nhom_hoc_phan', [])
    ctdt_info = d.get('chuong_trinh_dao_tao', {})

    hp_lookup: dict[str, str] = {}
    for n in nhoms:
        for hp in n.get('hoc_phan', []):
            hp_lookup[hp['ma_hoc_phan']] = hp['ten_hoc_phan']

    parsed_nhoms: list[dict[str, Any]] = []
    for n in nhoms:
        ma_phan, ten_base, so_tc, sub_code = parse_ten_nhom(n.get('ten_nhom', ''))
        parsed_nhoms.append({
            'raw_id'             : _make_raw_nhom_id(ma_phan, sub_code),
            'ma_phan'            : ma_phan,
            'ten_nhom_base'      : ten_base,
            'sub_nhom_code'      : sub_code,
            'loai_nhom'          : n.get('loai_nhom'),
            'so_tin_chi_yeu_cau' : n.get('so_tin_chi_yeu_cau', so_tc),
            '_hoc_phan'          : n.get('hoc_phan', []),
        })

    resolved = _resolve_duplicates([p['raw_id'] for p in parsed_nhoms])
    for p, nhom_id in zip(parsed_nhoms, resolved):
        p['nhom_id'] = nhom_id

    nhom_flat: list[dict[str, Any]] = [
        {
            'nhom_id'            : p['nhom_id'],
            'ma_ctdt'            : ma_ctdt,
            'ma_phan'            : p['ma_phan'],
            'ten_nhom_base'      : p['ten_nhom_base'],
            'sub_nhom_code'      : p['sub_nhom_code'],
            'loai_nhom'          : p['loai_nhom'],
            'so_tin_chi_yeu_cau' : p['so_tin_chi_yeu_cau'],
        }
        for p in parsed_nhoms
    ]

    phan_map: OrderedDict[str, dict[str, Any]] = OrderedDict()
    for nhom in nhom_flat:
        mp = nhom['ma_phan']
        if mp not in phan_map:
            phan_map[mp] = {
                'ma_phan'            : mp,
                'ma_ctdt'            : ma_ctdt,
                'ten_phan'           : nhom['ten_nhom_base'],
                'so_tin_chi_yeu_cau' : nhom['so_tin_chi_yeu_cau'],
                'so_nhom'            : 0,
                'nhom_ids'           : [],
            }
        phan_map[mp]['nhom_ids'].append(nhom['nhom_id'])
        phan_map[mp]['so_nhom'] += 1

    phan_flat: list[dict[str, Any]] = list(phan_map.values())

    hoc_phan_flat: list[dict[str, Any]] = []
    quan_he_flat : list[dict[str, Any]] = []

    for p in parsed_nhoms:
        for hp in p['_hoc_phan']:
            ma_hp = hp['ma_hoc_phan']
            hoc_phan_flat.append({
                'ma_ctdt'      : ma_ctdt,
                'nhom_id'      : p['nhom_id'],
                'ma_phan'      : p['ma_phan'],
                'loai_nhom'    : p['loai_nhom'],
                'ma_hoc_phan'  : ma_hp,
                'ten_hoc_phan' : hp.get('ten_hoc_phan'),
                'so_tin_chi'   : hp.get('so_tin_chi_tong'),
                'hoc_ky_goi_y' : hp.get('hoc_ky_goi_y'),
                'so_quan_he'   : len(hp.get('quan_he', [])),
            })

            for qh in hp.get('quan_he', []):
                ma_ref  = qh['ma_hoc_phan']
                ten_ref = hp_lookup.get(ma_ref)
                quan_he_flat.append({
                    'ma_ctdt'          : ma_ctdt,
                    'nhom_id'          : p['nhom_id'],
                    'ma_hoc_phan'      : ma_hp,
                    'ten_hoc_phan'     : hp.get('ten_hoc_phan'),
                    'loai_quan_he'     : qh.get('loai'),
                    'ma_hoc_phan_ref'  : ma_ref,
                    'ten_hoc_phan_ref' : ten_ref,
                    'backfill_source'  : 'same_ctdt' if ten_ref is not None else 'not_found',
                })

    return {
        'meta': {
            'ma_ctdt'    : ma_ctdt,
            'ten_ctdt'   : ctdt_info.get('ten_ctdt'),
            'bac_dao_tao': ctdt_info.get('bac_dao_tao'),
            'phien_ban'  : ctdt_info.get('phien_ban'),
            'source_file': raw.get('source_file', source_file),
        },
        'phan_flat'     : phan_flat,
        'nhom_flat'     : nhom_flat,
        'hoc_phan_flat' : hoc_phan_flat,
        'quan_he_flat'  : quan_he_flat,
    }


def normalize(file_path: str | Path) -> dict[str, Any]:
    """Đọc một file JSON CTDT và trả về dữ liệu đã chuẩn hóa dạng phẳng."""
    path = Path(file_path)
    with path.open(encoding="utf-8") as file:
        raw = json.load(file)
    if not isinstance(raw, dict):
        raise ValueError(f"CTDT input must be a JSON object: {path}")
    return process_ctdt_record(raw, path.name)


def _print_summary(result: dict[str, Any]) -> None:
    """In tóm tắt kiểm tra nhanh cho CLI, không dùng trong pipeline."""
    meta = result["meta"]
    nhom = result["nhom_flat"]
    quan_he = result["quan_he_flat"]
    found = sum(item["backfill_source"] == "same_ctdt" for item in quan_he)
    duplicate_ids = len({item["nhom_id"] for item in nhom}) != len(nhom)
    print(f"CTDT: {meta['ma_ctdt']} - {meta['ten_ctdt']}")
    print(f"phan_flat: {len(result['phan_flat'])}")
    print(f"nhom_flat: {len(nhom)}")
    print(f"hoc_phan_flat: {len(result['hoc_phan_flat'])}")
    print(f"quan_he_flat: {len(quan_he)} (backfill same_ctdt: {found})")
    print(f"nhom_id_unique: {not duplicate_ids}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m pipeline.m3.normalize_ctdt <input.json> [output.json]")
        raise SystemExit(1)

    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else input_path.with_name(
        f"{input_path.stem}_normalized.json"
    )
    normalized = normalize(input_path)
    output_path.write_text(
        json.dumps(normalized, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    _print_summary(normalized)
    print(f"output: {output_path}")
