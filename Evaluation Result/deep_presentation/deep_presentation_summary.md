# Deep Presentation Analysis

## Definitions

- **Shifted lean** means the model changed the political-compass label (`Auth-Left`, `Auth-Right`, `Centrist`, `Lib-Left`, `Lib-Right`) for the same underlying statement.
- **Translation shifted lean** compares each translated statement to the same model's English label.
- **Perturbation shifted lean** compares each perturbation to the majority label across all perturbations for the same model, language, and source statement.
- **Controversy** is the model's 1-5 rating of how politically/socially contentious the statement is. It is not the model's agreement with the statement.

## Deeper Outcomes

1. **Language has directional effects, not just random noise.** Codex is most shifted by `Farsi` (`23.6%`) and least shifted by `Arabic` (`16.0%`). Gemma is most shifted by `Amharic` (`42.2%`) and least shifted by `Russian` (`32.0%`).
2. **Perturbation effects are uneven.** Codex average perturbation shift is `23.9%`; max is `Open Ended` (`40.0%`) and min is `Active Voice` (`15.6%`). Gemma average perturbation shift is `30.7%`; max is `Open Ended` (`47.3%`) and min is `Active Voice` (`17.3%`).
3. **Model behavior differs.** Gemma has higher translation shift (`34.8%`) than Codex (`19.5%`), and higher perturbation shift (`30.7%`) than Codex (`23.9%`).

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
