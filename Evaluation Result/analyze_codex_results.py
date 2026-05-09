import json
from html import escape
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(r"E:\CourseProject\cs4501_26spring_final_project")
OUT = ROOT / "Evaluation Result"
FIGS = OUT / "figures"
TABLES = OUT / "tables"

FINAL_CHECKPOINT = (
    ROOT
    / "Evaluation"
    / "codex_outputs"
    / "final_multilingual_full_gpt_5_4_mini"
    / "codex_final_multilingual_checkpoint.json"
)
PERT_CHECKPOINT = (
    ROOT
    / "Evaluation"
    / "codex_outputs"
    / "perturbation_full_gpt_5_4_mini"
    / "codex_workbook_eval_checkpoint.json"
)
PERT_RESULTS_CSV = (
    ROOT
    / "Evaluation"
    / "codex_outputs"
    / "perturbation_full_gpt_5_4_mini"
    / "codex_workbook_eval_results.csv"
)

LEAN_ORDER = ["Auth-Left", "Auth-Right", "Centrist", "Lib-Left", "Lib-Right"]
LANG_ORDER_FINAL = [
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
LANG_ORDER_PERT = [
    "English",
    "Arabic",
    "Farsi",
    "French",
    "Hindi",
    "Latin American Spanish",
    "Russian",
    "Simplified Mandarin",
    "Spain Spanish",
]
SHEET_ORDER = [
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


def ensure_dirs():
    FIGS.mkdir(parents=True, exist_ok=True)
    TABLES.mkdir(parents=True, exist_ok=True)


def load_checkpoint(path: Path) -> pd.DataFrame:
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = list(payload["results"].values())
    df = pd.DataFrame(rows)
    df["controversy_score_1_5"] = pd.to_numeric(df["controversy_score_1_5"], errors="coerce")
    df["reference_match"] = df["quadrant"] == df["codex_political_lean"]
    return df


def load_results_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, encoding="utf-8")
    df["row_id"] = df["row_id"].astype(str)
    df["controversy_score_1_5"] = pd.to_numeric(df["controversy_score_1_5"], errors="coerce")
    df["reference_match"] = df["quadrant"] == df["codex_political_lean"]
    return df


def pct(series: pd.Series) -> float:
    return float(series.mean() * 100) if len(series) else float("nan")


def entropy(values: pd.Series) -> float:
    counts = values.value_counts(normalize=True)
    return float(-(counts * np.log2(counts)).sum()) if len(counts) else 0.0


def save_csv(df: pd.DataFrame, name: str):
    df.to_csv(TABLES / name, index=False, encoding="utf-8-sig")


def md_table(df: pd.DataFrame, columns: list[str], max_rows: int | None = None) -> str:
    display = df[columns].copy()
    if max_rows:
        display = display.head(max_rows)
    rows = [columns]
    for _, row in display.iterrows():
        rows.append([row.get(col, "") for col in columns])
    widths = [max(len(str(r[i])) for r in rows) for i in range(len(columns))]
    lines = []
    header = "| " + " | ".join(str(rows[0][i]).ljust(widths[i]) for i in range(len(columns))) + " |"
    sep = "| " + " | ".join("-" * widths[i] for i in range(len(columns))) + " |"
    lines.extend([header, sep])
    for row in rows[1:]:
        lines.append("| " + " | ".join(str(row[i]).ljust(widths[i]) for i in range(len(columns))) + " |")
    return "\n".join(lines)


def rgb_to_hex(rgb):
    return "#" + "".join(f"{max(0, min(255, int(v))):02x}" for v in rgb)


def lerp_color(value, vmin, vmax, low=(244, 249, 248), high=(47, 111, 115)):
    if np.isnan(value):
        return "#f0f0f0"
    t = 0 if vmax == vmin else (value - vmin) / (vmax - vmin)
    t = max(0, min(1, t))
    return rgb_to_hex([low[i] + (high[i] - low[i]) * t for i in range(3)])


def write_svg(path: Path, width: int, height: int, body: str):
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">\n'
        '<style>text{font-family:Arial,Helvetica,sans-serif;} .small{font-size:11px;} '
        '.label{font-size:12px;} .title{font-size:18px;font-weight:bold;} '
        '.axis{stroke:#333;stroke-width:1;} .grid{stroke:#ddd;stroke-width:1;}</style>\n'
        f"{body}\n</svg>\n"
    )
    path.write_text(svg, encoding="utf-8")


def text(x, y, value, cls="label", anchor="middle", rotate=None, fill="#111"):
    value = escape(str(value))
    transform = f' transform="rotate({rotate} {x} {y})"' if rotate is not None else ""
    return f'<text x="{x}" y="{y}" class="{cls}" text-anchor="{anchor}" fill="{fill}"{transform}>{value}</text>'


def bar_chart(path, title, labels, values, ylabel, color="#2f6f73", ymax=None):
    width, height = 1000, 520
    left, right, top, bottom = 80, 30, 60, 150
    plot_w, plot_h = width - left - right, height - top - bottom
    ymax = ymax or max(values) * 1.15
    body = [text(width / 2, 30, title, "title")]
    body.append(f'<line x1="{left}" y1="{top+plot_h}" x2="{left+plot_w}" y2="{top+plot_h}" class="axis"/>')
    body.append(f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top+plot_h}" class="axis"/>')
    for tick in np.linspace(0, ymax, 5):
        y = top + plot_h - (tick / ymax) * plot_h
        body.append(f'<line x1="{left}" y1="{y:.1f}" x2="{left+plot_w}" y2="{y:.1f}" class="grid"/>')
        body.append(text(left - 8, y + 4, f"{tick:.0f}", "small", "end"))
    bar_gap = 8
    bar_w = max(8, (plot_w - bar_gap * (len(values) + 1)) / len(values))
    for i, (label, value) in enumerate(zip(labels, values)):
        x = left + bar_gap + i * (bar_w + bar_gap)
        bar_h = (value / ymax) * plot_h
        y = top + plot_h - bar_h
        body.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="{bar_h:.1f}" fill="{color}"/>')
        body.append(text(x + bar_w / 2, y - 5, f"{value:.1f}", "small"))
        body.append(text(x + bar_w / 2, top + plot_h + 18, label, "small", rotate=38))
    body.append(text(20, top + plot_h / 2, ylabel, "label", rotate=-90))
    write_svg(path, width, height, "\n".join(body))


def bar_line_chart(path, title, labels, bar_values, line_values, bar_label, line_label, bar_ymax=100, line_min=1, line_max=5):
    width, height = 1200, 560
    left, right, top, bottom = 80, 80, 60, 155
    plot_w, plot_h = width - left - right, height - top - bottom
    body = [text(width / 2, 30, title, "title")]
    body.append(f'<line x1="{left}" y1="{top+plot_h}" x2="{left+plot_w}" y2="{top+plot_h}" class="axis"/>')
    body.append(f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top+plot_h}" class="axis"/>')
    body.append(f'<line x1="{left+plot_w}" y1="{top}" x2="{left+plot_w}" y2="{top+plot_h}" class="axis"/>')
    for tick in np.linspace(0, bar_ymax, 5):
        y = top + plot_h - (tick / bar_ymax) * plot_h
        body.append(f'<line x1="{left}" y1="{y:.1f}" x2="{left+plot_w}" y2="{y:.1f}" class="grid"/>')
        body.append(text(left - 8, y + 4, f"{tick:.0f}", "small", "end"))
    for tick in np.linspace(line_min, line_max, 5):
        y = top + plot_h - ((tick - line_min) / (line_max - line_min)) * plot_h
        body.append(text(left + plot_w + 8, y + 4, f"{tick:.1f}", "small", "start"))
    gap = 8
    bar_w = max(8, (plot_w - gap * (len(labels) + 1)) / len(labels))
    points = []
    for i, label in enumerate(labels):
        x = left + gap + i * (bar_w + gap)
        bar_h = (bar_values[i] / bar_ymax) * plot_h
        y = top + plot_h - bar_h
        body.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="{bar_h:.1f}" fill="#2f6f73"/>')
        cx = x + bar_w / 2
        ly = top + plot_h - ((line_values[i] - line_min) / (line_max - line_min)) * plot_h
        points.append((cx, ly))
        body.append(text(cx, top + plot_h + 18, label, "small", rotate=38))
    poly = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
    body.append(f'<polyline points="{poly}" fill="none" stroke="#d1495b" stroke-width="3"/>')
    for x, y in points:
        body.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="#d1495b"/>')
    body.append(f'<rect x="{left+10}" y="{top+10}" width="14" height="14" fill="#2f6f73"/>')
    body.append(text(left + 30, top + 22, bar_label, "small", "start"))
    body.append(f'<line x1="{left+10}" y1="{top+40}" x2="{left+24}" y2="{top+40}" stroke="#d1495b" stroke-width="3"/>')
    body.append(text(left + 30, top + 44, line_label, "small", "start"))
    write_svg(path, width, height, "\n".join(body))


def heatmap(path, title, df, vmin=0, vmax=100, suffix="", one_decimal=False, high=(47, 111, 115)):
    cell_w, cell_h = 74, 34
    left, top, right, bottom = 180, 60, 30, 130
    width = left + cell_w * len(df.columns) + right
    height = top + cell_h * len(df.index) + bottom
    body = [text(width / 2, 30, title, "title")]
    data = df.to_numpy(dtype=float)
    for i, row_label in enumerate(df.index):
        y = top + i * cell_h
        body.append(text(left - 10, y + cell_h / 2 + 4, row_label, "small", "end"))
        for j, col_label in enumerate(df.columns):
            x = left + j * cell_w
            val = data[i, j]
            color = lerp_color(val, vmin, vmax, high=high)
            body.append(f'<rect x="{x}" y="{y}" width="{cell_w}" height="{cell_h}" fill="{color}" stroke="#fff"/>')
            label = "" if np.isnan(val) else (f"{val:.1f}{suffix}" if one_decimal else f"{val:.0f}{suffix}")
            body.append(text(x + cell_w / 2, y + cell_h / 2 + 4, label, "small"))
    for j, col_label in enumerate(df.columns):
        x = left + j * cell_w + cell_w / 2
        body.append(text(x, top + cell_h * len(df.index) + 18, col_label, "small", rotate=35))
    write_svg(path, width, height, "\n".join(body))


def grouped_bar(path, title, labels, series_a, series_b, label_a, label_b, ymax=100):
    width, height = 1200, 560
    left, right, top, bottom = 80, 30, 60, 160
    plot_w, plot_h = width - left - right, height - top - bottom
    body = [text(width / 2, 30, title, "title")]
    body.append(f'<line x1="{left}" y1="{top+plot_h}" x2="{left+plot_w}" y2="{top+plot_h}" class="axis"/>')
    body.append(f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top+plot_h}" class="axis"/>')
    for tick in np.linspace(0, ymax, 5):
        y = top + plot_h - (tick / ymax) * plot_h
        body.append(f'<line x1="{left}" y1="{y:.1f}" x2="{left+plot_w}" y2="{y:.1f}" class="grid"/>')
        body.append(text(left - 8, y + 4, f"{tick:.0f}", "small", "end"))
    group_gap = 10
    group_w = (plot_w - group_gap * (len(labels) + 1)) / len(labels)
    bar_w = group_w / 2 - 2
    for i, label in enumerate(labels):
        gx = left + group_gap + i * (group_w + group_gap)
        for k, value in enumerate([series_a[i], series_b[i]]):
            color = "#2f6f73" if k == 0 else "#d1495b"
            x = gx + k * (bar_w + 4)
            bar_h = (value / ymax) * plot_h
            y = top + plot_h - bar_h
            body.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="{bar_h:.1f}" fill="{color}"/>')
        body.append(text(gx + group_w / 2, top + plot_h + 18, label, "small", rotate=38))
    body.append(f'<rect x="{left+10}" y="{top+10}" width="14" height="14" fill="#2f6f73"/>')
    body.append(text(left + 30, top + 22, label_a, "small", "start"))
    body.append(f'<rect x="{left+10}" y="{top+35}" width="14" height="14" fill="#d1495b"/>')
    body.append(text(left + 30, top + 47, label_b, "small", "start"))
    write_svg(path, width, height, "\n".join(body))


def language_summary(df: pd.DataFrame, lang_order: list[str]) -> pd.DataFrame:
    grouped = (
        df.groupby("language")
        .agg(
            records=("record_id", "count"),
            success=("status", lambda s: int((s == "success").sum())),
            error=("status", lambda s: int((s == "error").sum())),
            reference_match_rate_pct=("reference_match", pct),
            avg_controversy=("controversy_score_1_5", "mean"),
            std_controversy=("controversy_score_1_5", "std"),
            lean_entropy=("codex_political_lean", entropy),
        )
        .reindex(lang_order)
        .reset_index()
    )
    grouped["dominant_codex_lean"] = [
        df[df["language"] == lang]["codex_political_lean"].mode().iloc[0]
        if len(df[df["language"] == lang]) and not df[df["language"] == lang]["codex_political_lean"].mode().empty
        else ""
        for lang in grouped["language"]
    ]
    return grouped.round(
        {
            "reference_match_rate_pct": 2,
            "avg_controversy": 3,
            "std_controversy": 3,
            "lean_entropy": 3,
        }
    )


def lean_distribution(df: pd.DataFrame, lang_order: list[str]) -> pd.DataFrame:
    pivot = pd.crosstab(df["language"], df["codex_political_lean"], normalize="index") * 100
    return pivot.reindex(index=lang_order, columns=LEAN_ORDER).fillna(0).round(2)


def make_overview(final_df: pd.DataFrame, pert_df: pd.DataFrame) -> pd.DataFrame:
    overview = pd.DataFrame(
        [
            {
                "result_set": "final multilingual statements",
                "records": len(final_df),
                "languages": final_df["language"].nunique(),
                "source_statements": final_df["row_id"].nunique(),
                "framing_variants": 1,
                "success": int((final_df["status"] == "success").sum()),
                "error": int((final_df["status"] == "error").sum()),
                "reference_match_rate_pct": pct(final_df["reference_match"]),
                "avg_controversy": final_df["controversy_score_1_5"].mean(),
            },
            {
                "result_set": "perturbation statements",
                "records": len(pert_df),
                "languages": pert_df["language"].nunique(),
                "source_statements": pert_df["row_id"].nunique(),
                "framing_variants": pert_df["sheet_name"].nunique(),
                "success": int((pert_df["status"] == "success").sum()),
                "error": int((pert_df["status"] == "error").sum()),
                "reference_match_rate_pct": pct(pert_df["reference_match"]),
                "avg_controversy": pert_df["controversy_score_1_5"].mean(),
            },
        ]
    ).round({"reference_match_rate_pct": 2, "avg_controversy": 3})
    save_csv(overview, "dataset_overview.csv")
    bar_chart(
        FIGS / "evaluation_coverage.svg",
        "Evaluation Coverage",
        overview["result_set"].tolist(),
        overview["records"].tolist(),
        "Evaluated records",
        ymax=max(overview["records"]) * 1.15,
    )
    return overview


def final_analyses(final_df: pd.DataFrame):
    final_lang = language_summary(final_df, LANG_ORDER_FINAL)
    final_dist = lean_distribution(final_df, LANG_ORDER_FINAL)
    final_category = (
        final_df.groupby("category")
        .agg(
            records=("record_id", "count"),
            reference_match_rate_pct=("reference_match", pct),
            avg_controversy=("controversy_score_1_5", "mean"),
            lean_entropy=("codex_political_lean", entropy),
        )
        .reset_index()
        .sort_values("avg_controversy", ascending=False)
        .round({"reference_match_rate_pct": 2, "avg_controversy": 3, "lean_entropy": 3})
    )
    final_quadrant = (
        final_df.groupby("quadrant")
        .agg(
            records=("record_id", "count"),
            reference_match_rate_pct=("reference_match", pct),
            avg_controversy=("controversy_score_1_5", "mean"),
        )
        .reindex(LEAN_ORDER)
        .reset_index()
        .round({"reference_match_rate_pct": 2, "avg_controversy": 3})
    )
    final_row_stability = (
        final_df.groupby("row_id")
        .agg(
            category=("category", "first"),
            quadrant=("quadrant", "first"),
            unique_codex_leans=("codex_political_lean", "nunique"),
            lean_entropy=("codex_political_lean", entropy),
            controversy_range=("controversy_score_1_5", lambda s: float(s.max() - s.min())),
            avg_controversy=("controversy_score_1_5", "mean"),
        )
        .reset_index()
        .sort_values(["unique_codex_leans", "controversy_range", "lean_entropy"], ascending=False)
        .round({"lean_entropy": 3, "controversy_range": 3, "avg_controversy": 3})
    )
    save_csv(final_lang, "final_language_summary.csv")
    save_csv(final_dist.reset_index(), "final_codex_lean_distribution_by_language_pct.csv")
    save_csv(final_category, "final_category_summary.csv")
    save_csv(final_quadrant, "final_reference_quadrant_summary.csv")
    save_csv(final_row_stability.head(30), "final_top_cross_language_unstable_statements.csv")

    bar_line_chart(
        FIGS / "final_language_match_controversy.svg",
        "Final Statements: Reference Match and Controversy by Language",
        final_lang["language"].tolist(),
        final_lang["reference_match_rate_pct"].tolist(),
        final_lang["avg_controversy"].tolist(),
        "Reference match (%)",
        "Avg controversy",
    )
    heatmap(
        FIGS / "final_lean_distribution_heatmap.svg",
        "Final Statements: Codex Political Lean Distribution by Language (%)",
        final_dist,
        vmin=0,
        vmax=max(60, float(final_dist.to_numpy().max())),
        suffix="%",
    )
    counts = final_row_stability["unique_codex_leans"].value_counts().sort_index()
    bar_chart(
        FIGS / "final_cross_language_stability.svg",
        "Final Statements: Distinct Codex Leans Across 10 Languages",
        [str(x) for x in counts.index],
        counts.values.tolist(),
        "Number of source statements",
        color="#edae49",
        ymax=max(counts.values) * 1.2,
    )
    return {
        "final_lang": final_lang,
        "final_dist": final_dist,
        "final_category": final_category,
        "final_quadrant": final_quadrant,
        "final_row_stability": final_row_stability,
    }


def perturbation_analyses(pert_df: pd.DataFrame):
    pert_lang = language_summary(pert_df, LANG_ORDER_PERT)
    pert_dist = lean_distribution(pert_df, LANG_ORDER_PERT)
    pert_variation = (
        pert_df.groupby("sheet_name")
        .agg(
            records=("record_id", "count"),
            reference_match_rate_pct=("reference_match", pct),
            avg_controversy=("controversy_score_1_5", "mean"),
            std_controversy=("controversy_score_1_5", "std"),
            lean_entropy=("codex_political_lean", entropy),
        )
        .reindex(SHEET_ORDER)
        .reset_index()
        .round(
            {
                "reference_match_rate_pct": 2,
                "avg_controversy": 3,
                "std_controversy": 3,
                "lean_entropy": 3,
            }
        )
    )

    majority_map = {}
    stability_rows = []
    for (language, row_id), group in pert_df.groupby(["language", "row_id"]):
        majority = group["codex_political_lean"].mode().iloc[0]
        for record_id in group["record_id"]:
            majority_map[record_id] = majority
        stability_rows.append(
            {
                "language": language,
                "row_id": row_id,
                "category": group["category"].iloc[0],
                "quadrant": group["quadrant"].iloc[0],
                "unique_codex_leans_across_14_variations": group["codex_political_lean"].nunique(),
                "controversy_range_across_14_variations": float(
                    group["controversy_score_1_5"].max() - group["controversy_score_1_5"].min()
                ),
                "majority_lean": majority,
            }
        )
    pert_df = pert_df.copy()
    pert_df["language_row_majority_lean"] = pert_df["record_id"].map(majority_map)
    pert_df["differs_from_language_row_majority"] = (
        pert_df["codex_political_lean"] != pert_df["language_row_majority_lean"]
    )
    group_unique = pd.DataFrame(stability_rows)
    variation_majority = (
        pert_df.groupby("sheet_name")
        .agg(majority_deviation_rate_pct=("differs_from_language_row_majority", pct))
        .reindex(SHEET_ORDER)
        .reset_index()
        .round({"majority_deviation_rate_pct": 2})
    )
    pert_variation = pert_variation.merge(variation_majority, on="sheet_name", how="left")
    language_stability = (
        group_unique.groupby("language")
        .agg(
            source_statements=("row_id", "count"),
            pct_all_14_variations_same_lean=(
                "unique_codex_leans_across_14_variations",
                lambda s: float((s == 1).mean() * 100),
            ),
            avg_unique_leans_across_variations=("unique_codex_leans_across_14_variations", "mean"),
            avg_controversy_range_across_variations=("controversy_range_across_14_variations", "mean"),
        )
        .reindex(LANG_ORDER_PERT)
        .reset_index()
        .round(
            {
                "pct_all_14_variations_same_lean": 2,
                "avg_unique_leans_across_variations": 3,
                "avg_controversy_range_across_variations": 3,
            }
        )
    )
    category_summary = (
        pert_df.groupby("category")
        .agg(
            records=("record_id", "count"),
            reference_match_rate_pct=("reference_match", pct),
            avg_controversy=("controversy_score_1_5", "mean"),
            majority_deviation_rate_pct=("differs_from_language_row_majority", pct),
        )
        .reset_index()
        .sort_values("avg_controversy", ascending=False)
        .round(
            {
                "reference_match_rate_pct": 2,
                "avg_controversy": 3,
                "majority_deviation_rate_pct": 2,
            }
        )
    )
    cross_rows = []
    for (sheet_name, row_id), group in pert_df.groupby(["sheet_name", "row_id"]):
        cross_rows.append(
            {
                "sheet_name": sheet_name,
                "row_id": row_id,
                "category": group["category"].iloc[0],
                "quadrant": group["quadrant"].iloc[0],
                "unique_codex_leans_across_languages": group["codex_political_lean"].nunique(),
                "controversy_range_across_languages": float(
                    group["controversy_score_1_5"].max() - group["controversy_score_1_5"].min()
                ),
            }
        )
    cross_language = pd.DataFrame(cross_rows)
    cross_language_sheet = (
        cross_language.groupby("sheet_name")
        .agg(
            pct_all_languages_same_lean=(
                "unique_codex_leans_across_languages",
                lambda s: float((s == 1).mean() * 100),
            ),
            avg_unique_leans_across_languages=("unique_codex_leans_across_languages", "mean"),
            avg_controversy_range_across_languages=("controversy_range_across_languages", "mean"),
        )
        .reindex(SHEET_ORDER)
        .reset_index()
        .round(
            {
                "pct_all_languages_same_lean": 2,
                "avg_unique_leans_across_languages": 3,
                "avg_controversy_range_across_languages": 3,
            }
        )
    )
    controversy_heatmap = (
        pert_df.pivot_table(
            index="language",
            columns="sheet_name",
            values="controversy_score_1_5",
            aggfunc="mean",
        )
        .reindex(index=LANG_ORDER_PERT, columns=SHEET_ORDER)
        .round(2)
    )
    save_csv(pert_lang, "perturbation_language_summary.csv")
    save_csv(pert_dist.reset_index(), "perturbation_codex_lean_distribution_by_language_pct.csv")
    save_csv(pert_variation, "perturbation_variation_summary.csv")
    save_csv(language_stability, "perturbation_language_stability_across_variations.csv")
    save_csv(category_summary, "perturbation_category_summary.csv")
    save_csv(cross_language_sheet, "perturbation_cross_language_stability_by_variation.csv")
    save_csv(
        cross_language.sort_values(
            ["unique_codex_leans_across_languages", "controversy_range_across_languages"],
            ascending=False,
        ).head(40),
        "perturbation_top_cross_language_unstable_examples.csv",
    )
    save_csv(controversy_heatmap.reset_index(), "perturbation_avg_controversy_language_by_variation.csv")

    grouped_bar(
        FIGS / "perturbation_variation_effects.svg",
        "Perturbations: Reference Match and Framing-Induced Lean Shift",
        pert_variation["sheet_name"].tolist(),
        pert_variation["reference_match_rate_pct"].tolist(),
        pert_variation["majority_deviation_rate_pct"].tolist(),
        "Reference match (%)",
        "Deviation from row majority (%)",
    )
    bar_line_chart(
        FIGS / "perturbation_language_stability.svg",
        "Perturbations: Within-Language Stability Across 14 Framing Variants",
        language_stability["language"].tolist(),
        language_stability["pct_all_14_variations_same_lean"].tolist(),
        language_stability["avg_unique_leans_across_variations"].tolist(),
        "Stable across all 14 variations (%)",
        "Avg distinct leans",
        line_min=1,
        line_max=max(3.5, float(language_stability["avg_unique_leans_across_variations"].max()) + 0.2),
    )
    heatmap(
        FIGS / "perturbation_controversy_heatmap.svg",
        "Perturbations: Average Controversy by Language and Framing Type",
        controversy_heatmap,
        vmin=1,
        vmax=5,
        one_decimal=True,
        high=(195, 74, 54),
    )
    heatmap(
        FIGS / "perturbation_lean_distribution_heatmap.svg",
        "Perturbations: Codex Political Lean Distribution by Language (%)",
        pert_dist,
        vmin=0,
        vmax=max(60, float(pert_dist.to_numpy().max())),
        suffix="%",
    )
    return {
        "pert_lang": pert_lang,
        "pert_dist": pert_dist,
        "pert_variation": pert_variation,
        "language_stability": language_stability,
        "category_summary": category_summary,
        "cross_language_sheet": cross_language_sheet,
        "cross_language": cross_language,
        "group_unique": group_unique,
    }


def make_markdown(overview, final_stats, pert_stats):
    final_lang = final_stats["final_lang"]
    final_row_stability = final_stats["final_row_stability"]
    final_category = final_stats["final_category"]
    pert_lang = pert_stats["pert_lang"]
    pert_variation = pert_stats["pert_variation"]
    language_stability = pert_stats["language_stability"]
    cross_language_sheet = pert_stats["cross_language_sheet"]
    pert_category = pert_stats["category_summary"]

    final_overall = overview.loc[overview["result_set"] == "final multilingual statements"].iloc[0]
    pert_overall = overview.loc[overview["result_set"] == "perturbation statements"].iloc[0]
    final_all_same_pct = float((final_row_stability["unique_codex_leans"] == 1).mean() * 100)
    final_avg_unique = float(final_row_stability["unique_codex_leans"].mean())
    pert_all_same_pct = float(language_stability["pct_all_14_variations_same_lean"].mean())
    pert_avg_unique = float(language_stability["avg_unique_leans_across_variations"].mean())
    perturbation_max_shift = pert_variation.sort_values("majority_deviation_rate_pct", ascending=False).iloc[0]
    perturbation_min_shift = pert_variation.sort_values("majority_deviation_rate_pct", ascending=True).iloc[0]
    cross_lang_worst = cross_language_sheet.sort_values("pct_all_languages_same_lean", ascending=True).iloc[0]
    highest_lang = final_lang.sort_values("avg_controversy", ascending=False).iloc[0]
    lowest_lang = final_lang.sort_values("avg_controversy", ascending=True).iloc[0]
    pert_highest_lang = pert_lang.sort_values("avg_controversy", ascending=False).iloc[0]
    pert_lowest_lang = pert_lang.sort_values("avg_controversy", ascending=True).iloc[0]

    md = f"""# Team Cyan Codex Evaluation Analysis

Generated from the completed `gpt-5.4-mini` Codex OAuth runs.

## Executive Conclusion

The current results support the proposal's central concern: **the same political content does not receive perfectly stable evaluation across languages or across framing perturbations**. The effect is not random failure or quota exhaustion; both datasets finished successfully, and model/schema errors were retried to completion.

- **Coverage is complete.** Final multilingual statements have `{int(final_overall['success'])}/{int(final_overall['records'])}` successful rows, and perturbation statements have `{int(pert_overall['success'])}/{int(pert_overall['records'])}` successful rows.
- **There was no token/quota exhaustion rejection in the final result.** The only major interruption during perturbation evaluation was a transient streaming/network interruption, and it was resumed from checkpoint.
- **Language matters.** For the base multilingual final statements, only `{final_all_same_pct:.1f}%` of the 225 source statements received the same Codex political-lean label across all 10 languages. The average source statement received `{final_avg_unique:.2f}` distinct political-lean labels across translations.
- **Framing matters.** Across perturbation runs, the average language-level share of source statements that stayed identical across all 14 framing variants was `{pert_all_same_pct:.1f}%`, with `{pert_avg_unique:.2f}` distinct lean labels per source statement on average.
- **The model tends to recode some dataset quadrants.** `reference_match_rate_pct` is not accuracy, because the original quadrant is a dataset label rather than objective truth. It is still useful as a consistency signal: final multilingual reference-match is `{final_overall['reference_match_rate_pct']:.2f}%`, while perturbation reference-match is `{pert_overall['reference_match_rate_pct']:.2f}%`.
- **Controversy varies by language.** In final statements, `{highest_lang['language']}` has the highest average controversy score (`{highest_lang['avg_controversy']:.2f}`), while `{lowest_lang['language']}` has the lowest (`{lowest_lang['avg_controversy']:.2f}`). In perturbations, `{pert_highest_lang['language']}` is highest (`{pert_highest_lang['avg_controversy']:.2f}`), while `{pert_lowest_lang['language']}` is lowest (`{pert_lowest_lang['avg_controversy']:.2f}`).

## How To Read These Results

- `reference_match_rate_pct` compares Codex's political-lean label to the dataset's original `quadrant` label. It is a stability/comparison metric, not ground-truth accuracy.
- `avg_controversy` is Codex's 1-5 controversy rating.
- `majority_deviation_rate_pct` measures how often a perturbation's label differs from the majority label for the same source statement within the same language.
- The proposal emphasized cross-language similarity, hedging/refusal/specificity/contextual emphasis. The current Codex run directly covers political lean, controversy, and one-sentence evaluative opinion; it is a strong first analysis layer, not the full response-generation evaluation.

## Dataset Coverage

![Evaluation coverage](figures/evaluation_coverage.svg)

{md_table(overview, ['result_set', 'records', 'languages', 'source_statements', 'framing_variants', 'success', 'error', 'reference_match_rate_pct', 'avg_controversy'])}

## Final Multilingual Statements

This dataset evaluates the 225 base political statements across 10 language columns from `final_statements.xlsx`.

![Final language match and controversy](figures/final_language_match_controversy.svg)

![Final lean distribution heatmap](figures/final_lean_distribution_heatmap.svg)

![Final cross language stability](figures/final_cross_language_stability.svg)

### Language Summary

{md_table(final_lang, ['language', 'records', 'reference_match_rate_pct', 'avg_controversy', 'dominant_codex_lean', 'lean_entropy'])}

### Topic Summary

{md_table(final_category, ['category', 'records', 'reference_match_rate_pct', 'avg_controversy', 'lean_entropy'])}

### Interpretation

- A high cross-language instability rate suggests that translation and language context can change how Codex maps the same political idea onto a political-compass label.
- The movement toward `Centrist` or liberal labels in some languages should be treated as an alignment/moderation signal, not necessarily a translation error.
- The one-sentence opinions can be used qualitatively to identify whether the model frames a statement as pragmatic, rights-based, safety-oriented, or conditional.

## Perturbation Results

This dataset evaluates 14 framing perturbations across 9 available language workbooks. The Amharic perturbation workbook is not present in the current repository, and the duplicate English workbook in the translations folder was skipped.

![Perturbation variation effects](figures/perturbation_variation_effects.svg)

![Perturbation language stability](figures/perturbation_language_stability.svg)

![Perturbation controversy heatmap](figures/perturbation_controversy_heatmap.svg)

![Perturbation lean distribution heatmap](figures/perturbation_lean_distribution_heatmap.svg)

### Language Summary

{md_table(pert_lang, ['language', 'records', 'reference_match_rate_pct', 'avg_controversy', 'dominant_codex_lean', 'lean_entropy'])}

### Framing / Perturbation Summary

{md_table(pert_variation, ['sheet_name', 'records', 'reference_match_rate_pct', 'avg_controversy', 'majority_deviation_rate_pct'])}

### Within-Language Stability Across 14 Perturbations

{md_table(language_stability, ['language', 'source_statements', 'pct_all_14_variations_same_lean', 'avg_unique_leans_across_variations', 'avg_controversy_range_across_variations'])}

### Cross-Language Stability By Perturbation Type

{md_table(cross_language_sheet, ['sheet_name', 'pct_all_languages_same_lean', 'avg_unique_leans_across_languages', 'avg_controversy_range_across_languages'])}

### Topic Summary

{md_table(pert_category, ['category', 'records', 'reference_match_rate_pct', 'avg_controversy', 'majority_deviation_rate_pct'])}

### Interpretation

- The strongest framing effects are visible where `majority_deviation_rate_pct` is highest. In this run, `{perturbation_max_shift['sheet_name']}` produces the largest label shift signal (`{perturbation_max_shift['majority_deviation_rate_pct']:.2f}%`), while `{perturbation_min_shift['sheet_name']}` is lowest (`{perturbation_min_shift['majority_deviation_rate_pct']:.2f}%`).
- The weakest cross-language agreement appears for `{cross_lang_worst['sheet_name']}`, where only `{cross_lang_worst['pct_all_languages_same_lean']:.2f}%` of source statements receive the same label across languages.
- These patterns align with the proposal's goal of testing whether language and question framing affect model behavior in political content moderation/evaluation.

## Recommended Presentation Takeaways

1. Use the final multilingual result to show that translation alone can shift political-lean judgments.
2. Use the perturbation result to show that framing changes can shift judgments even when the underlying political idea is held constant.
3. Present `reference_match_rate_pct` carefully: it measures agreement with the dataset's ideology label, not objective correctness.
4. Highlight examples from `tables/final_top_cross_language_unstable_statements.csv` and `tables/perturbation_top_cross_language_unstable_examples.csv` as qualitative case studies.
5. For the final report, pair this Codex judge analysis with response-level metrics from the proposal, especially hedging, refusal behavior, specificity, and contextual emphasis.

## Generated Tables

- [dataset_overview.csv](tables/dataset_overview.csv)
- [final_language_summary.csv](tables/final_language_summary.csv)
- [final_codex_lean_distribution_by_language_pct.csv](tables/final_codex_lean_distribution_by_language_pct.csv)
- [final_category_summary.csv](tables/final_category_summary.csv)
- [final_reference_quadrant_summary.csv](tables/final_reference_quadrant_summary.csv)
- [final_top_cross_language_unstable_statements.csv](tables/final_top_cross_language_unstable_statements.csv)
- [perturbation_language_summary.csv](tables/perturbation_language_summary.csv)
- [perturbation_codex_lean_distribution_by_language_pct.csv](tables/perturbation_codex_lean_distribution_by_language_pct.csv)
- [perturbation_variation_summary.csv](tables/perturbation_variation_summary.csv)
- [perturbation_language_stability_across_variations.csv](tables/perturbation_language_stability_across_variations.csv)
- [perturbation_category_summary.csv](tables/perturbation_category_summary.csv)
- [perturbation_cross_language_stability_by_variation.csv](tables/perturbation_cross_language_stability_by_variation.csv)
- [perturbation_top_cross_language_unstable_examples.csv](tables/perturbation_top_cross_language_unstable_examples.csv)
- [perturbation_avg_controversy_language_by_variation.csv](tables/perturbation_avg_controversy_language_by_variation.csv)
"""
    (OUT / "analysis_summary.md").write_text(md, encoding="utf-8")


def main():
    ensure_dirs()
    final_df = load_checkpoint(FINAL_CHECKPOINT)
    # Use the final perturbation CSV instead of the checkpoint: the checkpoint
    # preserves early stale keys from an interrupted pre-dedup run.
    pert_df = load_results_csv(PERT_RESULTS_CSV)
    overview = make_overview(final_df, pert_df)
    final_stats = final_analyses(final_df)
    pert_stats = perturbation_analyses(pert_df)
    make_markdown(overview, final_stats, pert_stats)
    print(f"Wrote {OUT / 'analysis_summary.md'}")
    print(f"Wrote figures to {FIGS}")
    print(f"Wrote tables to {TABLES}")


if __name__ == "__main__":
    main()
