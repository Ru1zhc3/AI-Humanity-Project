from __future__ import annotations

import math
import textwrap
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "results"
COMPARISON = BASE / "model_comparison"
OUT = BASE / "presentation" / "deep_presentation"
FIG = OUT / "figures"
TABLE = OUT / "tables"

LANGUAGE_ORDER = [
    "English",
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
    "English": "English",
    "Hindi": "Hindi",
    "Simplified Mandarin": "Mandarin",
    "French": "French",
    "Russian": "Russian",
    "Arabic": "Arabic",
    "Farsi": "Farsi",
    "Amharic": "Amharic",
    "Spain Spanish": "Spain Spanish",
    "Latin American Spanish": "LatAm Spanish",
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
    "Open Ended": "Open",
    "Yes-No Forced Choice": "Yes/No",
    "Presupposition Loading": "Presupp.",
    "Embedded": "Embedded",
    "Direct": "Direct",
    "Gain Framing": "Gain",
    "Loss Framing": "Loss",
    "Identity Change": "Identity",
    "Formal": "Formal",
    "Colloquial": "Colloq.",
    "Hedged": "Hedged",
    "Assertive": "Assertive",
}

MODEL_COLORS = {
    "Codex gpt-5.4-mini": "#2563EB",
    "Gemma 4": "#F59E0B",
}


def pct(value: float) -> float:
    return round(float(value) * 100, 2)


def ensure_dirs() -> None:
    FIG.mkdir(parents=True, exist_ok=True)
    TABLE.mkdir(parents=True, exist_ok=True)


def esc(text: object) -> str:
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def save_svg(name: str, width: int, height: int, body: str) -> None:
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">\n'
        '<rect width="100%" height="100%" fill="#F8FAFC"/>\n'
        f"{body}\n</svg>\n"
    )
    (FIG / name).write_text(svg, encoding="utf-8")


def txt(text: str, x: float, y: float, size: int = 14, fill: str = "#172033", weight: int = 400, anchor: str = "start") -> str:
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" font-family="Arial, sans-serif" '
        f'font-size="{size}" fill="{fill}" font-weight="{weight}" text-anchor="{anchor}">{esc(text)}</text>'
    )


def line_chart_svg(
    filename: str,
    title: str,
    subtitle: str,
    categories: list[str],
    series: dict[str, list[float]],
    y_label: str,
    ymax: float | None = None,
) -> None:
    width, height = 1180, 640
    left, top, chart_w, chart_h = 92, 142, 1010, 330
    ymax = ymax if ymax is not None else max(max(vals) for vals in series.values()) * 1.15
    ymax = max(10, math.ceil(ymax / 10) * 10)
    parts = [
        txt(title, 46, 58, 30, "#0F172A", 700),
        txt(subtitle, 48, 92, 16, "#475569"),
        txt(y_label, 44, 126, 13, "#64748B", 700),
    ]
    for tick in range(0, int(ymax) + 1, 10):
        y = top + chart_h - chart_h * tick / ymax
        parts.append(f'<line x1="{left}" y1="{y:.1f}" x2="{left + chart_w}" y2="{y:.1f}" stroke="#E2E8F0"/>')
        parts.append(txt(str(tick), left - 14, y + 4, 12, "#64748B", 400, "end"))
    x_step = chart_w / (len(categories) - 1)
    for i, label in enumerate(categories):
        x = left + i * x_step
        parts.append(f'<line x1="{x:.1f}" y1="{top + chart_h}" x2="{x:.1f}" y2="{top + chart_h + 5}" stroke="#94A3B8"/>')
        wrapped = textwrap.wrap(label, width=10)
        for j, line in enumerate(wrapped[:2]):
            parts.append(txt(line, x, top + chart_h + 24 + j * 14, 11, "#475569", 400, "middle"))
    for model, vals in series.items():
        color = MODEL_COLORS[model]
        points = []
        for i, val in enumerate(vals):
            x = left + i * x_step
            y = top + chart_h - chart_h * val / ymax
            points.append((x, y, val))
        d = " ".join(f"{x:.1f},{y:.1f}" for x, y, _ in points)
        parts.append(f'<polyline points="{d}" fill="none" stroke="{color}" stroke-width="4" stroke-linejoin="round" stroke-linecap="round"/>')
        for x, y, val in points:
            parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="#F8FAFC" stroke="{color}" stroke-width="3"/>')
        for x, y, val in points:
            if val >= 1:
                parts.append(txt(f"{val:.0f}", x, y - 10, 10, color, 700, "middle"))
    legend_x = 820
    for i, model in enumerate(series):
        y = 55 + i * 28
        parts.append(f'<rect x="{legend_x}" y="{y - 14}" width="22" height="5" rx="2.5" fill="{MODEL_COLORS[model]}"/>')
        parts.append(txt(model, legend_x + 32, y - 8, 14, "#334155", 700))
    save_svg(filename, width, height, "\n".join(parts))


def table_svg(summary: pd.DataFrame) -> None:
    width, height = 1160, 420
    parts = [
        txt("Deep outcomes summary", 46, 58, 30, "#0F172A", 700),
        txt("Translation and perturbation effects are measured as shifted political-lean rates.", 48, 92, 16, "#475569"),
    ]
    headers = ["Dimension", "Codex gpt-5.4-mini", "Gemma 4", "Interpretation"]
    rows = [
        [
            "Translation average shift",
            f'{summary.loc["Codex gpt-5.4-mini", "translation_avg_shift_pct"]:.1f}%',
            f'{summary.loc["Gemma 4", "translation_avg_shift_pct"]:.1f}%',
            "How often non-English lean differs from English baseline.",
        ],
        [
            "Largest language effect",
            f'{summary.loc["Codex gpt-5.4-mini", "translation_max_language"]} ({summary.loc["Codex gpt-5.4-mini", "translation_max_shift_pct"]:.1f}%)',
            f'{summary.loc["Gemma 4", "translation_max_language"]} ({summary.loc["Gemma 4", "translation_max_shift_pct"]:.1f}%)',
            "Languages where translation most changes lean.",
        ],
        [
            "Perturbation average shift",
            f'{summary.loc["Codex gpt-5.4-mini", "perturbation_avg_shift_pct"]:.1f}%',
            f'{summary.loc["Gemma 4", "perturbation_avg_shift_pct"]:.1f}%',
            "How often a perturbation deviates from its local majority lean.",
        ],
        [
            "Largest perturbation effect",
            f'{summary.loc["Codex gpt-5.4-mini", "perturbation_max_type"]} ({summary.loc["Codex gpt-5.4-mini", "perturbation_max_shift_pct"]:.1f}%)',
            f'{summary.loc["Gemma 4", "perturbation_max_type"]} ({summary.loc["Gemma 4", "perturbation_max_shift_pct"]:.1f}%)',
            "Prompt forms most likely to flip political lean.",
        ],
    ]
    x0, y0 = 46, 124
    col_w = [225, 230, 230, 390]
    row_h = 54
    parts.append(f'<rect x="{x0}" y="{y0}" width="{sum(col_w)}" height="{row_h}" rx="8" fill="#E2E8F0"/>')
    x = x0
    for header, w in zip(headers, col_w):
        parts.append(txt(header, x + 14, y0 + 34, 14, "#0F172A", 700))
        x += w
    for i, row in enumerate(rows):
        y = y0 + (i + 1) * row_h
        parts.append(f'<rect x="{x0}" y="{y}" width="{sum(col_w)}" height="{row_h}" fill="{"#FFFFFF" if i % 2 == 0 else "#F1F5F9"}" stroke="#CBD5E1"/>')
        x = x0
        for value, w in zip(row, col_w):
            lines = textwrap.wrap(value, width=max(14, int(w / 8.5)))[:2]
            for j, line in enumerate(lines):
                parts.append(txt(line, x + 14, y + 22 + j * 15, 12.5, "#334155", 700 if w <= 230 and j == 0 else 400))
            x += w
    save_svg("deep_outcomes_summary_table.svg", width, height, "\n".join(parts))


def main() -> None:
    ensure_dirs()
    df = pd.read_csv(COMPARISON / "tables" / "combined_model_political_lean_rows.csv")
    df = df[df["political_lean"].notna()].copy()

    final = df[df["dataset"] == "Final statements"].copy()
    pivot = final.pivot_table(
        index=["model", "statement_id"],
        columns="language",
        values="political_lean",
        aggfunc="first",
    )
    language_rows = []
    for model, model_pivot in pivot.groupby(level=0):
        english = model_pivot["English"]
        for language in LANGUAGE_ORDER:
            if language not in model_pivot.columns:
                continue
            shifted = model_pivot[language] != english
            language_rows.append(
                {
                    "model": model,
                    "language": language,
                    "records": int(shifted.notna().sum()),
                    "shifted_lean_rate_pct": pct(shifted.mean()),
                }
            )
    language_shift = pd.DataFrame(language_rows)
    language_shift.to_csv(TABLE / "language_translation_shift_from_english.csv", index=False, encoding="utf-8-sig")

    pert = df[df["dataset"] == "Perturbations"].copy()
    majority = (
        pert.groupby(["model", "language", "statement_id"])["political_lean"]
        .agg(lambda s: s.value_counts().index[0])
        .rename("majority_lean")
        .reset_index()
    )
    pert = pert.merge(majority, on=["model", "language", "statement_id"], how="left")
    pert["shifted_from_majority"] = pert["political_lean"] != pert["majority_lean"]
    perturbation_shift = (
        pert.groupby(["model", "perturbation"], as_index=False)
        .agg(records=("shifted_from_majority", "size"), shifted_lean_rate_pct=("shifted_from_majority", lambda s: pct(s.mean())))
    )
    perturbation_shift["perturbation"] = pd.Categorical(
        perturbation_shift["perturbation"],
        categories=PERTURBATION_ORDER,
        ordered=True,
    )
    perturbation_shift = perturbation_shift.sort_values(["model", "perturbation"])
    perturbation_shift.to_csv(TABLE / "perturbation_shift_from_majority.csv", index=False, encoding="utf-8-sig")

    summary_rows = []
    for model in ["Codex gpt-5.4-mini", "Gemma 4"]:
        lang_non_english = language_shift[(language_shift["model"] == model) & (language_shift["language"] != "English")]
        pert_model = perturbation_shift[perturbation_shift["model"] == model]
        max_lang = lang_non_english.loc[lang_non_english["shifted_lean_rate_pct"].idxmax()]
        min_lang = lang_non_english.loc[lang_non_english["shifted_lean_rate_pct"].idxmin()]
        max_pert = pert_model.loc[pert_model["shifted_lean_rate_pct"].idxmax()]
        min_pert = pert_model.loc[pert_model["shifted_lean_rate_pct"].idxmin()]
        summary_rows.append(
            {
                "model": model,
                "translation_avg_shift_pct": round(lang_non_english["shifted_lean_rate_pct"].mean(), 2),
                "translation_max_language": max_lang["language"],
                "translation_max_shift_pct": max_lang["shifted_lean_rate_pct"],
                "translation_min_language": min_lang["language"],
                "translation_min_shift_pct": min_lang["shifted_lean_rate_pct"],
                "perturbation_avg_shift_pct": round(pert_model["shifted_lean_rate_pct"].mean(), 2),
                "perturbation_max_type": max_pert["perturbation"],
                "perturbation_max_shift_pct": max_pert["shifted_lean_rate_pct"],
                "perturbation_min_type": min_pert["perturbation"],
                "perturbation_min_shift_pct": min_pert["shifted_lean_rate_pct"],
            }
        )
    summary = pd.DataFrame(summary_rows).set_index("model")
    summary.to_csv(TABLE / "deep_outcome_metric_summary.csv", encoding="utf-8-sig")

    lang_series = {}
    for model in ["Codex gpt-5.4-mini", "Gemma 4"]:
        subset = language_shift[language_shift["model"] == model].set_index("language")
        lang_series[model] = [float(subset.loc[language, "shifted_lean_rate_pct"]) for language in LANGUAGE_ORDER]
    line_chart_svg(
        "language_translation_shift_line.svg",
        "Translation effect: shifted political lean by language",
        "Shifted lean = label differs from the same model's English baseline for the same source statement.",
        [LANGUAGE_LABELS[l] for l in LANGUAGE_ORDER],
        lang_series,
        "Shifted lean rate (%)",
        ymax=80,
    )

    pert_series = {}
    for model in ["Codex gpt-5.4-mini", "Gemma 4"]:
        subset = perturbation_shift[perturbation_shift["model"] == model].set_index("perturbation")
        pert_series[model] = [float(subset.loc[p, "shifted_lean_rate_pct"]) for p in PERTURBATION_ORDER]
    line_chart_svg(
        "perturbation_shift_line.svg",
        "Perturbation effect: shifted political lean by prompt variant",
        "Shifted lean = label differs from the majority lean for the same model, language, and source statement.",
        [PERTURBATION_LABELS[p] for p in PERTURBATION_ORDER],
        pert_series,
        "Shifted lean rate (%)",
        ymax=60,
    )
    table_svg(summary)

    md = f"""# Deep Presentation Analysis

## Definitions

- **Shifted lean** means the model changed the political-compass label (`Auth-Left`, `Auth-Right`, `Centrist`, `Lib-Left`, `Lib-Right`) for the same underlying statement.
- **Translation shifted lean** compares each translated statement to the same model's English label.
- **Perturbation shifted lean** compares each perturbation to the majority label across all perturbations for the same model, language, and source statement.
- **Controversy** is the model's 1-5 rating of how politically/socially contentious the statement is. It is not the model's agreement with the statement.

## Deeper Outcomes

1. **Language has directional effects, not just random noise.** Codex is most shifted by `{summary.loc["Codex gpt-5.4-mini", "translation_max_language"]}` (`{summary.loc["Codex gpt-5.4-mini", "translation_max_shift_pct"]:.1f}%`) and least shifted by `{summary.loc["Codex gpt-5.4-mini", "translation_min_language"]}` (`{summary.loc["Codex gpt-5.4-mini", "translation_min_shift_pct"]:.1f}%`). Gemma is most shifted by `{summary.loc["Gemma 4", "translation_max_language"]}` (`{summary.loc["Gemma 4", "translation_max_shift_pct"]:.1f}%`) and least shifted by `{summary.loc["Gemma 4", "translation_min_language"]}` (`{summary.loc["Gemma 4", "translation_min_shift_pct"]:.1f}%`).
2. **Perturbation effects are uneven.** Codex average perturbation shift is `{summary.loc["Codex gpt-5.4-mini", "perturbation_avg_shift_pct"]:.1f}%`; max is `{summary.loc["Codex gpt-5.4-mini", "perturbation_max_type"]}` (`{summary.loc["Codex gpt-5.4-mini", "perturbation_max_shift_pct"]:.1f}%`) and min is `{summary.loc["Codex gpt-5.4-mini", "perturbation_min_type"]}` (`{summary.loc["Codex gpt-5.4-mini", "perturbation_min_shift_pct"]:.1f}%`). Gemma average perturbation shift is `{summary.loc["Gemma 4", "perturbation_avg_shift_pct"]:.1f}%`; max is `{summary.loc["Gemma 4", "perturbation_max_type"]}` (`{summary.loc["Gemma 4", "perturbation_max_shift_pct"]:.1f}%`) and min is `{summary.loc["Gemma 4", "perturbation_min_type"]}` (`{summary.loc["Gemma 4", "perturbation_min_shift_pct"]:.1f}%`).
3. **Model behavior differs.** Gemma has higher translation shift (`{summary.loc["Gemma 4", "translation_avg_shift_pct"]:.1f}%`) than Codex (`{summary.loc["Codex gpt-5.4-mini", "translation_avg_shift_pct"]:.1f}%`), and higher perturbation shift (`{summary.loc["Gemma 4", "perturbation_avg_shift_pct"]:.1f}%`) than Codex (`{summary.loc["Codex gpt-5.4-mini", "perturbation_avg_shift_pct"]:.1f}%`).

## Possible Reasons To Present

- Languages with greater translation shift may carry stronger contextual or cultural cues in political vocabulary, or the model may have less balanced training coverage for that language.
- Codex often moves between `Centrist` and `Lib-Left`, suggesting more moderation-style recoding. Gemma tends to show stronger label movement overall, suggesting higher sensitivity to translated wording and prompt form.
- Perturbations that add assumptions or change pragmatics, such as presupposition loading, open-ended framing, and loss framing, are more likely to change the political-lean label because they alter what the model treats as the implied policy stance.

## Generated Figures

- `figures/language_translation_shift_line.svg`
- `figures/perturbation_shift_line.svg`
- `figures/deep_outcomes_summary_table.svg`

## Generated Tables

- `tables/language_translation_shift_from_english.csv`
- `tables/perturbation_shift_from_majority.csv`
- `tables/deep_outcome_metric_summary.csv`
"""
    (OUT / "deep_presentation_summary.md").write_text(md, encoding="utf-8")


if __name__ == "__main__":
    main()
