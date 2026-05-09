from pathlib import Path

import pandas as pd


folder = Path(r"E:\CourseProject\cs4501_26spring_final_project\Evaluation Result\gemma4perturbation")
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
