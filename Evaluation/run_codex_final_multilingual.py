import argparse
import logging
import sys
from pathlib import Path

from codex_eval.auth import CodexOAuthProvider
from codex_eval.multilingual_final_statements import (
    MultilingualFinalStatementsConfig,
    MultilingualFinalStatementsEvaluator,
    MultilingualFinalStatementsPaths,
)
from codex_eval.provider import CodexProvider, CodexProviderError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run Codex OAuth evaluation over multilingual columns in final_statements.xlsx."
    )
    parser.add_argument("--output-dir", dest="output_dir", help="Directory for checkpoint and CSV outputs.")
    parser.add_argument("--auth-path", default="", help="Optional explicit path to Codex auth.json.")
    parser.add_argument("--model", default="gpt-5.4-mini", help="Codex model name. Default: gpt-5.4-mini")
    parser.add_argument("--api-base", default="https://chatgpt.com/backend-api", help="Codex backend base URL.")
    parser.add_argument("--batch-size", type=int, default=25, help="Number of statements to evaluate per request.")
    parser.add_argument("--max-items", type=int, default=None, help="Optional cap for a smaller smoke test run.")
    parser.add_argument("--overwrite", action="store_true", help="Ignore any existing checkpoint and start from scratch.")
    parser.add_argument("--no-retry-errors", action="store_true", help="Resume without retrying rows that currently have status=error.")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"], help="Console log level.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    workspace_root = Path(__file__).resolve().parents[1]
    paths = MultilingualFinalStatementsPaths.defaults(
        workspace_root,
        output_dir=Path(args.output_dir).resolve() if args.output_dir else None,
    )
    config = MultilingualFinalStatementsConfig(
        model=args.model,
        batch_size=args.batch_size,
        max_items=args.max_items,
        overwrite=args.overwrite,
        retry_errors=not args.no_retry_errors,
    )

    oauth_provider = CodexOAuthProvider(auth_path=args.auth_path, cache_dir=paths.cache_dir)
    provider = CodexProvider(oauth_provider=oauth_provider, model=config.model, api_base=args.api_base)
    evaluator = MultilingualFinalStatementsEvaluator(provider=provider, paths=paths, config=config)

    try:
        summary = evaluator.run()
    except (CodexProviderError, RuntimeError) as exc:
        logging.getLogger(__name__).error("Multilingual final statement evaluation failed: %s", exc)
        return 1

    logging.getLogger(__name__).info(
        "Finished multilingual final statement evaluation. total=%s success=%s error=%s pending=%s",
        summary.get("total", 0),
        summary.get("success", 0),
        summary.get("error", 0),
        summary.get("pending", 0),
    )
    logging.getLogger(__name__).info("Machine output: %s", paths.machine_output_path)
    logging.getLogger(__name__).info("Review output: %s", paths.review_output_path)
    logging.getLogger(__name__).info("Summary output: %s", paths.summary_output_path)
    logging.getLogger(__name__).info("Checkpoint: %s", paths.checkpoint_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
