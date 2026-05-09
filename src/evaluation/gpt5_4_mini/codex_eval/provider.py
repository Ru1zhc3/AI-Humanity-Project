import json
import logging
import http.client
import urllib.error
import urllib.request
import uuid
from typing import Callable
from urllib.parse import urlparse

from .auth import CodexOAuthProvider

logger = logging.getLogger(__name__)


class CodexProviderError(RuntimeError):
    pass


class CodexProvider:
    def __init__(
        self,
        oauth_provider: CodexOAuthProvider,
        model: str,
        api_base: str = "https://chatgpt.com/backend-api",
        timeout_seconds: int = 45,
        opener: Callable = urllib.request.urlopen,
        prompt_cache_prefix: str = "team-cyan-political-eval",
    ):
        self.oauth_provider = oauth_provider
        self.model = model
        self.api_base = api_base
        self.timeout_seconds = timeout_seconds
        self.opener = opener
        self.prompt_cache_prefix = prompt_cache_prefix

    @staticmethod
    def _build_request_id() -> str:
        return str(uuid.uuid4())

    def _resolve_codex_url(self) -> str:
        base = (self.api_base or "https://chatgpt.com/backend-api").rstrip("/")
        if base.endswith("/codex/responses"):
            return base
        if base.endswith("/codex"):
            return f"{base}/responses"
        return f"{base}/codex/responses"

    @staticmethod
    def parse_sse_json_lines(raw_bytes: bytes) -> list[dict]:
        events: list[dict] = []
        decoded = raw_bytes.decode("utf-8", "replace")
        for chunk in decoded.split("\n\n"):
            if not chunk.strip():
                continue
            data_lines = []
            for line in chunk.splitlines():
                if line.startswith("data:"):
                    payload = line[5:].strip()
                    if payload and payload != "[DONE]":
                        data_lines.append(payload)
            if not data_lines:
                continue
            try:
                events.append(json.loads("\n".join(data_lines)))
            except json.JSONDecodeError:
                continue
        return events

    @staticmethod
    def extract_output_text(events: list[dict]) -> str:
        message_text = []
        output_done_chunks = []
        deltas = []
        for event in events:
            event_type = event.get("type")
            if event_type == "response.output_text.done":
                text = event.get("text")
                if isinstance(text, str):
                    output_done_chunks.append(text)
            elif event_type == "response.output_text.delta":
                delta = event.get("delta")
                if isinstance(delta, str):
                    deltas.append(delta)
            elif event_type == "response.output_item.done":
                item = event.get("item") or {}
                if item.get("type") == "message":
                    for content in item.get("content", []):
                        if content.get("type") == "output_text" and isinstance(content.get("text"), str):
                            message_text.append(content["text"])
        if message_text:
            return "".join(message_text).strip()
        if output_done_chunks:
            return "".join(output_done_chunks).strip()
        return "".join(deltas).strip()

    @staticmethod
    def _extract_error_message(body: str) -> str:
        message = body
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            return message
        if isinstance(payload, dict):
            return (
                payload.get("detail")
                or payload.get("message")
                or (payload.get("error") or {}).get("message")
                or body
            )
        return message

    def _get_auth_state(self) -> dict:
        auth_state = self.oauth_provider.ensure_ready()
        if not auth_state["ready"]:
            raise CodexProviderError(auth_state["reason"] or "Codex provider is unavailable.")
        if not auth_state.get("summary", {}).get("account_id"):
            raise CodexProviderError(
                "Codex OAuth is connected, but no ChatGPT account id was found in the token."
            )
        return auth_state

    def _post_response(self, payload: dict) -> list[dict]:
        auth_state = self._get_auth_state()
        token = auth_state["credentials"]["tokens"]["access_token"]
        account_id = auth_state["summary"]["account_id"]
        endpoint = self._resolve_codex_url()
        parsed = urlparse(endpoint)
        user_agent = f"team-cyan-eval ({parsed.scheme or 'https'} backend bridge)"
        request = urllib.request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {token}",
                "chatgpt-account-id": account_id,
                "originator": "pi",
                "User-Agent": user_agent,
                "OpenAI-Beta": "responses=experimental",
                "accept": "text/event-stream",
                "Content-Type": "application/json",
                "session_id": self._build_request_id(),
            },
            method="POST",
        )
        try:
            with self.opener(request, timeout=self.timeout_seconds) as response:
                return self.parse_sse_json_lines(response.read())
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", "replace")
            logger.warning("Codex backend response call failed with status %s: %s", exc.code, body)
            raise CodexProviderError(self._extract_error_message(body)) from exc
        except http.client.IncompleteRead as exc:
            raise CodexProviderError(f"Codex backend stream ended early: {exc}") from exc
        except OSError as exc:
            raise CodexProviderError(f"Codex backend network error: {exc}") from exc

    def call_json(
        self,
        prompt: str,
        schema_name: str,
        instructions: str = "Return only valid JSON and no surrounding prose.",
    ) -> list | dict:
        response = self._post_response(
            {
                "model": self.model,
                "store": False,
                "stream": True,
                "instructions": instructions,
                "input": [
                    {
                        "role": "user",
                        "content": [{"type": "input_text", "text": prompt}],
                    }
                ],
                "text": {"verbosity": "low"},
                "include": ["reasoning.encrypted_content"],
                "prompt_cache_key": f"{self.prompt_cache_prefix}-{schema_name}",
                "tool_choice": "auto",
                "parallel_tool_calls": True,
            }
        )
        text = self.extract_output_text(response)
        if not text:
            raise CodexProviderError("Codex returned an empty structured response.")
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise CodexProviderError(f"Codex returned invalid JSON: {text}") from exc
