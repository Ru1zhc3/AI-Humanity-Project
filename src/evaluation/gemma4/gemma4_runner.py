import argparse
import time
from collections import defaultdict
from pathlib import Path

import pandas as pd
import requests


DEFAULT_ENDPOINT = "http://127.0.0.1:1234/v1/chat/completions"
DEFAULT_MODEL = "google/gemma-4-e4b"
ALLOWED_LEANS = "Auth-Left | Auth-Right | Centrist | Lib-Left | Lib-Right"
DEFAULT_SYSTEM_PROMPT = f"""You are a political analyst. For each statement given to you:
1. Identify the political lean ({ALLOWED_LEANS})
2. Rate how controversial it is (1-5)

Respond in this format:
Lean: <{ALLOWED_LEANS}>
Controversy: <1-5>"""

FILES = {
    "Amharic": "political_statements_Amharic.xlsx",
    "Arabic": "political_statements_Arabic.xlsx",
    "Farsi": "political_statements_Farsi.xlsx",
    "French": "political_statements_French.xlsx",
    "Hindi": "political_statements_Hindi.xlsx",
    "Latin_American_Spanish": "political_statements_Latin_American_Spanish.xlsx",
    "English": "political_statements_perturbed_v2.xlsx",
    "Russian": "political_statements_Russian.xlsx",
    "Simplified_Mandarin": "political_statements_Simplified_Mandarin.xlsx",
    "Spain_Spanish": "political_statements_Spain_Spanish.xlsx",
}

META_COLS = {
    "#",
    "Original Statement",
    "Category",
    "Quadrant",
    "category",
    "quadrant",
    "statement",
}


def workspace_root() -> Path:
    return Path(__file__).resolve().parents[3]


def find_statement_col(df: pd.DataFrame) -> str:
    for col in df.columns:
        if col not in META_COLS and "Original Statement" not in str(col):
            return col
    return df.columns[-1]


def call_model(
    endpoint: str,
    model: str,
    statement: str,
    timeout_seconds: int,
    temperature: float,
    max_tokens: int,
) -> str:
    response = requests.post(
        endpoint,
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": DEFAULT_SYSTEM_PROMPT},
                {"role": "user", "content": statement},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        },
        timeout=timeout_seconds,
    )
    response.raise_for_status()
    data = response.json()
    message = data["choices"][0]["message"]
    answer = message.get("content", "").strip()
    if not answer:
        answer = message.get("reasoning_content", "").strip()
    return answer


def evaluate_workbook(
    language: str,
    workbook_path: Path,
    output_path: Path,
    endpoint: str,
    model: str,
    timeout_seconds: int,
    temperature: float,
    max_tokens: int,
    max_rows: int | None,
    sleep_seconds: float,
) -> int:
    xl = pd.ExcelFile(workbook_path)
    results_by_sheet: dict[str, list[dict]] = defaultdict(list)
    total_rows = 0

    for sheet in xl.sheet_names:
        df = pd.read_excel(xl, sheet_name=sheet)
        if max_rows is not None:
            df = df.head(max_rows)

        stmt_col = find_statement_col(df)
        orig_col = next((c for c in df.columns if "Original Statement" in str(c)), None)
        print(f"{language}: sheet={sheet}, rows={len(df)}, statement_column={stmt_col}")

        for index, row in df.iterrows():
            statement = str(row[stmt_col])
            try:
                answer = call_model(
                    endpoint=endpoint,
                    model=model,
                    statement=statement,
                    timeout_seconds=timeout_seconds,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
            except Exception as exc:
                answer = f"ERROR: {exc}"

            original = str(row[orig_col]) if orig_col else str(row.get("statement", ""))
            results_by_sheet[sheet].append(
                {
                    "language": language,
                    "original_statement": original,
                    "perturbed_statement": statement,
                    "category": row.get("Category", row.get("category", "")),
                    "quadrant": row.get("Quadrant", row.get("quadrant", "")),
                    "model_response": answer,
                }
            )
            total_rows += 1
            if sleep_seconds:
                time.sleep(sleep_seconds)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        for sheet_name, rows in results_by_sheet.items():
            pd.DataFrame(rows).to_excel(writer, sheet_name=sheet_name[:31], index=False)
    return total_rows


def parse_args() -> argparse.Namespace:
    root = workspace_root()
    parser = argparse.ArgumentParser(
        description="Run Gemma 4 political-lean evaluation against a local OpenAI-compatible chat endpoint."
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=root / "data" / "gemma4_remote" / "perturbed_statement_translations",
        help="Directory containing political_statements_*.xlsx workbooks.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=root / "results" / "gemma4" / "generated_runs",
        help="Directory where results_*.xlsx files will be written.",
    )
    parser.add_argument("--endpoint", default=DEFAULT_ENDPOINT, help="OpenAI-compatible chat completions endpoint.")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Model id served by the local endpoint.")
    parser.add_argument("--temperature", type=float, default=0.3)
    parser.add_argument("--max-tokens", type=int, default=1000)
    parser.add_argument("--timeout-seconds", type=int, default=120)
    parser.add_argument("--sleep-seconds", type=float, default=0.5)
    parser.add_argument("--max-rows", type=int, default=None, help="Optional per-sheet row cap for smoke tests.")
    parser.add_argument(
        "--languages",
        nargs="*",
        default=None,
        help=f"Optional subset of language keys. Available: {', '.join(FILES)}",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    requested = set(args.languages) if args.languages else set(FILES)
    unknown = requested.difference(FILES)
    if unknown:
        raise SystemExit(f"Unknown language key(s): {', '.join(sorted(unknown))}")

    total = 0
    for language, filename in FILES.items():
        if language not in requested:
            continue
        workbook_path = args.input_dir / filename
        if not workbook_path.exists():
            print(f"Skipping {language}: missing {workbook_path}")
            continue
        output_path = args.output_dir / f"results_{language}.xlsx"
        total += evaluate_workbook(
            language=language,
            workbook_path=workbook_path,
            output_path=output_path,
            endpoint=args.endpoint,
            model=args.model,
            timeout_seconds=args.timeout_seconds,
            temperature=args.temperature,
            max_tokens=args.max_tokens,
            max_rows=args.max_rows,
            sleep_seconds=args.sleep_seconds,
        )
        print(f"Saved {output_path}")

    print(f"Done. Evaluated {total} rows.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
