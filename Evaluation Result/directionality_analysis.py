from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(r"E:\CourseProject\cs4501_26spring_final_project")
BASE = ROOT / "Evaluation Result"
COMPARISON = BASE / "model_comparison" / "tables"
OUT = BASE / "directionality"
OUT.mkdir(exist_ok=True)

LEAN_ORDER = ["Auth-Left", "Auth-Right", "Centrist", "Lib-Left", "Lib-Right"]
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


def pct(value: float) -> float:
    return round(float(value) * 100, 2)


def value_dist(series: pd.Series) -> pd.Series:
    counts = series.value_counts(normalize=True)
    return pd.Series({lean: counts.get(lean, 0.0) * 100 for lean in LEAN_ORDER})


def mode_with_pct(series: pd.Series) -> tuple[str, float]:
    series = series.dropna()
    if series.empty:
        return "", 0.0
    counts = series.value_counts()
    return str(counts.index[0]), pct(counts.iloc[0] / counts.sum())


def top_transition(df: pd.DataFrame) -> tuple[str, int, float]:
    shifted = df[df["source_lean"] != df["target_lean"]].copy()
    if shifted.empty:
        return "", 0, 0.0
    transitions = (shifted["source_lean"].astype(str) + " -> " + shifted["target_lean"].astype(str)).value_counts()
    return str(transitions.index[0]), int(transitions.iloc[0]), pct(transitions.iloc[0] / len(shifted))


def direction_label(dominant_to: str, net_to: str) -> str:
    if not dominant_to:
        return "No measurable shift"
    if dominant_to == net_to:
        return f"Strong {net_to} direction"
    return f"Mixed: shifted-to {dominant_to}, net +{net_to}"


def language_directionality(df: pd.DataFrame) -> pd.DataFrame:
    final = df[df["dataset"] == "Final statements"].copy()
    rows = []
    for model, model_df in final.groupby("model"):
        pivot = model_df.pivot_table(
            index="statement_id",
            columns="language",
            values="political_lean",
            aggfunc="first",
        )
        english_dist = value_dist(pivot["English"])
        for language in LANGUAGE_ORDER:
            if language not in pivot.columns:
                continue
            pair = pd.DataFrame(
                {
                    "source_lean": pivot["English"],
                    "target_lean": pivot[language],
                }
            ).dropna()
            shifted = pair[pair["source_lean"] != pair["target_lean"]]
            dominant_to, dominant_to_pct = mode_with_pct(shifted["target_lean"])
            lang_dist = value_dist(pair["target_lean"])
            delta = lang_dist - english_dist
            net_to = str(delta.idxmax())
            transition, transition_count, transition_pct = top_transition(pair)
            rows.append(
                {
                    "model": model,
                    "language": language,
                    "records": len(pair),
                    "shift_count": len(shifted),
                    "shift_rate_pct": pct(len(shifted) / len(pair)) if len(pair) else 0.0,
                    "dominant_shifted_to_lean": dominant_to,
                    "dominant_shifted_to_pct_of_shifted": dominant_to_pct,
                    "largest_net_increase_lean": net_to,
                    "largest_net_increase_pct_points": round(float(delta[net_to]), 2),
                    "largest_net_decrease_lean": str(delta.idxmin()),
                    "largest_net_decrease_pct_points": round(float(delta.min()), 2),
                    "top_transition": transition,
                    "top_transition_count": transition_count,
                    "top_transition_pct_of_shifted": transition_pct,
                    "direction_summary": direction_label(dominant_to, net_to),
                }
            )
    out = pd.DataFrame(rows)
    out["language"] = pd.Categorical(out["language"], categories=LANGUAGE_ORDER, ordered=True)
    out = out.sort_values(["language", "model"])
    return out


def language_cross_model(language_dir: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for language, group in language_dir.groupby("language", observed=True):
        by_model = group.set_index("model")
        if {"Codex gpt-5.4-mini", "Gemma 4"} - set(by_model.index):
            continue
        codex = by_model.loc["Codex gpt-5.4-mini"]
        gemma = by_model.loc["Gemma 4"]
        rows.append(
            {
                "language": language,
                "codex_shift_to": codex["dominant_shifted_to_lean"],
                "codex_net_to": codex["largest_net_increase_lean"],
                "codex_shift_rate_pct": codex["shift_rate_pct"],
                "gemma_shift_to": gemma["dominant_shifted_to_lean"],
                "gemma_net_to": gemma["largest_net_increase_lean"],
                "gemma_shift_rate_pct": gemma["shift_rate_pct"],
                "same_dominant_shift_to": codex["dominant_shifted_to_lean"] == gemma["dominant_shifted_to_lean"],
                "same_net_direction": codex["largest_net_increase_lean"] == gemma["largest_net_increase_lean"],
            }
        )
    return pd.DataFrame(rows)


def perturbation_directionality(df: pd.DataFrame) -> pd.DataFrame:
    pert = df[df["dataset"] == "Perturbations"].copy()
    majority = (
        pert.groupby(["model", "language", "statement_id"])["political_lean"]
        .agg(lambda s: s.value_counts().index[0])
        .rename("source_lean")
        .reset_index()
    )
    pert = pert.merge(majority, on=["model", "language", "statement_id"], how="left")
    pert = pert.rename(columns={"political_lean": "target_lean"})
    rows = []
    for (model, perturbation), group in pert.groupby(["model", "perturbation"]):
        pair = group[["source_lean", "target_lean"]].dropna()
        shifted = pair[pair["source_lean"] != pair["target_lean"]]
        dominant_to, dominant_to_pct = mode_with_pct(shifted["target_lean"])
        target_dist = value_dist(pair["target_lean"])
        baseline_dist = value_dist(pair["source_lean"])
        delta = target_dist - baseline_dist
        net_to = str(delta.idxmax())
        transition, transition_count, transition_pct = top_transition(pair)
        rows.append(
            {
                "model": model,
                "perturbation": perturbation,
                "records": len(pair),
                "shift_count": len(shifted),
                "shift_rate_pct": pct(len(shifted) / len(pair)) if len(pair) else 0.0,
                "dominant_shifted_to_lean": dominant_to,
                "dominant_shifted_to_pct_of_shifted": dominant_to_pct,
                "largest_net_increase_lean": net_to,
                "largest_net_increase_pct_points": round(float(delta[net_to]), 2),
                "largest_net_decrease_lean": str(delta.idxmin()),
                "largest_net_decrease_pct_points": round(float(delta.min()), 2),
                "top_transition": transition,
                "top_transition_count": transition_count,
                "top_transition_pct_of_shifted": transition_pct,
                "direction_summary": direction_label(dominant_to, net_to),
            }
        )
    out = pd.DataFrame(rows)
    out["perturbation"] = pd.Categorical(out["perturbation"], categories=PERTURBATION_ORDER, ordered=True)
    out = out.sort_values(["perturbation", "model"])
    return out


def perturbation_cross_model(pert_dir: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for perturbation, group in pert_dir.groupby("perturbation", observed=True):
        by_model = group.set_index("model")
        if {"Codex gpt-5.4-mini", "Gemma 4"} - set(by_model.index):
            continue
        codex = by_model.loc["Codex gpt-5.4-mini"]
        gemma = by_model.loc["Gemma 4"]
        rows.append(
            {
                "perturbation": perturbation,
                "codex_shift_to": codex["dominant_shifted_to_lean"],
                "codex_net_to": codex["largest_net_increase_lean"],
                "codex_shift_rate_pct": codex["shift_rate_pct"],
                "gemma_shift_to": gemma["dominant_shifted_to_lean"],
                "gemma_net_to": gemma["largest_net_increase_lean"],
                "gemma_shift_rate_pct": gemma["shift_rate_pct"],
                "same_dominant_shift_to": codex["dominant_shifted_to_lean"] == gemma["dominant_shifted_to_lean"],
                "same_net_direction": codex["largest_net_increase_lean"] == gemma["largest_net_increase_lean"],
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    df = pd.read_csv(COMPARISON / "combined_model_political_lean_rows.csv")
    df = df[df["political_lean"].isin(LEAN_ORDER)].copy()

    lang_dir = language_directionality(df)
    lang_cross = language_cross_model(lang_dir)
    pert_dir = perturbation_directionality(df)
    pert_cross = perturbation_cross_model(pert_dir)

    lang_dir.to_csv(OUT / "language_directionality_by_model.csv", index=False, encoding="utf-8-sig")
    lang_cross.to_csv(OUT / "language_directionality_cross_model.csv", index=False, encoding="utf-8-sig")
    pert_dir.to_csv(OUT / "perturbation_directionality_by_model.csv", index=False, encoding="utf-8-sig")
    pert_cross.to_csv(OUT / "perturbation_directionality_cross_model.csv", index=False, encoding="utf-8-sig")

    summary = [
        "# Directionality Analysis",
        "",
        "Language directionality compares each translated final statement to the same model's English label.",
        "Perturbation directionality compares each perturbation label to the majority label for the same model, language, and source statement.",
        "",
        "## Languages with same net direction across models",
    ]
    same_lang = lang_cross[lang_cross["same_net_direction"] == True]
    if same_lang.empty:
        summary.append("- None.")
    else:
        for row in same_lang.itertuples(index=False):
            summary.append(f"- {row.language}: both net +{row.codex_net_to}.")
    summary.append("")
    summary.append("## Perturbations with same net direction across models")
    same_pert = pert_cross[pert_cross["same_net_direction"] == True]
    if same_pert.empty:
        summary.append("- None.")
    else:
        for row in same_pert.itertuples(index=False):
            summary.append(f"- {row.perturbation}: both net +{row.codex_net_to}.")
    (OUT / "directionality_summary.md").write_text("\n".join(summary), encoding="utf-8")


if __name__ == "__main__":
    main()
