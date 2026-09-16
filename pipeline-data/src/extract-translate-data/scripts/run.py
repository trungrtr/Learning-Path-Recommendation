"""Entrypoint cho extract-translate-data pipeline (chỉ extract + translate).

Ví dụ:
  python scripts/run.py --flow ctdt
  python scripts/run.py --flow syllabus
  python scripts/run.py --flow all
  python scripts/run.py --flow syllabus --resume-from m3
  python scripts/run.py --module m2
  python scripts/run.py --module m3
  python scripts/run.py --reset-interim

Lưu ý: M4/M5/M6 đã chuyển sang repo esco-skill-mapping.
Dùng esco-skill-mapping/scripts/run.py để chạy các module đó.
"""

import argparse
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pipeline.orchestrator import flow_syllabus, flow_ctdt, run_module


def main():
    parser = argparse.ArgumentParser(
        description="extract-translate-data: M2 (extract) + M3 (translate/export)"
    )
    parser.add_argument("--flow", choices=["syllabus", "ctdt", "all"])
    parser.add_argument("--module", choices=["m2", "m3"])
    parser.add_argument("--resume-from")
    parser.add_argument("--reset-interim", action="store_true")
    args = parser.parse_args()

    if args.reset_interim:
        raise NotImplementedError("xóa data/interim/* để chạy lại từ đầu")

    if args.module:
        run_module(args.module)
        return

    if args.flow == "ctdt":
        flow_ctdt(resume_from=args.resume_from)
    elif args.flow == "syllabus":
        flow_syllabus(resume_from=args.resume_from)
    elif args.flow == "all":
        flow_ctdt()
        flow_syllabus()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
