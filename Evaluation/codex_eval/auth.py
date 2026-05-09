import base64
import json
import logging
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Callable

logger = logging.getLogger(__name__)


def _utc_now() -> datetime:
    return datetime.now(UTC)


@dataclass
class AuthPaths:
    auth_path: str = ""
    cache_dir: Path = Path(".")


class CodexCredentialStore:
    def __init__(self, paths: AuthPaths):
        self.paths = paths

    def candidate_paths(self) -> list[Path]:
        candidates: list[Path] = []
        if self.paths.auth_path:
            candidates.append(Path(self.paths.auth_path).expanduser())
        candidates.extend(
            [
                Path.home() / ".codex" / "auth.json",
                Path.home() / ".openai" / "codex" / "auth.json",
            ]
        )
        return candidates

    def load_from_codex_cli(self):
        for path in self.candidate_paths():
            if path.exists():
                data = json.loads(path.read_text(encoding="utf-8"))
                logger.info("Loaded Codex credentials from %s", path)
                return {"path": str(path), "data": data}
        return None

    def load_from_local_cache(self):
        path = self.paths.cache_dir / "codex_auth.json"
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def save_local_cache(self, data):
        self.paths.cache_dir.mkdir(parents=True, exist_ok=True)
        path = self.paths.cache_dir / "codex_auth.json"
        path.write_text(json.dumps(data, indent=2, ensure_ascii=True), encoding="utf-8")
        return data


class CodexAuthManager:
    @staticmethod
    def _decode_jwt_payload(token: str) -> dict:
        if not token or token.count(".") < 2:
            return {}
        try:
            payload = token.split(".")[1]
            padding = "=" * (-len(payload) % 4)
            decoded = base64.urlsafe_b64decode(payload + padding)
            return json.loads(decoded.decode("utf-8"))
        except (ValueError, json.JSONDecodeError, UnicodeDecodeError):
            return {}

    @classmethod
    def _resolve_expiry(cls, credentials: dict | None):
        if not credentials:
            return None
        expires_at = credentials.get("expires_at")
        if expires_at:
            try:
                return datetime.fromisoformat(str(expires_at).replace("Z", "+00:00"))
            except ValueError:
                pass

        tokens = credentials.get("tokens") or {}
        for token_name in ("access_token", "id_token"):
            payload = cls._decode_jwt_payload(tokens.get(token_name, ""))
            exp = payload.get("exp")
            if exp:
                try:
                    return datetime.fromtimestamp(exp, tz=UTC)
                except (TypeError, ValueError, OSError):
                    continue
        return None

    @classmethod
    def summarize_credentials(cls, credentials: dict) -> dict:
        tokens = credentials.get("tokens") or {}
        id_payload = cls._decode_jwt_payload(tokens.get("id_token", ""))
        access_payload = cls._decode_jwt_payload(tokens.get("access_token", ""))
        expiry = cls._resolve_expiry(credentials)
        auth_profile = (
            id_payload.get("https://api.openai.com/auth")
            or access_payload.get("https://api.openai.com/auth")
            or {}
        )
        profile_payload = access_payload.get("https://api.openai.com/profile", {})
        return {
            "auth_mode": credentials.get("auth_mode", ""),
            "email": id_payload.get("email") or profile_payload.get("email", ""),
            "account_id": tokens.get("account_id") or auth_profile.get("chatgpt_account_id", ""),
            "plan_type": auth_profile.get("chatgpt_plan_type", ""),
            "expires_at": expiry.isoformat() if expiry else "",
            "last_refresh": credentials.get("last_refresh", ""),
            "scopes": access_payload.get("scp", []),
        }

    @classmethod
    def is_expired(cls, credentials: dict | None) -> bool:
        if not credentials:
            return True
        expiry = cls._resolve_expiry(credentials)
        if not expiry:
            return False
        return expiry <= _utc_now() + timedelta(minutes=5)

    @classmethod
    def refresh_if_needed(
        cls,
        credentials: dict | None,
        opener: Callable = urllib.request.urlopen,
    ):
        if not credentials:
            return None
        if not cls.is_expired(credentials):
            return credentials
        refreshed = cls.refresh_credentials(credentials, opener=opener)
        if refreshed:
            return refreshed
        updated = json.loads(json.dumps(credentials))
        updated["refresh_required"] = True
        updated["refreshed_at"] = _utc_now().isoformat()
        logger.warning("Codex credentials appear expired; manual `codex --login` may be required.")
        return updated

    @classmethod
    def refresh_credentials(
        cls,
        credentials: dict,
        opener: Callable = urllib.request.urlopen,
    ):
        tokens = credentials.get("tokens") or {}
        refresh_token = tokens.get("refresh_token")
        if not refresh_token:
            return None
        access_payload = cls._decode_jwt_payload(tokens.get("access_token", ""))
        id_payload = cls._decode_jwt_payload(tokens.get("id_token", ""))
        client_id = access_payload.get("client_id")
        if not client_id:
            audience = id_payload.get("aud") or []
            client_id = audience[0] if isinstance(audience, list) and audience else audience
        if not client_id:
            logger.warning("Codex credentials are refreshable in principle, but no client_id was found.")
            return None
        body = json.dumps(
            {
                "grant_type": "refresh_token",
                "client_id": client_id,
                "refresh_token": refresh_token,
            }
        ).encode("utf-8")
        request = urllib.request.Request(
            "https://auth0.openai.com/oauth/token",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with opener(request, timeout=20) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            logger.warning("Codex OAuth refresh failed with status %s.", exc.code)
            return None
        except OSError as exc:
            logger.warning("Codex OAuth refresh failed due to network or OS error: %s", exc)
            return None

        updated = json.loads(json.dumps(credentials))
        new_tokens = updated.setdefault("tokens", {})
        for key in ("access_token", "id_token", "refresh_token"):
            if payload.get(key):
                new_tokens[key] = payload[key]
        updated["last_refresh"] = _utc_now().isoformat()
        updated["refresh_required"] = False
        updated["refreshed_at"] = _utc_now().isoformat()
        logger.info("Refreshed Codex OAuth credentials through the OpenAI OAuth token endpoint.")
        return updated

    @classmethod
    def choose_best_credentials(cls, *candidates):
        best = None
        best_expiry = None
        for candidate in candidates:
            if not candidate:
                continue
            expiry = cls._resolve_expiry(candidate)
            if best is None:
                best = candidate
                best_expiry = expiry
                continue
            if best_expiry is None and expiry is not None:
                best = candidate
                best_expiry = expiry
                continue
            if best_expiry is not None and expiry is not None and expiry > best_expiry:
                best = candidate
                best_expiry = expiry
        return best


class CodexOAuthProvider:
    def __init__(
        self,
        auth_path: str = "",
        cache_dir: Path | None = None,
        opener: Callable = urllib.request.urlopen,
    ):
        self.store = CodexCredentialStore(
            AuthPaths(auth_path=auth_path, cache_dir=cache_dir or Path("."))
        )
        self.auth_manager = CodexAuthManager()
        self.opener = opener

    def ensure_ready(self) -> dict:
        source = self.store.load_from_codex_cli()
        cache = self.store.load_from_local_cache()
        credentials = None
        source_path = ""
        if source:
            credentials = self.auth_manager.choose_best_credentials(source["data"], cache)
            if credentials is source["data"]:
                source_path = source["path"]
            else:
                source_path = str(self.store.paths.cache_dir / "codex_auth.json")
        elif cache:
            credentials = cache
            source_path = str(self.store.paths.cache_dir / "codex_auth.json")

        if not credentials:
            return {"ready": False, "reason": "No Codex CLI credentials found."}

        credentials = self.auth_manager.refresh_if_needed(credentials, opener=self.opener)
        self.store.save_local_cache(credentials)
        return {
            "ready": not credentials.get("refresh_required", False),
            "reason": "" if not credentials.get("refresh_required") else "Credentials need refresh.",
            "credentials": credentials,
            "source_path": source_path,
            "summary": self.auth_manager.summarize_credentials(credentials),
        }
