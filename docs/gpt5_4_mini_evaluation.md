# Codex Evaluation Pipeline

This folder now includes a reusable Codex OAuth evaluation pipeline for Team Cyan's English `final_statements.csv` dataset.

## What it does

- Reads `data/building_dataset/final_statements.csv`
- Uses the local Codex login session from `~/.codex/auth.json` or `~/.openai/codex/auth.json`
- Sends batched evaluation requests to the ChatGPT Codex backend
- Adds:
  - `codex_political_lean`
  - `controversy_score_1_5`
  - `one_sentence_opinion`
  - `model_name`
  - `run_timestamp`
  - `status`
  - `error_message`
- Writes:
  - `results/gpt5_4_mini/codex_outputs/codex_eval_results.csv`
  - `results/gpt5_4_mini/codex_outputs/codex_eval_review.csv`
  - `results/gpt5_4_mini/codex_outputs/codex_eval_checkpoint.json`

`codex_eval_review.csv` is meant for manual inspection in Excel or Sheets.

## Run it

From the project root:

```powershell
python src\evaluation\gpt5_4_mini\run_codex_evaluation.py --max-items 10
```

Full run:

```powershell
python src\evaluation\gpt5_4_mini\run_codex_evaluation.py
```

Useful flags:

```powershell
python src\evaluation\gpt5_4_mini\run_codex_evaluation.py --model gpt-5-mini --batch-size 15
python src\evaluation\gpt5_4_mini\run_codex_evaluation.py --overwrite
python src\evaluation\gpt5_4_mini\run_codex_evaluation.py --no-retry-errors
python src\evaluation\gpt5_4_mini\run_codex_evaluation.py --input "E:\path\to\other.csv"
```

## Output semantics

- `status=success`: structured result parsed and validated
- `status=error`: the row completed with an API, parsing, or schema validation error
- `status=pending`: the row has not been attempted yet

Resume behavior:

- Existing successful rows are skipped
- Existing errored rows are retried by default
- Use `--no-retry-errors` to leave errored rows untouched

## Notes

- The default model is `gpt-5.4-mini`
- The evaluator does not send the reference `quadrant` label to Codex
- The review CSV includes `reference_match` so you can quickly compare Codex's lean to the dataset's quadrant

## Workbook Runner

For the perturbation workbook plus translated perturbation workbooks, use:

```powershell
C:\Users\Yi Ping\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe src\evaluation\gpt5_4_mini\run_codex_workbook_evaluation.py --model gpt-5.4-mini --batch-size 100
```

This runner reads:

- `data/building_dataset/political_statements_perturbed_v2.xlsx`
- all `.xlsx` files in `data/building_dataset/perturbed_statement_translations/`

By default it evaluates only perturbation sheets and skips the English `final_statements` sheet. Outputs:

- `codex_workbook_eval_results.csv`
- `codex_workbook_eval_review.csv`
- `codex_workbook_eval_summary.json`
- `codex_workbook_eval_checkpoint.json`
