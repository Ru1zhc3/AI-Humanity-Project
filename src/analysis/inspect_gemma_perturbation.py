from pathlib import Path
import sys

import pandas as pd

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


folder = Path(__file__).resolve().parents[2] / "results" / "gemma4" / "local_perturbation_results"
rows = []
lean_counts = {}
for path in sorted(folder.glob("*.xlsx")):
    xl = pd.ExcelFile(path)
    total = 0
    non_null = 0
    for sheet in xl.sheet_names:
        df = pd.read_excel(path, sheet_name=sheet)
        total += len(df)
        if "model_response" in df:
            non_null += df["model_response"].notna().sum()
            first_line = df["model_response"].dropna().astype(str).str.split("\n").str[0]
            for value, count in first_line.value_counts().items():
                lean_counts[value] = lean_counts.get(value, 0) + int(count)
    rows.append((path.name, total, non_null, len(xl.sheet_names), xl.sheet_names))

print("FILES")
for row in rows:
    print(row)

print("\nLEAN FIRST LINES")
for value, count in sorted(lean_counts.items(), key=lambda item: item[1], reverse=True)[:220]:
    print(f"{count}\t{value}")
