from __future__ import annotations

import csv
import math
import re
import textwrap
import zipfile
from collections import Counter, defaultdict
from pathlib import Path
from xml.etree import ElementTree as ET

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
RESULT_DIR = ROOT / "results"
GPT_ANALYSIS_DIR = RESULT_DIR / "gpt5_4_mini" / "analysis"
GEMMA_DIR = RESULT_DIR / "gemma4"
PROJECT_DOC_DIR = ROOT / "docs" / "project_documents"
OUT_DIR = RESULT_DIR / "model_comparison"
FIG_DIR = OUT_DIR / "figures"
TABLE_DIR = OUT_DIR / "tables"

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

LEAN_ORDER = ["Auth-Left", "Auth-Right", "Centrist", "Lib-Left", "Lib-Right"]
LEAN_COLORS = {
    "Auth-Left": "#7C3AED",
    "Auth-Right": "#DC2626",
    "Centrist": "#64748B",
    "Lib-Left": "#2563EB",
    "Lib-Right": "#16A34A",
}
MODEL_COLORS = {
    "Codex gpt-5.4-mini": "#2563EB",
    "Gemma 4": "#F59E0B",
}


def normalize_lean(value: object) -> str | None:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None
    text = str(value).strip()
    if not text:
        return None
    multilingual_aliases = [
        ("Auth-Left", ["सत्तावादी-वाम", "威权-左派", "Autoritaire-Gauche", "Авторитарный-Левый", "سلطوي-يسار", "اقتدارگرا-چپ", "ሥልጣናዊ-ግራ", "Autoritario-Izquierda"]),
        ("Auth-Right", ["सत्तावादी-दक्षिण", "威权-右派", "Autoritaire-Droite", "Авторитарный-Правый", "سلطوي-يمين", "اقتدارگرا-راست", "ሥልጣናዊ-ቀኝ", "Autoritario-Derecha"]),
        ("Centrist", ["मध्यमार्गी", "中间派", "Centriste", "Centrist", "Центрист", "وسطي", "میانه‌رو", "መካከለኛ", "Centrista"]),
        ("Lib-Left", ["उदारवादी-वाम", "自由-左派", "Libéral-Gauche", "Либеральный-Левый", "ليبرالي-يسار", "آزادی‌خواه-چپ", "ሊበራል-ግራ", "Liberal-Izquierda"]),
        ("Lib-Right", ["उदारवादी-दक्षिण", "自由-右派", "Libéral-Droite", "Либеральный-Правый", "ليبرالي-يمين", "آزادی‌خواه-راست", "ሊበራል-ቀኝ", "Liberal-Derecha"]),
    ]
    for lean, aliases in multilingual_aliases:
        if any(alias in text for alias in aliases):
            return lean
    compact = (
        text.lower()
        .replace("_", "-")
        .replace(" ", "-")
        .replace("authoritarian", "auth")
        .replace("libertarian", "lib")
    )
    compact = re.sub(r"[^a-z-]", "", compact)
    aliases = {
        "auth-left": "Auth-Left",
        "authleft": "Auth-Left",
        "left-authoritarian": "Auth-Left",
        "leftauth": "Auth-Left",
        "authoritarian-left": "Auth-Left",
        "auth-right": "Auth-Right",
        "authright": "Auth-Right",
        "right-authoritarian": "Auth-Right",
        "rightauth": "Auth-Right",
        "authoritarian-right": "Auth-Right",
        "centrist": "Centrist",
        "center": "Centrist",
        "centre": "Centrist",
        "moderate": "Centrist",
        "lib-left": "Lib-Left",
        "libleft": "Lib-Left",
        "left-libertarian": "Lib-Left",
        "libertarian-left": "Lib-Left",
        "lib-right": "Lib-Right",
        "libright": "Lib-Right",
        "right-libertarian": "Lib-Right",
        "libertarian-right": "Lib-Right",
    }
    if compact in aliases:
        return aliases[compact]
    for lean in LEAN_ORDER:
        if lean.lower() in compact:
            return lean
    return text


def parse_response_lean(value: object) -> str | None:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None
    text = str(value)
    match = re.search(r"lean\s*:\s*([A-Za-z -]+)", text, flags=re.IGNORECASE)
    if match:
        return normalize_lean(match.group(1).strip())
    return normalize_lean(text)


def normalize_language(name: object) -> str:
    text = str(name).strip()
    text = text.replace("_", " ")
    text = re.sub(r"\s+", " ", text)
    if text.lower().startswith("statement- english"):
        return "English"
    aliases = {
        "Latin American Spanish": "Latin American Spanish",
        "Latin american Spanish": "Latin American Spanish",
        "Latin American spanish": "Latin American Spanish",
        "Simplified Mandarin": "Simplified Mandarin",
        "Spain Spanish": "Spain Spanish",
        "Spanish Spain": "Spain Spanish",
        "Latin America Spanish": "Latin American Spanish",
    }
    return aliases.get(text, text)


def normalize_perturbation(name: object) -> str:
    text = str(name).strip()
    aliases = {
        "Open-ended": "Open Ended",
        "Open Ended": "Open Ended",
        "Yes-No Forced Choice": "Yes-No Forced Choice",
        "Yes-no/forced choice": "Yes-No Forced Choice",
        "Embedding": "Embedded",
        "Embedded": "Embedded",
    }
    return aliases.get(text, text)


def find_col(columns: list[str], candidates: list[str], contains: list[str] | None = None) -> str | None:
    norm = {str(c).strip().lower(): c for c in columns}
    for candidate in candidates:
        key = candidate.strip().lower()
        if key in norm:
            return norm[key]
    if contains:
        for c in columns:
            low = str(c).strip().lower()
            if all(part in low for part in contains):
                return c
    return None


def load_codex_final() -> pd.DataFrame:
    path = GPT_ANALYSIS_DIR / "codex_final_multilingual_review.csv"
    df = pd.read_csv(path, encoding="utf-8")
    out = pd.DataFrame(
        {
            "model": "Codex gpt-5.4-mini",
            "dataset": "Final statements",
            "language": df["language"].map(normalize_language),
            "statement_id": df["row_id"],
            "category": df["category"],
            "reference_lean": df["quadrant"].map(normalize_lean),
            "political_lean": df["codex_political_lean"].map(normalize_lean),
            "perturbation": "Original",
            "status": df.get("status", "success"),
        }
    )
    return out


def load_codex_perturbation() -> pd.DataFrame:
    path = GPT_ANALYSIS_DIR / "codex_workbook_eval_results.csv"
    df = pd.read_csv(path, encoding="utf-8")
    out = pd.DataFrame(
        {
            "model": "Codex gpt-5.4-mini",
            "dataset": "Perturbations",
            "language": df["language"].map(normalize_language),
            "statement_id": df["row_id"],
            "category": df["category"],
            "reference_lean": df["quadrant"].map(normalize_lean),
            "political_lean": df["codex_political_lean"].map(normalize_lean),
            "perturbation": df["sheet_name"].map(normalize_perturbation),
            "status": df.get("status", "success"),
        }
    )
    return out


def load_gemma_final() -> pd.DataFrame:
    path = GEMMA_DIR / "Gemma4.xlsx"
    xl = pd.ExcelFile(path)
    frames: list[pd.DataFrame] = []
    for sheet in xl.sheet_names:
        raw = pd.read_excel(path, sheet_name=sheet)
        if raw.empty:
            continue
        cols = list(raw.columns)
        language_col = find_col(cols, ["language", "Language"])
        statement_col = find_col(cols, ["statement_id", "Statement ID", "id", "ID"])
        category_col = find_col(cols, ["category", "Category"])
        ref_col = find_col(cols, ["quadrant", "reference_quadrant", "original_quadrant", "Quadrant"])
        lean_col = find_col(
            cols,
            [
                "political_lean",
                "gemma_political_lean",
                "predicted_lean",
                "lean",
                "Political Lean",
                "Political lean",
            ],
            contains=["lean"],
        )
        response_col = find_col(cols, ["model_response", "response", "Model Response"])
        if lean_col is None and response_col is None:
            continue
        language = raw[language_col].map(normalize_language) if language_col else normalize_language(sheet)
        if statement_col:
            statement_id = raw[statement_col]
        elif language_col:
            statement_id = raw.groupby(language_col).cumcount() + 1
        else:
            statement_id = raw.index + 1
        lean_values = raw[lean_col].map(normalize_lean) if lean_col else raw[response_col].map(parse_response_lean)
        frame = pd.DataFrame(
            {
                "model": "Gemma 4",
                "dataset": "Final statements",
                "language": language,
                "statement_id": statement_id,
                "category": raw[category_col] if category_col else None,
                "reference_lean": raw[ref_col].map(normalize_lean) if ref_col else None,
                "political_lean": lean_values,
                "perturbation": "Original",
                "status": "success",
            }
        )
        frames.append(frame)
    if not frames:
        raise ValueError(f"No Gemma final political lean columns found in {path}")
    return pd.concat(frames, ignore_index=True)


def load_gemma_perturbation() -> pd.DataFrame:
    folder = GEMMA_DIR / "local_perturbation_results"
    frames: list[pd.DataFrame] = []
    for path in sorted(folder.glob("*.xlsx")):
        language = normalize_language(path.stem.removeprefix("results_"))
        xl = pd.ExcelFile(path)
        for sheet in xl.sheet_names:
            if sheet.strip().lower() == "final_statements":
                continue
            raw = pd.read_excel(path, sheet_name=sheet)
            if raw.empty:
                continue
            cols = list(raw.columns)
            statement_col = find_col(cols, ["statement_id", "Statement ID", "id", "ID"])
            category_col = find_col(cols, ["category", "Category"])
            ref_col = find_col(cols, ["quadrant", "reference_quadrant", "original_quadrant", "Quadrant"])
            lean_col = find_col(
                cols,
                [
                    "political_lean",
                    "gemma_political_lean",
                    "predicted_lean",
                    "lean",
                    "Political Lean",
                    "Political lean",
                ],
                contains=["lean"],
            )
            response_col = find_col(cols, ["model_response", "response", "Model Response"])
            if lean_col is None and response_col is None:
                continue
            lean_values = raw[lean_col].map(normalize_lean) if lean_col else raw[response_col].map(parse_response_lean)
            frame = pd.DataFrame(
                {
                    "model": "Gemma 4",
                    "dataset": "Perturbations",
                    "language": language,
                    "statement_id": raw[statement_col] if statement_col else raw.index + 1,
                    "category": raw[category_col] if category_col else None,
                    "reference_lean": raw[ref_col].map(normalize_lean) if ref_col else None,
                    "political_lean": lean_values,
                    "perturbation": normalize_perturbation(sheet),
                    "status": "success",
                }
            )
            frames.append(frame)
    if not frames:
        raise ValueError(f"No Gemma perturbation political lean columns found in {folder}")
    return pd.concat(frames, ignore_index=True)


def entropy(values: pd.Series) -> float:
    counts = values.dropna().value_counts()
    counts = counts[counts > 0]
    total = counts.sum()
    if total == 0:
        return 0.0
    return float(-sum((count / total) * math.log2(count / total) for count in counts))


def pct(value: float) -> float:
    return round(float(value) * 100, 2)


def reference_match_rate(df: pd.DataFrame) -> float:
    valid = df[df["reference_lean"].notna() & df["political_lean"].notna()]
    if valid.empty:
        return float("nan")
    return pct((valid["reference_lean"] == valid["political_lean"]).mean())


def dominant_lean(df: pd.DataFrame) -> str:
    counts = df["political_lean"].dropna().value_counts()
    return counts.index[0] if not counts.empty else ""


def summarize_language(df: pd.DataFrame, dataset: str) -> pd.DataFrame:
    rows = []
    for (model, language), g in df[df["dataset"] == dataset].groupby(["model", "language"], sort=False):
        rows.append(
            {
                "model": model,
                "language": language,
                "records": len(g),
                "reference_match_rate_pct": reference_match_rate(g),
                "dominant_lean": dominant_lean(g),
                "lean_entropy": round(entropy(g["political_lean"]), 3),
            }
        )
    return pd.DataFrame(rows).sort_values(["model", "language"])


def lean_distribution(df: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    grouped = df.groupby(group_cols + ["political_lean"], dropna=False).size().reset_index(name="count")
    total = grouped.groupby(group_cols)["count"].transform("sum")
    grouped["pct"] = (grouped["count"] / total * 100).round(2)
    pivot = grouped.pivot_table(index=group_cols, columns="political_lean", values="pct", fill_value=0).reset_index()
    for lean in LEAN_ORDER:
        if lean not in pivot.columns:
            pivot[lean] = 0.0
    return pivot[group_cols + LEAN_ORDER]


def model_agreement_final(df: pd.DataFrame) -> pd.DataFrame:
    final = df[df["dataset"] == "Final statements"].copy()
    pivot = final.pivot_table(
        index=["language", "statement_id"],
        columns="model",
        values="political_lean",
        aggfunc="first",
    ).reset_index()
    both = pivot.dropna(subset=["Codex gpt-5.4-mini", "Gemma 4"])
    return (
        both.assign(agree=both["Codex gpt-5.4-mini"] == both["Gemma 4"])
        .groupby("language", as_index=False)
        .agg(records=("agree", "size"), model_agreement_pct=("agree", lambda s: pct(s.mean())))
        .sort_values("model_agreement_pct")
    )


def model_agreement_perturbation(df: pd.DataFrame) -> pd.DataFrame:
    pert = df[df["dataset"] == "Perturbations"].copy()
    pivot = pert.pivot_table(
        index=["language", "statement_id", "perturbation"],
        columns="model",
        values="political_lean",
        aggfunc="first",
    ).reset_index()
    both = pivot.dropna(subset=["Codex gpt-5.4-mini", "Gemma 4"])
    return (
        both.assign(agree=both["Codex gpt-5.4-mini"] == both["Gemma 4"])
        .groupby("perturbation", as_index=False)
        .agg(records=("agree", "size"), model_agreement_pct=("agree", lambda s: pct(s.mean())))
        .sort_values("model_agreement_pct")
    )


def cross_language_stability(df: pd.DataFrame) -> pd.DataFrame:
    final = df[df["dataset"] == "Final statements"].copy()
    rows = []
    for model, g in final.groupby("model"):
        per_statement = g.groupby("statement_id")["political_lean"].nunique()
        rows.append(
            {
                "model": model,
                "source_statements": int(per_statement.count()),
                "pct_all_languages_same_lean": pct((per_statement == 1).mean()),
                "avg_unique_leans_across_languages": round(per_statement.mean(), 3),
            }
        )
    return pd.DataFrame(rows)


def perturbation_stability(df: pd.DataFrame) -> pd.DataFrame:
    pert = df[df["dataset"] == "Perturbations"].copy()
    rows = []
    for (model, language), g in pert.groupby(["model", "language"]):
        per_statement = g.groupby("statement_id")["political_lean"].nunique()
        rows.append(
            {
                "model": model,
                "language": language,
                "source_statements": int(per_statement.count()),
                "pct_all_perturbations_same_lean": pct((per_statement == 1).mean()),
                "avg_unique_leans_across_perturbations": round(per_statement.mean(), 3),
            }
        )
    return pd.DataFrame(rows).sort_values(["model", "language"])


def perturbation_shift(df: pd.DataFrame) -> pd.DataFrame:
    pert = df[df["dataset"] == "Perturbations"].copy()
    rows = []
    for (model, perturbation), g in pert.groupby(["model", "perturbation"]):
        rows.append(
            {
                "model": model,
                "perturbation": perturbation,
                "records": len(g),
                "reference_match_rate_pct": reference_match_rate(g),
                "dominant_lean": dominant_lean(g),
                "lean_entropy": round(entropy(g["political_lean"]), 3),
            }
        )
    return pd.DataFrame(rows).sort_values(["model", "perturbation"])


def write_csv(df: pd.DataFrame, filename: str) -> None:
    path = TABLE_DIR / filename
    df.to_csv(path, index=False, encoding="utf-8-sig")


def svg_escape(text: object) -> str:
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def draw_text(lines: list[str], x: int, y: int, size: int = 14, color: str = "#111827", weight: int = 400) -> str:
    out = []
    for i, line in enumerate(lines):
        out.append(
            f'<text x="{x}" y="{y + i * int(size * 1.35)}" font-family="Arial, sans-serif" '
            f'font-size="{size}" fill="{color}" font-weight="{weight}">{svg_escape(line)}</text>'
        )
    return "\n".join(out)


def save_svg(name: str, width: int, height: int, body: str) -> None:
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">\n'
        '<rect width="100%" height="100%" fill="#F8FAFC"/>\n'
        f"{body}\n</svg>\n"
    )
    (FIG_DIR / name).write_text(svg, encoding="utf-8")


def grouped_bar_svg(summary: pd.DataFrame) -> None:
    metrics = [
        ("Cross-language stability", "pct_all_languages_same_lean"),
        ("Perturbation stability", "pct_all_perturbations_same_lean"),
        ("Final model agreement", "final_model_agreement_pct"),
        ("Perturbation model agreement", "perturbation_model_agreement_pct"),
    ]
    data = {
        "Codex gpt-5.4-mini": {
            "pct_all_languages_same_lean": float(summary.loc["Codex gpt-5.4-mini", "pct_all_languages_same_lean"]),
            "pct_all_perturbations_same_lean": float(summary.loc["Codex gpt-5.4-mini", "pct_all_perturbations_same_lean"]),
            "final_model_agreement_pct": float(summary.loc["Codex gpt-5.4-mini", "final_model_agreement_pct"]),
            "perturbation_model_agreement_pct": float(summary.loc["Codex gpt-5.4-mini", "perturbation_model_agreement_pct"]),
        },
        "Gemma 4": {
            "pct_all_languages_same_lean": float(summary.loc["Gemma 4", "pct_all_languages_same_lean"]),
            "pct_all_perturbations_same_lean": float(summary.loc["Gemma 4", "pct_all_perturbations_same_lean"]),
            "final_model_agreement_pct": float(summary.loc["Gemma 4", "final_model_agreement_pct"]),
            "perturbation_model_agreement_pct": float(summary.loc["Gemma 4", "perturbation_model_agreement_pct"]),
        },
    }
    width, height = 1120, 620
    left, top, chart_w, chart_h = 120, 150, 900, 350
    parts = [
        draw_text(["Model comparison: political-lean stability and agreement"], 52, 62, 30, "#0F172A", 700),
        draw_text(["Lower stability/agreement means more recoding of the same political content."], 54, 98, 16, "#475569", 400),
    ]
    for tick in range(0, 101, 20):
        x = left + chart_w * tick / 100
        parts.append(f'<line x1="{x:.1f}" y1="{top}" x2="{x:.1f}" y2="{top + chart_h}" stroke="#E2E8F0"/>')
        parts.append(f'<text x="{x - 8:.1f}" y="{top + chart_h + 34}" font-family="Arial" font-size="13" fill="#64748B">{tick}</text>')
    group_gap = 74
    bar_h = 28
    for idx, (label, key) in enumerate(metrics):
        y = top + idx * group_gap + 14
        parts.append(draw_text([label], 54, y + 20, 14, "#334155", 700))
        for j, model in enumerate(["Codex gpt-5.4-mini", "Gemma 4"]):
            val = data[model][key]
            by = y + j * (bar_h + 6)
            color = MODEL_COLORS[model]
            parts.append(f'<rect x="{left}" y="{by}" width="{chart_w * val / 100:.1f}" height="{bar_h}" rx="5" fill="{color}"/>')
            parts.append(f'<text x="{left + chart_w * val / 100 + 8:.1f}" y="{by + 19}" font-family="Arial" font-size="13" fill="#334155" font-weight="700">{val:.1f}%</text>')
    lx = 760
    for i, model in enumerate(["Codex gpt-5.4-mini", "Gemma 4"]):
        parts.append(f'<rect x="{lx}" y="{66 + i * 26}" width="18" height="18" rx="4" fill="{MODEL_COLORS[model]}"/>')
        parts.append(f'<text x="{lx + 26}" y="{80 + i * 26}" font-family="Arial" font-size="14" fill="#334155">{model}</text>')
    save_svg("model_stability_agreement.svg", width, height, "\n".join(parts))


def heatmap_svg(dist: pd.DataFrame, dataset: str, filename: str, title: str) -> None:
    subset = dist[dist["dataset"] == dataset].copy() if "dataset" in dist.columns else dist.copy()
    languages = [l for l in LANGUAGE_ORDER if l in set(subset["language"])]
    models = ["Codex gpt-5.4-mini", "Gemma 4"]
    cell_w, cell_h = 86, 26
    left, top = 220, 126
    width = left + len(LEAN_ORDER) * cell_w + 60
    height = top + len(models) * len(languages) * cell_h + 90
    parts = [
        draw_text([title], 42, 55, 28, "#0F172A", 700),
        draw_text(["Political-lean distribution by model and language (% of rows)."], 44, 88, 15, "#475569"),
    ]
    for i, lean in enumerate(LEAN_ORDER):
        parts.append(
            f'<text x="{left + i * cell_w + cell_w / 2}" y="{top - 14}" text-anchor="middle" '
            f'font-family="Arial" font-size="12" fill="#475569" font-weight="700">{svg_escape(lean)}</text>'
        )
    row_i = 0
    for model in models:
        parts.append(f'<text x="42" y="{top + row_i * cell_h + 18}" font-family="Arial" font-size="13" fill="{MODEL_COLORS[model]}" font-weight="700">{model}</text>')
        for language in languages:
            row = subset[(subset["model"] == model) & (subset["language"] == language)]
            y = top + row_i * cell_h
            parts.append(f'<text x="118" y="{y + 18}" font-family="Arial" font-size="12" fill="#334155">{svg_escape(language)}</text>')
            for j, lean in enumerate(LEAN_ORDER):
                val = float(row[lean].iloc[0]) if not row.empty and lean in row.columns else 0.0
                alpha = 0.12 + 0.78 * val / 100
                color = LEAN_COLORS[lean]
                parts.append(f'<rect x="{left + j * cell_w}" y="{y}" width="{cell_w - 2}" height="{cell_h - 2}" fill="{color}" opacity="{alpha:.2f}"/>')
                if val >= 9:
                    parts.append(
                        f'<text x="{left + j * cell_w + cell_w / 2}" y="{y + 17}" text-anchor="middle" '
                        f'font-family="Arial" font-size="11" fill="#0F172A" font-weight="700">{val:.0f}</text>'
                    )
            row_i += 1
        row_i += 1
    save_svg(filename, width, height, "\n".join(parts))


def perturbation_agreement_svg(agreement: pd.DataFrame) -> None:
    data = agreement.sort_values("model_agreement_pct", ascending=True)
    width, height = 1040, 650
    left, top, chart_w, bar_h = 250, 118, 700, 25
    parts = [
        draw_text(["Where models disagree most: perturbation political lean"], 42, 54, 28, "#0F172A", 700),
        draw_text(["Model agreement between Codex gpt-5.4-mini and Gemma 4 by perturbation type."], 44, 86, 15, "#475569"),
    ]
    for tick in range(0, 101, 20):
        x = left + chart_w * tick / 100
        parts.append(f'<line x1="{x:.1f}" y1="{top - 8}" x2="{x:.1f}" y2="{top + len(data) * 34}" stroke="#E2E8F0"/>')
        parts.append(f'<text x="{x - 8:.1f}" y="{top + len(data) * 34 + 28}" font-family="Arial" font-size="12" fill="#64748B">{tick}</text>')
    for i, row in enumerate(data.itertuples(index=False)):
        y = top + i * 34
        label = getattr(row, "perturbation")
        val = float(getattr(row, "model_agreement_pct"))
        parts.append(f'<text x="{left - 14}" y="{y + 17}" text-anchor="end" font-family="Arial" font-size="13" fill="#334155">{svg_escape(label)}</text>')
        parts.append(f'<rect x="{left}" y="{y}" width="{chart_w * val / 100:.1f}" height="{bar_h}" rx="5" fill="#0F766E"/>')
        parts.append(f'<text x="{left + chart_w * val / 100 + 8:.1f}" y="{y + 17}" font-family="Arial" font-size="12" fill="#334155" font-weight="700">{val:.1f}%</text>')
    save_svg("perturbation_model_agreement.svg", width, height, "\n".join(parts))


def table_svg(summary: pd.DataFrame) -> None:
    width, height = 1120, 430
    parts = [
        draw_text(["Core results for presentation"], 42, 58, 28, "#0F172A", 700),
        draw_text(["Political-lean evaluation across two models, languages, and perturbations."], 44, 90, 15, "#475569"),
    ]
    headers = ["Question", "Codex gpt-5.4-mini", "Gemma 4", "Takeaway"]
    rows = [
        [
            "No perturbation: stable across languages",
            f'{summary.loc["Codex gpt-5.4-mini", "pct_all_languages_same_lean"]:.1f}%',
            f'{summary.loc["Gemma 4", "pct_all_languages_same_lean"]:.1f}%',
            "Translation changes political-lean labels for both models.",
        ],
        [
            "Perturbations: stable across 14 variants",
            f'{summary.loc["Codex gpt-5.4-mini", "pct_all_perturbations_same_lean"]:.1f}%',
            f'{summary.loc["Gemma 4", "pct_all_perturbations_same_lean"]:.1f}%',
            "Prompt perturbation creates stronger instability than translation alone.",
        ],
        [
            "Cross-model agreement, no perturbation",
            f'{summary.loc["Codex gpt-5.4-mini", "final_model_agreement_pct"]:.1f}%',
            f'{summary.loc["Gemma 4", "final_model_agreement_pct"]:.1f}%',
            "The models often recode the same statement differently.",
        ],
        [
            "Cross-model agreement, perturbations",
            f'{summary.loc["Codex gpt-5.4-mini", "perturbation_model_agreement_pct"]:.1f}%',
            f'{summary.loc["Gemma 4", "perturbation_model_agreement_pct"]:.1f}%',
            "Model identity matters when prompt form changes.",
        ],
    ]
    x0, y0 = 42, 128
    col_w = [300, 180, 150, 390]
    row_h = 52
    parts.append(f'<rect x="{x0}" y="{y0}" width="{sum(col_w)}" height="{row_h}" fill="#E2E8F0"/>')
    x = x0
    for h, w in zip(headers, col_w):
        parts.append(f'<text x="{x + 14}" y="{y0 + 32}" font-family="Arial" font-size="14" fill="#0F172A" font-weight="700">{svg_escape(h)}</text>')
        x += w
    for i, row in enumerate(rows):
        y = y0 + row_h * (i + 1)
        fill = "#FFFFFF" if i % 2 == 0 else "#F1F5F9"
        parts.append(f'<rect x="{x0}" y="{y}" width="{sum(col_w)}" height="{row_h}" fill="{fill}" stroke="#CBD5E1"/>')
        x = x0
        for val, w in zip(row, col_w):
            wrapped = textwrap.wrap(str(val), width=max(10, int(w / 9)))
            parts.append(draw_text(wrapped[:2], x + 14, y + 21, 13, "#334155", 700 if w < 200 else 400))
            x += w
    save_svg("presentation_core_results_table.svg", width, height, "\n".join(parts))


def docx_text(path: Path) -> str:
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    with zipfile.ZipFile(path) as zf:
        root = ET.fromstring(zf.read("word/document.xml"))
    paras = []
    for par in root.findall(".//w:p", ns):
        text = "".join(t.text or "" for t in par.findall(".//w:t", ns)).strip()
        if text:
            paras.append(text)
    return "\n".join(paras)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    TABLE_DIR.mkdir(parents=True, exist_ok=True)

    frames = [
        load_codex_final(),
        load_codex_perturbation(),
        load_gemma_final(),
        load_gemma_perturbation(),
    ]
    all_df = pd.concat(frames, ignore_index=True)
    all_df = all_df[all_df["political_lean"].isin(LEAN_ORDER)].copy()
    all_df["language"] = pd.Categorical(all_df["language"], categories=LANGUAGE_ORDER, ordered=True)
    all_df["political_lean"] = pd.Categorical(all_df["political_lean"], categories=LEAN_ORDER, ordered=True)
    all_df["reference_lean"] = pd.Categorical(all_df["reference_lean"], categories=LEAN_ORDER, ordered=True)

    write_csv(all_df, "combined_model_political_lean_rows.csv")

    dataset_overview = (
        all_df.groupby(["model", "dataset"], observed=True)
        .agg(
            records=("political_lean", "size"),
            languages=("language", "nunique"),
            source_statements=("statement_id", "nunique"),
            perturbations=("perturbation", "nunique"),
        )
        .reset_index()
    )
    write_csv(dataset_overview, "dataset_overview.csv")

    final_language_summary = summarize_language(all_df, "Final statements")
    perturbation_language_summary = summarize_language(all_df, "Perturbations")
    write_csv(final_language_summary, "final_language_summary_by_model.csv")
    write_csv(perturbation_language_summary, "perturbation_language_summary_by_model.csv")

    final_dist = lean_distribution(all_df[all_df["dataset"] == "Final statements"], ["model", "language"])
    final_dist["dataset"] = "Final statements"
    perturbation_dist = lean_distribution(all_df[all_df["dataset"] == "Perturbations"], ["model", "language"])
    perturbation_dist["dataset"] = "Perturbations"
    write_csv(final_dist, "final_lean_distribution_model_language_pct.csv")
    write_csv(perturbation_dist, "perturbation_lean_distribution_model_language_pct.csv")

    final_agree = model_agreement_final(all_df)
    perturb_agree = model_agreement_perturbation(all_df)
    write_csv(final_agree, "final_cross_model_agreement_by_language.csv")
    write_csv(perturb_agree, "perturbation_cross_model_agreement_by_type.csv")

    cross_lang = cross_language_stability(all_df)
    perturb_stab = perturbation_stability(all_df)
    perturb_shift_summary = perturbation_shift(all_df)
    write_csv(cross_lang, "final_cross_language_stability_by_model.csv")
    write_csv(perturb_stab, "perturbation_stability_by_model_language.csv")
    write_csv(perturb_shift_summary, "perturbation_summary_by_model_type.csv")

    stability_avg = perturb_stab.groupby("model", as_index=False).agg(
        pct_all_perturbations_same_lean=("pct_all_perturbations_same_lean", "mean"),
        avg_unique_leans_across_perturbations=("avg_unique_leans_across_perturbations", "mean"),
    )
    summary = cross_lang.merge(stability_avg, on="model")
    final_overall_agreement = pct(
        all_df[all_df["dataset"] == "Final statements"]
        .pivot_table(index=["language", "statement_id"], columns="model", values="political_lean", aggfunc="first")
        .dropna()
        .pipe(lambda p: (p["Codex gpt-5.4-mini"] == p["Gemma 4"]).mean())
    )
    perturb_overall_agreement = pct(
        all_df[all_df["dataset"] == "Perturbations"]
        .pivot_table(index=["language", "statement_id", "perturbation"], columns="model", values="political_lean", aggfunc="first")
        .dropna()
        .pipe(lambda p: (p["Codex gpt-5.4-mini"] == p["Gemma 4"]).mean())
    )
    summary["final_model_agreement_pct"] = final_overall_agreement
    summary["perturbation_model_agreement_pct"] = perturb_overall_agreement
    summary = summary.set_index("model")
    write_csv(summary.reset_index(), "presentation_metric_summary.csv")

    grouped_bar_svg(summary)
    heatmap_svg(final_dist, "Final statements", "final_model_language_lean_heatmap.svg", "No perturbation: political lean by model and language")
    heatmap_svg(perturbation_dist, "Perturbations", "perturbation_model_language_lean_heatmap.svg", "Perturbations: political lean by model and language")
    perturbation_agreement_svg(perturb_agree)
    table_svg(summary)

    proposal_path = PROJECT_DOC_DIR / "Team Cyan AI and Humanity Project Idea.docx"
    proposal = docx_text(proposal_path) if proposal_path.exists() else ""
    proposal_hits = []
    for line in proposal.splitlines():
        low = line.lower()
        if any(word in low for word in ["language", "political", "bias", "framing", "moderation", "alignment"]):
            proposal_hits.append(line)
        if len(proposal_hits) >= 12:
            break

    lowest_perturb = perturb_agree.sort_values("model_agreement_pct").head(3)
    highest_final_disagree = final_agree.sort_values("model_agreement_pct").head(3)
    md = f"""# Model Comparison Analysis for Results Slides

This analysis compares `Codex gpt-5.4-mini` and `Gemma 4` on political-lean labels across languages and perturbations.

## Presentation-Ready Takeaways

1. **Language changes political-lean judgments even without perturbation.** Codex keeps the same lean across all translated versions for `{summary.loc["Codex gpt-5.4-mini", "pct_all_languages_same_lean"]:.1f}%` of source statements; Gemma 4 keeps the same lean for `{summary.loc["Gemma 4", "pct_all_languages_same_lean"]:.1f}%`.
2. **Perturbation changes political-lean judgments more strongly than translation alone.** Codex stability across all 14 perturbations averages `{summary.loc["Codex gpt-5.4-mini", "pct_all_perturbations_same_lean"]:.1f}%`; Gemma 4 averages `{summary.loc["Gemma 4", "pct_all_perturbations_same_lean"]:.1f}%`.
3. **Model identity matters.** Codex and Gemma 4 agree on `{final_overall_agreement:.1f}%` of no-perturbation language rows and `{perturb_overall_agreement:.1f}%` of perturbation rows.
4. **The lowest model agreement under perturbation appears in:** {", ".join(f"{r.perturbation} ({r.model_agreement_pct:.1f}%)" for r in lowest_perturb.itertuples(index=False))}.
5. **The lowest model agreement without perturbation appears in:** {", ".join(f"{r.language} ({r.model_agreement_pct:.1f}%)" for r in highest_final_disagree.itertuples(index=False))}.

## How This Connects To The Proposal

The proposal asks whether political-content moderation/evaluation changes across languages, model families, and prompt framing. These results support that framing:

- The same source statement can move across political-compass labels after translation.
- Perturbations are not merely surface rewrites; they change model political-lean judgments.
- Differences appear both within one model and between models, which suggests the behavior is not just a translation artifact.

## Recommended Slide Placement

- **Slide 20 / Shifted Lean:** insert `figures/final_model_language_lean_heatmap.svg` to show no-perturbation language effects by model.
- **Slide 25 / Outcomes:** insert `figures/model_stability_agreement.svg` or `figures/presentation_core_results_table.svg` as the main evidence chart/table.
- **Slide 26 / Conclusion:** use the conclusion text below and optionally add `figures/perturbation_model_agreement.svg` if there is room.

## Suggested Result / Outcome Wording

**Result:** Across the original, non-perturbed statements, political-lean labels vary by language and by model. This means translation alone can change how a model places the same political claim on the political compass.

**Outcome 1:** Language is an evaluation variable. Even when statements are semantically equivalent, both models recode some translations into different political-lean categories.

**Outcome 2:** Perturbation amplifies instability. Prompt variants such as open-ended, loss-framed, and hedged wording create larger political-lean shifts and lower cross-model agreement.

**Conclusion:** Political-content moderation is shaped by both language and prompt form. Because Codex and Gemma 4 disagree on a substantial share of rows, multilingual moderation should not assume that one model, one language, or one prompt framing gives a neutral baseline.

## Generated Figures

- `figures/model_stability_agreement.svg`
- `figures/final_model_language_lean_heatmap.svg`
- `figures/perturbation_model_language_lean_heatmap.svg`
- `figures/perturbation_model_agreement.svg`
- `figures/presentation_core_results_table.svg`

## Generated Tables

- `tables/presentation_metric_summary.csv`
- `tables/final_language_summary_by_model.csv`
- `tables/final_lean_distribution_model_language_pct.csv`
- `tables/final_cross_model_agreement_by_language.csv`
- `tables/perturbation_language_summary_by_model.csv`
- `tables/perturbation_lean_distribution_model_language_pct.csv`
- `tables/perturbation_cross_model_agreement_by_type.csv`
- `tables/perturbation_stability_by_model_language.csv`
- `tables/perturbation_summary_by_model_type.csv`

## Proposal Lines Used As Context

{chr(10).join("- " + line for line in proposal_hits)}
"""
    (OUT_DIR / "model_comparison_summary.md").write_text(md, encoding="utf-8")


if __name__ == "__main__":
    main()
