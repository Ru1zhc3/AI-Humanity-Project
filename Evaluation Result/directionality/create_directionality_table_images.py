from __future__ import annotations

import html
import math
from pathlib import Path

import pandas as pd


BASE = Path(r"E:\CourseProject\cs4501_26spring_final_project\Evaluation Result\directionality")
OUT = BASE / "figures"
OUT.mkdir(exist_ok=True)

MODEL_LABELS = {
    "Codex gpt-5.4-mini": "GPT-5.4-mini",
    "Gemma 4": "Gemma 4 e4b",
}

LANGUAGE_ORDER = [
    "Hindi",
    "Simplified Mandarin",
    "French",
    "Russian",
    "Arabic",
    "Farsi",
    "Amharic",
    "Spain Spanish",
    "Latin American Spanish",
]

LANGUAGE_LABELS = {
    "Hindi": "Hindi",
    "Simplified Mandarin": "Mandarin",
    "French": "French",
    "Russian": "Russian",
    "Arabic": "Arabic",
    "Farsi": "Farsi",
    "Amharic": "Amharic",
    "Spain Spanish": "Spain\nSpanish",
    "Latin American Spanish": "LatAm\nSpanish",
}

PERTURBATION_ORDER = [
    "Active Voice",
    "Passive Voice",
    "Open Ended",
    "Yes-No Forced Choice",
    "Presupposition Loading",
    "Embedded",
    "Direct",
    "Gain Framing",
    "Loss Framing",
    "Identity Change",
    "Formal",
    "Colloquial",
    "Hedged",
    "Assertive",
]

PERTURBATION_LABELS = {
    "Active Voice": "Active",
    "Passive Voice": "Passive",
    "Open Ended": "Open\nEnded",
    "Yes-No Forced Choice": "Yes-No\nForced",
    "Presupposition Loading": "Presupp.\nLoading",
    "Embedded": "Embedded",
    "Direct": "Direct",
    "Gain Framing": "Gain\nFraming",
    "Loss Framing": "Loss\nFraming",
    "Identity Change": "Identity\nChange",
    "Formal": "Formal",
    "Colloquial": "Colloquial",
    "Hedged": "Hedged",
    "Assertive": "Assertive",
}

LEAN_COLORS = {
    "Auth-Left": "#7C3AED",
    "Auth-Right": "#DC2626",
    "Centrist": "#64748B",
    "Lib-Left": "#2563EB",
    "Lib-Right": "#16A34A",
}


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def text_lines(text: str) -> list[str]:
    return str(text).split("\n")


def add_text(parts: list[str], text: str, x: float, y: float, size: int, color: str = "#172033", weight: int = 400, anchor: str = "middle") -> None:
    lines = text_lines(text)
    for i, line in enumerate(lines):
        parts.append(
            f'<text x="{x:.1f}" y="{y + i * size * 1.12:.1f}" font-family="Arial, sans-serif" '
            f'font-size="{size}" fill="{color}" font-weight="{weight}" text-anchor="{anchor}">{esc(line)}</text>'
        )


def make_cell_text(row: pd.Series) -> str:
    lean = row["dominant_shifted_to_lean"]
    pct = float(row["dominant_shifted_to_pct_of_shifted"])
    return f"{lean}\n{pct:.1f}% of shifts"


def render_table(
    *,
    filename: str,
    df: pd.DataFrame,
    columns: list[str],
    column_labels: dict[str, str],
    key_col: str,
    cell_w: int,
) -> None:
    models = ["Codex gpt-5.4-mini", "Gemma 4"]
    left_w = 132
    header_h = 64
    row_h = 72
    # Place the outer stroke on the canvas edge so there is no visible whitespace
    # outside the table border in the exported slide image.
    x0 = 1
    y0 = 1
    total_w = left_w + cell_w * len(columns)
    total_h = header_h + row_h * len(models)
    width = total_w + x0 * 2
    height = total_h + y0 * 2
    bg = "#f1f9f3"
    border = "#8FA99A"
    grid = "#B8CDBF"
    parts: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        f'<rect width="100%" height="100%" fill="{bg}"/>',
    ]
    parts.append(f'<rect x="{x0}" y="{y0}" width="{total_w}" height="{total_h}" fill="#FFFFFF" stroke="{border}" stroke-width="2"/>')
    parts.append(f'<rect x="{x0}" y="{y0}" width="{total_w}" height="{header_h}" fill="{bg}" stroke="{border}" stroke-width="2"/>')
    parts.append(f'<rect x="{x0}" y="{y0 + header_h + row_h}" width="{total_w}" height="{row_h}" fill="{bg}"/>')
    parts.append(f'<line x1="{x0}" y1="{y0 + header_h}" x2="{x0 + total_w}" y2="{y0 + header_h}" stroke="{border}" stroke-width="2"/>')
    parts.append(f'<line x1="{x0}" y1="{y0 + header_h + row_h}" x2="{x0 + total_w}" y2="{y0 + header_h + row_h}" stroke="{border}" stroke-width="1.5"/>')

    for i, col in enumerate(columns):
        cx = x0 + left_w + i * cell_w + cell_w / 2
        label = column_labels[col]
        label_y = y0 + (27 if "\n" in label else 39)
        add_text(parts, label, cx, label_y, 11.7, "#23372D", 800)
        parts.append(f'<line x1="{x0 + left_w + i * cell_w}" y1="{y0}" x2="{x0 + left_w + i * cell_w}" y2="{y0 + total_h}" stroke="{grid}" stroke-width="1.2"/>')
    parts.append(f'<line x1="{x0 + left_w}" y1="{y0}" x2="{x0 + left_w}" y2="{y0 + total_h}" stroke="{border}" stroke-width="2"/>')

    for r, model in enumerate(models):
        y = y0 + header_h + r * row_h
        add_text(parts, MODEL_LABELS[model], x0 + left_w / 2, y + 42, 13, "#172033", 700)
        model_df = df[df["model"] == model].set_index(key_col)
        for i, col in enumerate(columns):
            cx = x0 + left_w + i * cell_w + cell_w / 2
            row = model_df.loc[col]
            lean = str(row["dominant_shifted_to_lean"])
            color = LEAN_COLORS.get(lean, "#64748B")
            parts.append(
                f'<rect x="{cx - cell_w / 2 + 6:.1f}" y="{y + 12}" width="{cell_w - 12}" height="48" '
                f'rx="8" fill="{color}16" stroke="{color}8A" stroke-width="1.4"/>'
            )
            add_text(parts, lean, cx, y + 32, 9.8, color, 700)
            add_text(parts, f'{float(row["dominant_shifted_to_pct_of_shifted"]):.1f}% of shifts', cx, y + 48, 7.9, "#334155", 700)
    parts.append("</svg>")
    (OUT / filename).write_text("\n".join(parts), encoding="utf-8")


def main() -> None:
    language = pd.read_csv(BASE / "language_directionality_by_model.csv")
    perturbation = pd.read_csv(BASE / "perturbation_directionality_by_model.csv")

    render_table(
        filename="translation_directionality_table.svg",
        df=language,
        columns=LANGUAGE_ORDER,
        column_labels=LANGUAGE_LABELS,
        key_col="language",
        cell_w=102,
    )
    render_table(
        filename="perturbation_directionality_table.svg",
        df=perturbation,
        columns=PERTURBATION_ORDER,
        column_labels=PERTURBATION_LABELS,
        key_col="perturbation",
        cell_w=84,
    )


if __name__ == "__main__":
    main()
