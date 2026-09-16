import pandas as pd
import sys
from pathlib import Path

try:
    xl = pd.ExcelFile(Path(__file__).resolve().parent.parent / 'data/thucthe_quanhe_pipeline_v2.xlsx')
    sheet_name = xl.sheet_names[-1]
    df = xl.parse(sheet_name)
    with open(Path(__file__).resolve().parent.parent / 'docs/sheet4.md', 'w', encoding='utf-8') as f:
        f.write(df.to_markdown())
    print("Success")
except Exception as e:
    print("Error:", e)
    sys.exit(1)
