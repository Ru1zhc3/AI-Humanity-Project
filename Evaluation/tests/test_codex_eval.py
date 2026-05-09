import base64
import csv
import json
import sys
import unittest
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from codex_eval.auth import CodexAuthManager
from codex_eval.pipeline import EvaluationPaths, EvaluationRunConfig, PoliticalBatchEvaluator
from codex_eval.provider import CodexProvider


def build_jwt(payload: dict) -> str:
    encoded = base64.urlsafe_b64encode(json.dumps(payload).encode("utf-8")).decode("ascii").rstrip("=")
    return f"header.{encoded}.signature"


class CodexAuthManagerTests(unittest.TestCase):
    def test_summarize_credentials_prefers_account_id_and_resolves_expiry(self):
        access_token = build_jwt(
            {
                "exp": 4102444800,
                "scp": ["openid", "profile"],
                "https://api.openai.com/profile": {"email": "student@example.com"},
            }
        )
        credentials = {
            "auth_mode": "oauth",
            "tokens": {
                "access_token": access_token,
                "account_id": "acct_123",
            },
        }

        summary = CodexAuthManager.summarize_credentials(credentials)

        self.assertEqual(summary["account_id"], "acct_123")
        self.assertEqual(summary["email"], "student@example.com")
        self.assertTrue(summary["expires_at"].startswith("2100-"))


class CodexProviderTests(unittest.TestCase):
    def test_parse_and_extract_sse_output(self):
        raw = (
            b'data: {"type":"response.output_text.delta","delta":"Hello"}\n\n'
            b'data: {"type":"response.output_text.delta","delta":" world"}\n\n'
            b"data: [DONE]\n\n"
        )

        events = CodexProvider.parse_sse_json_lines(raw)
        text = CodexProvider.extract_output_text(events)

        self.assertEqual(text, "Hello world")


class FakeProvider:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = 0

    def call_json(self, prompt: str, schema_name: str):
        self.calls += 1
        if not self.responses:
            raise AssertionError("Unexpected provider call")
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


class PoliticalBatchEvaluatorTests(unittest.TestCase):
    def make_workspace_tempdir(self) -> Path:
        root = Path(__file__).resolve().parent / f"codex-eval-test-{uuid.uuid4().hex}"
        root.mkdir(parents=True, exist_ok=True)
        return root

    def create_input_csv(self, path: Path):
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["statement", "category", "quadrant"])
            writer.writeheader()
            writer.writerow(
                {
                    "statement": "Gun control laws would lower violent crime.",
                    "category": "Criminal justice",
                    "quadrant": "Auth-Left",
                }
            )
            writer.writerow(
                {
                    "statement": "Drug offenses should be treated as health issues.",
                    "category": "Criminal justice",
                    "quadrant": "Auth-Left",
                }
            )
            writer.writerow(
                {
                    "statement": "Markets work best with minimal regulation.",
                    "category": "Economic policy",
                    "quadrant": "Lib-Right",
                }
            )

    def test_run_writes_outputs_and_resume_skips_successes(self):
        root = self.make_workspace_tempdir()
        input_path = root / "final_statements.csv"
        output_dir = root / "outputs"
        self.create_input_csv(input_path)

        paths = EvaluationPaths(
            input_path=input_path,
            output_dir=output_dir,
            checkpoint_path=output_dir / "checkpoint.json",
            machine_output_path=output_dir / "results.csv",
            review_output_path=output_dir / "review.csv",
            cache_dir=output_dir / "oauth_cache",
        )
        provider = FakeProvider(
            [
                [
                    {
                        "index": 0,
                        "political_lean": "Auth-Left",
                        "controversy_score_1_5": 3,
                        "one_sentence_opinion": "This reflects a state-led public safety argument.",
                    },
                    {
                        "index": 1,
                        "political_lean": "Auth-Left",
                        "controversy_score_1_5": 2,
                        "one_sentence_opinion": "This frames drug policy as a health-centered intervention.",
                    },
                ],
                [
                    {
                        "index": 0,
                        "political_lean": "Lib-Right",
                        "controversy_score_1_5": 4,
                        "one_sentence_opinion": "This favors market autonomy over government control.",
                    }
                ],
            ]
        )

        evaluator = PoliticalBatchEvaluator(
            provider=provider,
            paths=paths,
            config=EvaluationRunConfig(batch_size=2),
        )
        summary = evaluator.run()

        self.assertEqual(summary["success"], 3)
        self.assertTrue(paths.machine_output_path.exists())
        self.assertTrue(paths.review_output_path.exists())
        self.assertEqual(provider.calls, 2)

        with paths.machine_output_path.open("r", encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[0]["codex_political_lean"], "Auth-Left")
        self.assertEqual(rows[2]["codex_political_lean"], "Lib-Right")

        resume_provider = FakeProvider([])
        resume_evaluator = PoliticalBatchEvaluator(
            provider=resume_provider,
            paths=paths,
            config=EvaluationRunConfig(batch_size=2),
        )
        resume_summary = resume_evaluator.run()
        self.assertEqual(resume_summary["success"], 3)
        self.assertEqual(resume_provider.calls, 0)

    def test_invalid_row_is_marked_error_without_crashing_whole_run(self):
        root = self.make_workspace_tempdir()
        input_path = root / "final_statements.csv"
        output_dir = root / "outputs"
        self.create_input_csv(input_path)

        paths = EvaluationPaths(
            input_path=input_path,
            output_dir=output_dir,
            checkpoint_path=output_dir / "checkpoint.json",
            machine_output_path=output_dir / "results.csv",
            review_output_path=output_dir / "review.csv",
            cache_dir=output_dir / "oauth_cache",
        )
        provider = FakeProvider(
            [
                [
                    {
                        "index": 0,
                        "political_lean": "Auth-Left",
                        "controversy_score_1_5": 3,
                        "one_sentence_opinion": "This reflects a state-led public safety argument.",
                    },
                    {
                        "index": 1,
                        "political_lean": "Invalid",
                        "controversy_score_1_5": 2,
                        "one_sentence_opinion": "Bad lean.",
                    },
                ],
                [
                    {
                        "index": 0,
                        "political_lean": "Lib-Right",
                        "controversy_score_1_5": 4,
                        "one_sentence_opinion": "This favors market autonomy over government control.",
                    }
                ],
            ]
        )

        evaluator = PoliticalBatchEvaluator(
            provider=provider,
            paths=paths,
            config=EvaluationRunConfig(batch_size=2, retry_errors=False),
        )
        summary = evaluator.run()

        self.assertEqual(summary["success"], 2)
        self.assertEqual(summary["error"], 1)

        with paths.machine_output_path.open("r", encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(rows[1]["status"], "error")
        self.assertIn("Invalid political_lean", rows[1]["error_message"])


if __name__ == "__main__":
    unittest.main()
