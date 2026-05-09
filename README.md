# AI-Humanity-Project

This repository contains Team Cyan's CS4501 AI and Humanity project on political-content evaluation across languages, prompt perturbations, and model families. The project compares how two evaluators, GPT-5.4-mini through a Codex OAuth workflow and Gemma 4 through a local OpenAI-compatible endpoint, assign political-lean and controversy labels to the same underlying political statements.

## Project Question

Do political-content evaluations stay stable when the same ideas are translated across languages or reframed through different prompt perturbations?

The current results suggest that they do not. GPT-5.4-mini completed 2,250 multilingual final-statement rows and 28,350 perturbation rows. Only 53.8% of base source statements kept the same political-lean label across all 10 language versions, and only 13.6% of perturbation source statements kept the same lean across all 14 framing variants within a language. Gemma 4 results are stored separately so the two model families can be compared without mixing provenance.

## Repository Layout

```text
data/
  building_dataset/                         # Locally generated datasets and GPT-5.4-mini inputs
  gemma4_remote/perturbed_statement_translations/
                                             # Workbooks pulled from the remote Gemma 4 test repo

src/
  evaluation/gpt5_4_mini/                   # Codex OAuth evaluation package and runners
  evaluation/gemma4/                        # Local Gemma 4 runner
  analysis/                                 # Analysis scripts that generate tables, SVGs, and summaries

results/
  gpt5_4_mini/                              # GPT-5.4-mini checkpoints, CSVs, tables, figures
  gemma4/                                   # Gemma 4 result workbooks
  model_comparison/                         # Cross-model comparison outputs
  presentation/                             # Slide-build artifacts, previews, and presentation support
  back_tested_statement_translations/       # Earlier cross-language similarity outputs

docs/
  presentations/                            # Final and intermediate slide decks
  project_documents/                        # Proposal/update documents

notebooks/                                  # Dataset/evaluation notebooks
tests/                                      # Unit tests for the reusable evaluation framework
```

Ignored local runtime material such as `node_modules/`, OAuth caches, `__pycache__/`, and temporary render folders is intentionally not tracked.

## Setup

Use Python 3.11+ and install the Python dependencies:

```powershell
python -m pip install -r requirements.txt
```

The GPT-5.4-mini runner uses the local Codex/ChatGPT OAuth session from `~/.codex/auth.json` or `~/.openai/codex/auth.json`. The Gemma 4 runner expects a local OpenAI-compatible chat-completions server, such as LM Studio or another local model server, listening on `http://127.0.0.1:1234/v1/chat/completions` by default.

## Running Evaluations

Small GPT-5.4-mini smoke run:

```powershell
python src\evaluation\gpt5_4_mini\run_codex_evaluation.py --max-items 10
```

Multilingual final-statement run:

```powershell
python src\evaluation\gpt5_4_mini\run_codex_final_multilingual.py --model gpt-5.4-mini --batch-size 25
```

Perturbation workbook run:

```powershell
python src\evaluation\gpt5_4_mini\run_codex_workbook_evaluation.py --model gpt-5.4-mini --batch-size 100
```

Gemma 4 smoke run against a local endpoint:

```powershell
python src\evaluation\gemma4\gemma4_runner.py --languages English --max-rows 1 --sleep-seconds 0
```

Full Gemma 4 perturbation run:

```powershell
python src\evaluation\gemma4\gemma4_runner.py
```

## Reproducing Analysis

The main analysis outputs are already checked in under `results/`. To regenerate them:

```powershell
python src\analysis\analyze_codex_results.py
python src\analysis\model_comparison_analysis.py
python src\analysis\deep_presentation_analysis.py
python src\analysis\directionality_analysis.py
```

Generated summaries:

- `results/gpt5_4_mini/analysis/analysis_summary.md`
- `results/model_comparison/model_comparison_summary.md`
- `results/presentation/deep_presentation/deep_presentation_summary.md`
- `results/presentation/directionality/directionality_summary.md`

## Testing

Run the reusable Python unit tests:

```powershell
$env:PYTHONDONTWRITEBYTECODE=1
python -m unittest discover -s tests
```

Run syntax/import smoke checks:

```powershell
$env:PYTHONDONTWRITEBYTECODE=1
python -c "import ast, pathlib; [ast.parse(p.read_text(encoding='utf-8')) for p in pathlib.Path('src').rglob('*.py')]"
python src\evaluation\gpt5_4_mini\run_codex_evaluation.py --help
python src\evaluation\gemma4\gemma4_runner.py --help
```

Live model tests require external state: Codex OAuth credentials for GPT-5.4-mini, and a running local Gemma 4 endpoint for Gemma 4. Those are not required for unit tests.

## Notes

- `reference_match` compares model labels to the dataset quadrant label. It is useful as a consistency signal, not as objective ideological ground truth.
- GPT-5.4-mini outputs include machine CSVs, review CSVs, checkpoints, summaries, figures, and presentation-ready tables.
- Gemma 4 remote assets were pulled from `Ru1zhc3/AI-Humanity-Project` and kept separate from local GPT-5.4-mini assets to preserve provenance.
