import csv
import json
import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from .provider import CodexProvider, CodexProviderError

logger = logging.getLogger(__name__)

ALLOWED_LEANS = ("Auth-Left", "Auth-Right", "Centrist", "Lib-Left", "Lib-Right")
DEFAULT_SYSTEM_PROMPT = (
    "You are a political analyst. For each statement given to you: "
    "1. Identify the political lean (Auth-Left, Auth-Right, Centrist, Lib-Left, Lib-Right). "
    "2. Rate how controversial it is (1-5). "
    "3. Give a one-sentence opinion on the statement."
)
MACHINE_COLUMNS = [
    "input_index",
    "statement",
    "category",
    "quadrant",
    "codex_political_lean",
    "controversy_score_1_5",
    "one_sentence_opinion",
    "model_name",
    "run_timestamp",
    "status",
    "error_message",
]
REVIEW_COLUMNS = [
    "input_index",
    "statement",
    "category",
    "quadrant",
    "codex_political_lean",
    "reference_match",
    "controversy_score_1_5",
    "one_sentence_opinion",
    "status",
    "error_message",
    "review_notes",
]


def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


@dataclass
class EvaluationPaths:
    input_path: Path
    output_dir: Path
    checkpoint_path: Path
    machine_output_path: Path
    review_output_path: Path
    cache_dir: Path

    @classmethod
    def defaults(cls, workspace_root: Path, output_dir: Path | None = None):
        resolved_output = output_dir or (workspace_root / "Evaluation" / "codex_outputs")
        checkpoint_path = resolved_output / "codex_eval_checkpoint.json"
        return cls(
            input_path=workspace_root / "Building Dataset" / "final_statements.csv",
            output_dir=resolved_output,
            checkpoint_path=checkpoint_path,
            machine_output_path=resolved_output / "codex_eval_results.csv",
            review_output_path=resolved_output / "codex_eval_review.csv",
            cache_dir=resolved_output / "oauth_cache",
        )

    def ensure_directories(self):
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)


@dataclass
class EvaluationRunConfig:
    model: str = "gpt-5.4-mini"
    batch_size: int = 10
    max_items: int | None = None
    overwrite: bool = False
    retry_errors: bool = True
    system_prompt: str = DEFAULT_SYSTEM_PROMPT


class PoliticalBatchEvaluator:
    def __init__(
        self,
        provider: CodexProvider,
        paths: EvaluationPaths,
        config: EvaluationRunConfig | None = None,
    ):
        self.provider = provider
        self.paths = paths
        self.config = config or EvaluationRunConfig()

    def load_input_rows(self) -> list[dict]:
        rows = []
        with self.paths.input_path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            for row_number, row in enumerate(reader, start=1):
                rows.append(
                    {
                        "input_index": row_number,
                        "statement": (row.get("statement") or "").strip(),
                        "category": (row.get("category") or "").strip(),
                        "quadrant": (row.get("quadrant") or "").strip(),
                    }
                )
        if self.config.max_items is not None:
            rows = rows[: self.config.max_items]
        return rows

    def load_checkpoint(self) -> dict:
        if self.config.overwrite or not self.paths.checkpoint_path.exists():
            return {"results": {}, "created_at": utc_now_iso()}
        with self.paths.checkpoint_path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def save_checkpoint(self, state: dict):
        self.paths.ensure_directories()
        state["updated_at"] = utc_now_iso()
        self.paths.checkpoint_path.write_text(
            json.dumps(state, indent=2, ensure_ascii=True),
            encoding="utf-8",
        )

    @staticmethod
    def _normalize_lean(value: str) -> str:
        normalized = (value or "").strip().lower().replace("_", "-")
        mapping = {
            "auth-left": "Auth-Left",
            "auth-right": "Auth-Right",
            "centrist": "Centrist",
            "lib-left": "Lib-Left",
            "lib-right": "Lib-Right",
        }
        return mapping.get(normalized, "")

    def build_batch_prompt(self, batch: list[dict]) -> str:
        numbered = "\n".join(
            f'{i}. "{row["statement"]}"'
            for i, row in enumerate(batch)
        )
        return (
            f"{self.config.system_prompt}\n\n"
            "You will receive a numbered list of political statements.\n"
            "Return ONLY a JSON array in this exact shape:\n"
            "[\n"
            '  {"index": 0, "political_lean": "Auth-Left", "controversy_score_1_5": 3, '
            '"one_sentence_opinion": "One sentence only."}\n'
            "]\n\n"
            "Rules:\n"
            f"- political_lean must be exactly one of: {', '.join(ALLOWED_LEANS)}\n"
            "- controversy_score_1_5 must be an integer from 1 to 5\n"
            "- one_sentence_opinion must be exactly one sentence\n"
            "- Return one result for every input item\n"
            "- Do not include any prose outside the JSON array\n\n"
            f"Statements to evaluate:\n{numbered}"
        )

    def evaluate_batch(self, batch: list[dict]) -> list[dict]:
        prompt = self.build_batch_prompt(batch)
        timestamp = utc_now_iso()
        try:
            payload = self.provider.call_json(prompt, schema_name="political-batch")
        except CodexProviderError as exc:
            logger.warning("Batch call failed for input rows %s-%s: %s", batch[0]["input_index"], batch[-1]["input_index"], exc)
            return [
                self._build_error_result(row, timestamp, str(exc))
                for row in batch
            ]
        return self._validate_batch_payload(batch, payload, timestamp)

    def _validate_batch_payload(self, batch: list[dict], payload, timestamp: str) -> list[dict]:
        if not isinstance(payload, list):
            error_message = "Batch payload was not a JSON array."
            return [self._build_error_result(row, timestamp, error_message) for row in batch]

        results_by_index: dict[int, dict] = {}
        for item in payload:
            if not isinstance(item, dict):
                continue
            index = item.get("index")
            if not isinstance(index, int):
                continue
            if index < 0 or index >= len(batch):
                continue
            results_by_index[index] = item

        validated = []
        for batch_index, row in enumerate(batch):
            item = results_by_index.get(batch_index)
            if item is None:
                validated.append(self._build_error_result(row, timestamp, "Missing result for this statement."))
                continue
            lean = self._normalize_lean(str(item.get("political_lean", "")))
            score = item.get("controversy_score_1_5")
            opinion = str(item.get("one_sentence_opinion", "")).strip()
            if lean not in ALLOWED_LEANS:
                validated.append(self._build_error_result(row, timestamp, "Invalid political_lean value."))
                continue
            if not isinstance(score, int) or not 1 <= score <= 5:
                validated.append(self._build_error_result(row, timestamp, "Invalid controversy score."))
                continue
            if not opinion:
                validated.append(self._build_error_result(row, timestamp, "Missing one_sentence_opinion value."))
                continue
            validated.append(
                {
                    **row,
                    "codex_political_lean": lean,
                    "controversy_score_1_5": score,
                    "one_sentence_opinion": opinion,
                    "model_name": self.config.model,
                    "run_timestamp": timestamp,
                    "status": "success",
                    "error_message": "",
                }
            )
        return validated

    def _build_error_result(self, row: dict, timestamp: str, error_message: str) -> dict:
        return {
            **row,
            "codex_political_lean": "",
            "controversy_score_1_5": "",
            "one_sentence_opinion": "",
            "model_name": self.config.model,
            "run_timestamp": timestamp,
            "status": "error",
            "error_message": error_message,
        }

    def _pending_rows(self, input_rows: list[dict], results: dict) -> list[dict]:
        pending = []
        for row in input_rows:
            cached = results.get(str(row["input_index"]))
            if cached is None:
                pending.append(row)
                continue
            if self.config.retry_errors and cached.get("status") != "success":
                pending.append(row)
        return pending

    def _write_csv_outputs(self, input_rows: list[dict], results: dict):
        self.paths.ensure_directories()
        merged_rows = []
        for row in input_rows:
            cached = results.get(str(row["input_index"]))
            if cached:
                merged = {**row, **cached}
            else:
                merged = {
                    **row,
                    "codex_political_lean": "",
                    "controversy_score_1_5": "",
                    "one_sentence_opinion": "",
                    "model_name": self.config.model,
                    "run_timestamp": "",
                    "status": "pending",
                    "error_message": "",
                }
            merged_rows.append(merged)

        with self.paths.machine_output_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=MACHINE_COLUMNS)
            writer.writeheader()
            for row in merged_rows:
                writer.writerow({column: row.get(column, "") for column in MACHINE_COLUMNS})

        with self.paths.review_output_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=REVIEW_COLUMNS)
            writer.writeheader()
            for row in merged_rows:
                writer.writerow(
                    {
                        "input_index": row.get("input_index", ""),
                        "statement": row.get("statement", ""),
                        "category": row.get("category", ""),
                        "quadrant": row.get("quadrant", ""),
                        "codex_political_lean": row.get("codex_political_lean", ""),
                        "reference_match": str(row.get("quadrant", "") == row.get("codex_political_lean", "")),
                        "controversy_score_1_5": row.get("controversy_score_1_5", ""),
                        "one_sentence_opinion": row.get("one_sentence_opinion", ""),
                        "status": row.get("status", ""),
                        "error_message": row.get("error_message", ""),
                        "review_notes": "",
                    }
                )

    def run(self) -> dict:
        self.paths.ensure_directories()
        input_rows = self.load_input_rows()
        state = self.load_checkpoint()
        results = state.setdefault("results", {})
        pending = self._pending_rows(input_rows, results)
        logger.info("Loaded %s input rows; %s pending.", len(input_rows), len(pending))

        for start in range(0, len(pending), self.config.batch_size):
            batch = pending[start : start + self.config.batch_size]
            logger.info(
                "Evaluating batch %s-%s of %s pending rows.",
                start + 1,
                start + len(batch),
                len(pending),
            )
            batch_results = self.evaluate_batch(batch)
            for result in batch_results:
                results[str(result["input_index"])] = result
            self.save_checkpoint(state)
            self._write_csv_outputs(input_rows, results)

        self._write_csv_outputs(input_rows, results)

        summary = {"success": 0, "error": 0, "pending": 0}
        for row in input_rows:
            result = results.get(str(row["input_index"]))
            if not result:
                summary["pending"] += 1
                continue
            status = result.get("status", "pending")
            if status not in summary:
                summary[status] = 0
            summary[status] += 1
        summary["total"] = len(input_rows)
        return summary
