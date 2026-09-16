# CTDT and course contract

The contract has two top-level branches. CTDT files define the allowed
programmes, groups, and course memberships. Shared course folders contain
only resolved courses referenced by at least one CTDT:

```text
contract/
└── ctdt/
    └── <ma_ctdt>/
        ├── CTDT_<ma_ctdt>.json
        ├── MISSING_COURSES.md
└── hoc_phan/
    └── <ma_hoc_phan>/
        ├── <ma_hoc_phan>__hoc_phan.json
        ├── <ma_hoc_phan>__muc_tieu.json
        ├── <ma_hoc_phan>__clo.json
        └── <ma_hoc_phan>__bai_hoc.json
```

Supplementary courses keep their complete original code and receive the
`_BS` suffix, for example `BS6038_BS`. The CTDT file lists programme
metadata, course groups, all course codes, and explicitly separates courses
resolved from `hoc_phan_bo_sung`.
`MISSING_COURSES.md` lists CTDT courses that were not found in either source.
Course folders contain the translated course data consumed by the
skill-mapping pipeline. A course referenced by multiple CTDTs is stored once
and keeps all of its `ctdt_memberships`.