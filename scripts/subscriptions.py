#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "requests>=2.32.0",
#   "rich>=13.7.0",
#   "PyYAML>=6.0.0",
# ]
# ///

from __future__ import annotations

import argparse
import base64
import json
import os
import shutil
import subprocess
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
import yaml
from rich import box
from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text


CACHE_DIR = Path.home() / ".cache" / "ai-usage-lite"

CLAUDE_CREDS = Path.home() / ".claude" / ".credentials.json"

CODEX_AUTH_CANDIDATES = [
    Path.home() / ".codex" / "auth.json",
    Path.home() / ".pi" / "agent" / "auth.json",
]

OPENCODE_AUTH = Path.home() / ".local" / "share" / "opencode" / "auth.json"

COPILOT_AUTH_CANDIDATES = [
    Path.home() / ".config" / "github-copilot" / "apps.json",
    Path.home() / ".config" / "github-copilot" / "hosts.json",
    Path.home() / ".config" / "gh" / "hosts.yml",
    Path.home() / ".config" / "gh" / "hosts.yaml",
]

CLAUDE_USAGE_URL = "https://api.anthropic.com/api/oauth/usage"
CLAUDE_TOKEN_URL = "https://platform.claude.com/v1/oauth/token"
CLAUDE_CLIENT_ID = "9d1c250a-e61b-44d9-88ed-5944d1962f5e"

CODEX_USAGE_URL = "https://chatgpt.com/backend-api/wham/usage"
CODEX_TOKEN_URL = "https://auth.openai.com/oauth/token"
CODEX_CLIENT_ID = "app_EMoamEEZ73f0CkXaXp7hrann"

GITHUB_API_USER_URL = "https://api.github.com/user"
GITHUB_COPILOT_TOKEN_URL = "https://api.github.com/copilot_internal/v2/token"

REFRESH_BUFFER_SECONDS = 300
DEFAULT_CACHE_TTL_SECONDS = 60

WINDOW_DURATIONS_SECONDS = {
    "session_5h": 5 * 60 * 60,
    "weekly_7d": 7 * 24 * 60 * 60,
    "sonnet_7d": 7 * 24 * 60 * 60,
    "code_review": 7 * 24 * 60 * 60,
}

SECRET_KEY_PARTS = (
    "token",
    "access",
    "refresh",
    "secret",
    "password",
    "authorization",
    "api_key",
    "apikey",
    "key",
)


@dataclass
class Window:
    name: str
    used_percent: float | None = None
    remaining_percent: float | None = None
    reset_at: str | None = None
    reset_in: str | None = None
    elapsed_percent: float | None = None
    burn_delta_points: float | None = None
    burn_status: str | None = None
    risk: str | None = None


@dataclass
class ProviderReport:
    provider: str
    status: str
    plan: str | None = None
    headline: str | None = None
    windows: list[Window] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)
    diagnostics: list[str] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)
    cached: bool = False


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, dict) else {"value": data}


def read_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data if isinstance(data, dict) else {"value": data}


def write_json_atomic(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    tmp.replace(path)


def cache_path(name: str) -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = name.replace("/", "_").replace(":", "_")
    return CACHE_DIR / f"{safe_name}.json"


def get_cached(name: str, ttl: int) -> tuple[dict[str, Any] | None, bool]:
    path = cache_path(name)
    if not path.exists():
        return None, False

    age = time.time() - path.stat().st_mtime
    if age > ttl:
        return None, False

    return read_json(path), True


def set_cached(name: str, data: dict[str, Any]) -> None:
    write_json_atomic(cache_path(name), data)


def http_json(
    *,
    cache_name: str,
    cache_ttl: int,
    no_cache: bool,
    method: str,
    url: str,
    headers: dict[str, str] | None = None,
    json_body: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], bool]:
    method = method.upper()

    if method == "GET" and not no_cache:
        cached, ok = get_cached(cache_name, cache_ttl)
        if ok and cached is not None:
            return cached, True

    response = requests.request(
        method,
        url,
        headers=headers,
        json=json_body,
        timeout=25,
    )

    if response.status_code >= 400:
        body = response.text[:700].replace("\n", " ")
        raise RuntimeError(f"HTTP {response.status_code}: {body}")

    data = response.json()
    if not isinstance(data, dict):
        data = {"value": data}

    if method == "GET":
        set_cached(cache_name, data)

    return data, False


def to_epoch(value: str | int | float | None) -> float | None:
    if value is None:
        return None

    if isinstance(value, str):
        try:
            normalized = value.replace("Z", "+00:00")
            return datetime.fromisoformat(normalized).timestamp()
        except Exception:
            try:
                return float(value)
            except Exception:
                return None

    return float(value)


def epoch_to_iso(value: int | float | None) -> str | None:
    if value is None:
        return None

    return datetime.fromtimestamp(float(value), tz=timezone.utc).isoformat(timespec="seconds")


def duration_until(value: str | int | float | None) -> str | None:
    epoch = to_epoch(value)
    if epoch is None:
        return None

    seconds = int(epoch - time.time())
    if seconds <= 0:
        return "now"

    days = seconds // 86_400
    hours = (seconds % 86_400) // 3_600
    minutes = (seconds % 3_600) // 60

    if days:
        return f"{days}d {hours}h"

    return f"{hours}h {minutes:02d}m"


def decode_jwt_payload(token: str | None) -> dict[str, Any]:
    if not token:
        return {}

    try:
        payload = token.split(".")[1]
        payload += "=" * (-len(payload) % 4)
        raw = base64.urlsafe_b64decode(payload.encode())
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def jwt_exp(token: str | None) -> int:
    payload = decode_jwt_payload(token)
    return int(payload.get("exp") or 0)


def redact(value: Any, key_hint: str = "") -> Any:
    key_lower = key_hint.lower()

    if any(part in key_lower for part in SECRET_KEY_PARTS):
        if value is None or value == "":
            return value
        return "<redacted>"

    if isinstance(value, dict):
        return {str(k): redact(v, str(k)) for k, v in value.items()}

    if isinstance(value, list):
        return [redact(item, key_hint) for item in value]

    return value


def sorted_keys(value: Any) -> list[str]:
    if isinstance(value, dict):
        return sorted(str(k) for k in value.keys())

    return []


def elapsed_percent_for_window(
    name: str,
    reset: str | int | float | None,
) -> float | None:
    duration = WINDOW_DURATIONS_SECONDS.get(name)
    reset_epoch = to_epoch(reset)

    if not duration or reset_epoch is None:
        return None

    start_epoch = reset_epoch - duration
    elapsed = ((time.time() - start_epoch) / duration) * 100
    elapsed = max(0.0, min(100.0, elapsed))

    return round(elapsed, 1)


def burn_status(
    *,
    used_percent: float | None,
    elapsed_percent: float | None,
    tolerance_points: float = 5.0,
) -> tuple[str | None, float | None]:
    if used_percent is None or elapsed_percent is None:
        return None, None

    delta = round(used_percent - elapsed_percent, 1)

    if delta > tolerance_points:
        return "overspending", delta

    if delta < -tolerance_points:
        return "conserving", delta

    return "steady", delta


def risk_level(
    *,
    used_percent: float | None,
    remaining_percent: float | None,
    burn: str | None,
) -> str | None:
    if used_percent is None:
        return None

    if remaining_percent is not None and remaining_percent <= 0:
        return "exhausted"

    if used_percent >= 90:
        return "critical"

    if used_percent >= 75:
        return "high"

    if burn == "overspending":
        return "watch"

    return "ok"


def make_window(name: str, used: Any, reset: Any) -> Window:
    try:
        used_percent = round(float(used), 1)
    except Exception:
        used_percent = None

    reset_at = epoch_to_iso(reset) if isinstance(reset, (int, float)) else reset

    remaining = None
    if used_percent is not None:
        remaining = max(0.0, round(100.0 - used_percent, 1))

    elapsed = elapsed_percent_for_window(name, reset)
    burn, delta = burn_status(
        used_percent=used_percent,
        elapsed_percent=elapsed,
    )

    return Window(
        name=name,
        used_percent=used_percent,
        remaining_percent=remaining,
        reset_at=reset_at,
        reset_in=duration_until(reset),
        elapsed_percent=elapsed,
        burn_delta_points=delta,
        burn_status=burn,
        risk=risk_level(
            used_percent=used_percent,
            remaining_percent=remaining,
            burn=burn,
        ),
    )


def percent_from_amounts(used: Any, limit: Any) -> float | None:
    try:
        used_f = float(used)
        limit_f = float(limit)

        if limit_f <= 0:
            return None

        return round((used_f / limit_f) * 100, 1)
    except Exception:
        return None


def remaining_amount(used: Any, limit: Any) -> float | None:
    try:
        return round(max(0.0, float(limit) - float(used)), 2)
    except Exception:
        return None


def as_range(value: Any) -> str | None:
    if isinstance(value, list) and len(value) == 2:
        return f"{value[0]}-{value[1]}"

    if value is None:
        return None

    return str(value)


def claude_refresh_if_needed(creds: dict[str, Any]) -> dict[str, Any]:
    oauth = creds.get("claudeAiOauth") or {}

    access_token = oauth.get("accessToken")
    refresh_token = oauth.get("refreshToken")
    expires_at_ms = int(float(oauth.get("expiresAt") or 0))
    expires_at_s = expires_at_ms // 1000

    if not access_token or not refresh_token:
        raise RuntimeError("Missing Claude OAuth tokens. Run `claude` and login again.")

    if expires_at_s > int(time.time()) + REFRESH_BUFFER_SECONDS:
        return creds

    body = {
        "grant_type": "refresh_token",
        "client_id": CLAUDE_CLIENT_ID,
        "refresh_token": refresh_token,
    }

    data, _ = http_json(
        cache_name="claude-token-refresh-never-cache",
        cache_ttl=0,
        no_cache=True,
        method="POST",
        url=CLAUDE_TOKEN_URL,
        headers={
            "Content-Type": "application/json",
            "anthropic-beta": "oauth-2025-04-20",
            "User-Agent": "claude-cli/1.0",
        },
        json_body=body,
    )

    oauth["accessToken"] = data["access_token"]
    oauth["refreshToken"] = data.get("refresh_token") or refresh_token
    oauth["expiresAt"] = int((time.time() + int(data.get("expires_in", 3600))) * 1000)

    creds["claudeAiOauth"] = oauth
    write_json_atomic(CLAUDE_CREDS, creds)

    return creds


def report_claude(args: argparse.Namespace) -> ProviderReport:
    try:
        if not CLAUDE_CREDS.exists():
            return ProviderReport(
                provider="claude",
                status="unavailable",
                headline="Claude credentials not found.",
                diagnostics=[
                    f"Missing file: {CLAUDE_CREDS}",
                    "Run `claude` and login first.",
                ],
            )

        creds = read_json(CLAUDE_CREDS)
        creds = claude_refresh_if_needed(creds)
        oauth = creds["claudeAiOauth"]

        usage, cached = http_json(
            cache_name="claude-usage",
            cache_ttl=args.cache_ttl,
            no_cache=args.no_cache,
            method="GET",
            url=CLAUDE_USAGE_URL,
            headers={
                "Authorization": f"Bearer {oauth['accessToken']}",
                "anthropic-beta": "oauth-2025-04-20",
            },
        )

        plan = str(oauth.get("subscriptionType") or "unknown")
        tier = str(oauth.get("rateLimitTier") or "")

        if "5x" in tier:
            plan += " 5x"
        elif "20x" in tier:
            plan += " 20x"

        windows: list[Window] = []
        window_sources = {
            "session_5h": usage.get("five_hour") or {},
            "weekly_7d": usage.get("seven_day") or {},
            "sonnet_7d": usage.get("seven_day_sonnet") or {},
        }

        for name, source in window_sources.items():
            if source:
                windows.append(
                    make_window(
                        name,
                        source.get("utilization"),
                        source.get("resets_at"),
                    )
                )

        extra_usage = usage.get("extra_usage") or {}

        details: dict[str, Any] = {
            "auth_source": str(CLAUDE_CREDS),
            "subscription_type": oauth.get("subscriptionType"),
            "rate_limit_tier": oauth.get("rateLimitTier"),
            "oauth_expires_at": epoch_to_iso(
                (int(float(oauth.get("expiresAt") or 0)) // 1000) or None
            ),
            "usage_response_keys": sorted_keys(usage),
            "extra_usage_enabled": extra_usage.get("is_enabled"),
            "extra_used_credits": extra_usage.get("used_credits"),
            "extra_monthly_limit": extra_usage.get("monthly_limit"),
            "extra_remaining_credits": remaining_amount(
                extra_usage.get("used_credits"),
                extra_usage.get("monthly_limit"),
            ),
            "extra_usage_percent": percent_from_amounts(
                extra_usage.get("used_credits"),
                extra_usage.get("monthly_limit"),
            ),
        }

        exhausted = [w.name for w in windows if w.risk == "exhausted"]
        headline = "Usage available."

        if exhausted:
            headline = "Exhausted: " + ", ".join(exhausted)

        return ProviderReport(
            provider="claude",
            status="ok",
            plan=plan,
            headline=headline,
            windows=windows,
            details=details,
            raw={"usage": redact(usage)} if args.raw else {},
            cached=cached,
        )

    except Exception as e:
        return ProviderReport(
            provider="claude",
            status="error",
            headline="Claude request failed.",
            diagnostics=[str(e)],
        )


def find_codex_auth_file(args: argparse.Namespace) -> Path | None:
    if args.codex_auth:
        path = Path(args.codex_auth).expanduser()
        return path if path.exists() else None

    for path in CODEX_AUTH_CANDIDATES:
        if path.exists():
            return path

    return None


def load_codex_credentials(path: Path) -> tuple[dict[str, Any], str]:
    raw = read_json(path)

    if isinstance(raw.get("tokens"), dict):
        return raw, "codex-cli"

    if isinstance(raw.get("openai-codex"), dict):
        return raw, "openai-codex"

    for key, value in raw.items():
        if key.startswith("openai-codex") and isinstance(value, dict):
            if value.get("access") and value.get("refresh"):
                return raw, key

    raise RuntimeError(
        f"Found {path}, but could not find Codex OAuth credentials. "
        "Expected `tokens` or `openai-codex`."
    )


def get_codex_tokens(creds: dict[str, Any], schema: str) -> dict[str, Any]:
    if schema == "codex-cli":
        tokens = creds.get("tokens") or {}

        return {
            "access_token": tokens.get("access_token"),
            "refresh_token": tokens.get("refresh_token"),
            "id_token": tokens.get("id_token"),
            "account_id": tokens.get("account_id"),
            "expires_at_ms": None,
        }

    pi_tokens = creds.get(schema) or {}

    return {
        "access_token": pi_tokens.get("access"),
        "refresh_token": pi_tokens.get("refresh"),
        "id_token": pi_tokens.get("id"),
        "account_id": pi_tokens.get("account_id"),
        "expires_at_ms": pi_tokens.get("expires"),
    }


def save_codex_tokens(
    path: Path,
    creds: dict[str, Any],
    schema: str,
    refreshed: dict[str, Any],
) -> None:
    if schema == "codex-cli":
        tokens = creds.setdefault("tokens", {})
        tokens["access_token"] = refreshed.get("access_token") or tokens.get("access_token")
        tokens["refresh_token"] = refreshed.get("refresh_token") or tokens.get("refresh_token")

        if refreshed.get("id_token"):
            tokens["id_token"] = refreshed["id_token"]

        creds["last_refresh"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        write_json_atomic(path, creds)
        return

    pi_tokens = creds.setdefault(schema, {})
    pi_tokens["access"] = refreshed.get("access_token") or pi_tokens.get("access")
    pi_tokens["refresh"] = refreshed.get("refresh_token") or pi_tokens.get("refresh")

    if refreshed.get("expires_in"):
        pi_tokens["expires"] = int((time.time() + int(refreshed["expires_in"])) * 1000)

    if refreshed.get("id_token"):
        pi_tokens["id"] = refreshed["id_token"]

    write_json_atomic(path, creds)


def codex_access_token_expired(tokens: dict[str, Any]) -> bool:
    expires_at_ms = tokens.get("expires_at_ms")

    if expires_at_ms:
        try:
            expires_at_s = int(float(expires_at_ms)) // 1000
            return expires_at_s <= int(time.time()) + REFRESH_BUFFER_SECONDS
        except Exception:
            pass

    exp = jwt_exp(tokens.get("access_token"))

    if exp:
        return exp <= int(time.time()) + REFRESH_BUFFER_SECONDS

    return True


def codex_refresh_if_needed(
    path: Path,
    creds: dict[str, Any],
    schema: str,
) -> dict[str, Any]:
    tokens = get_codex_tokens(creds, schema)

    if not tokens.get("access_token") or not tokens.get("refresh_token"):
        raise RuntimeError(
            "Missing Codex OAuth tokens. For Pi, run `pi`, then `/login`, "
            "then select ChatGPT Plus/Pro / Codex."
        )

    if not codex_access_token_expired(tokens):
        return creds

    body = {
        "client_id": CODEX_CLIENT_ID,
        "grant_type": "refresh_token",
        "refresh_token": tokens["refresh_token"],
        "scope": "openid profile email",
    }

    data, _ = http_json(
        cache_name="codex-token-refresh-never-cache",
        cache_ttl=0,
        no_cache=True,
        method="POST",
        url=CODEX_TOKEN_URL,
        headers={"Content-Type": "application/json"},
        json_body=body,
    )

    save_codex_tokens(path, creds, schema, data)
    return read_json(path)


def report_codex(args: argparse.Namespace) -> ProviderReport:
    try:
        auth_path = find_codex_auth_file(args)

        if not auth_path:
            return ProviderReport(
                provider="codex",
                status="unavailable",
                headline="Codex credentials not found.",
                diagnostics=[
                    "Tried ~/.codex/auth.json and ~/.pi/agent/auth.json.",
                    "For Pi, run `pi`, then `/login`, then select ChatGPT Plus/Pro / Codex.",
                ],
            )

        creds, schema = load_codex_credentials(auth_path)
        creds = codex_refresh_if_needed(auth_path, creds, schema)
        tokens = get_codex_tokens(creds, schema)
        access_token = tokens.get("access_token")

        if not access_token:
            raise RuntimeError(f"No Codex access token found in {auth_path}")

        headers = {"Authorization": f"Bearer {access_token}"}

        if tokens.get("account_id"):
            headers["chatgpt-account-id"] = tokens["account_id"]

        usage, cached = http_json(
            cache_name=f"codex-usage-{schema}",
            cache_ttl=args.cache_ttl,
            no_cache=args.no_cache,
            method="GET",
            url=CODEX_USAGE_URL,
            headers=headers,
        )

        id_claims = decode_jwt_payload(tokens.get("id_token"))
        access_claims = decode_jwt_payload(access_token)
        auth_claims = id_claims.get("https://api.openai.com/auth") or {}

        plan = usage.get("plan_type") or auth_claims.get("chatgpt_plan_type") or "unknown"

        windows: list[Window] = []
        rate = usage.get("rate_limit") or {}
        primary = rate.get("primary_window") or {}
        secondary = rate.get("secondary_window") or {}

        if primary:
            windows.append(
                make_window(
                    "session_5h",
                    primary.get("used_percent"),
                    primary.get("reset_at"),
                )
            )

        if secondary:
            windows.append(
                make_window(
                    "weekly_7d",
                    secondary.get("used_percent"),
                    secondary.get("reset_at"),
                )
            )

        code_review = usage.get("code_review_rate_limit") or {}
        review_primary = code_review.get("primary_window") or {}

        if review_primary:
            windows.append(
                make_window(
                    "code_review",
                    review_primary.get("used_percent"),
                    review_primary.get("reset_at"),
                )
            )

        credits = usage.get("credits") or {}

        details = {
            "auth_source": str(auth_path),
            "auth_schema": schema,
            "access_token_expires_at": epoch_to_iso(jwt_exp(access_token)) if jwt_exp(access_token) else None,
            "plan_type": usage.get("plan_type"),
            "rate_limit_allowed": rate.get("allowed"),
            "rate_limit_reached": rate.get("limit_reached"),
            "rate_limit_reached_type": usage.get("rate_limit_reached_type"),
            "credits_balance": credits.get("balance"),
            "credits_unlimited": credits.get("unlimited"),
            "approx_local_messages": as_range(credits.get("approx_local_messages")),
            "approx_cloud_messages": as_range(credits.get("approx_cloud_messages")),
            "spend_control": usage.get("spend_control"),
            "promo": usage.get("promo"),
            "additional_rate_limits_keys": sorted_keys(usage.get("additional_rate_limits")),
            "usage_response_keys": sorted_keys(usage),
            "rate_limit_keys": sorted_keys(rate),
            "code_review_rate_limit_keys": sorted_keys(code_review),
            "jwt_plan": auth_claims.get("chatgpt_plan_type"),
            "jwt_has_openai_auth_claim": bool(access_claims.get("https://api.openai.com/auth")),
            "account_id_present": bool(tokens.get("account_id")),
            "usage_account_id_present": bool(usage.get("account_id")),
            "email_present": bool(usage.get("email")),
            "user_id_present": bool(usage.get("user_id")),
        }

        exhausted = [w.name for w in windows if w.risk == "exhausted"]
        headline = "Usage available."

        if exhausted:
            headline = "Exhausted: " + ", ".join(exhausted)

        return ProviderReport(
            provider="codex",
            status="ok",
            plan=str(plan),
            headline=headline,
            windows=windows,
            details=details,
            raw={"usage": redact(usage)} if args.raw else {},
            cached=cached,
        )

    except Exception as e:
        return ProviderReport(
            provider="codex",
            status="error",
            headline="Codex request failed.",
            diagnostics=[str(e)],
        )


def recursive_find_token(data: Any, path: str = "") -> tuple[str | None, str | None]:
    if isinstance(data, dict):
        priority_keys = [
            "oauth_token",
            "oauthToken",
            "user_token",
            "github_token",
            "token",
        ]

        for key in priority_keys:
            value = data.get(key)
            if isinstance(value, str) and value:
                return value, f"{path}.{key}".strip(".")

        users = data.get("users")

        if isinstance(users, dict):
            for user_name, user_data in users.items():
                token, token_path = recursive_find_token(
                    user_data,
                    f"{path}.users.{user_name}".strip("."),
                )

                if token:
                    return token, token_path

        for key, value in data.items():
            token, token_path = recursive_find_token(
                value,
                f"{path}.{key}".strip("."),
            )

            if token:
                return token, token_path

    if isinstance(data, list):
        for index, item in enumerate(data):
            token, token_path = recursive_find_token(item, f"{path}[{index}]")

            if token:
                return token, token_path

    return None, None


def run_gh_auth_token() -> tuple[str | None, str | None]:
    gh = shutil.which("gh")

    if not gh:
        return None, "gh executable not found"

    try:
        result = subprocess.run(
            [gh, "auth", "token"],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=5,
        )
    except Exception as e:
        return None, f"gh auth token failed: {e}"

    token = result.stdout.strip()

    if result.returncode == 0 and token:
        return token, "gh auth token"

    err = result.stderr.strip() or "gh auth token returned no token"
    return None, err


def load_token_from_file(path: Path) -> tuple[str | None, str | None, dict[str, Any]]:
    try:
        data = read_yaml(path) if path.suffix.lower() in {".yml", ".yaml"} else read_json(path)
    except Exception as e:
        return None, f"could not read {path}: {e}", {}

    token, token_path = recursive_find_token(data)

    if token:
        return token, token_path or str(path), data

    return None, f"no token-like field found in {path}", data


def discover_github_token(args: argparse.Namespace) -> tuple[str | None, dict[str, Any], list[str]]:
    details: dict[str, Any] = {
        "auth_sources_tried": [],
        "auth_source": None,
        "auth_source_kind": None,
        "auth_token_path": None,
    }

    diagnostics: list[str] = []

    if args.copilot_token:
        details.update(
            {
                "auth_source": "--copilot-token",
                "auth_source_kind": "cli_argument",
                "auth_token_path": "argument",
            }
        )
        return args.copilot_token, details, diagnostics

    for env_name in ("GH_TOKEN", "GITHUB_TOKEN"):
        token = os.getenv(env_name)
        details["auth_sources_tried"].append(env_name)

        if token:
            details.update(
                {
                    "auth_source": env_name,
                    "auth_source_kind": "environment",
                    "auth_token_path": env_name,
                }
            )
            return token, details, diagnostics

    token, gh_diag = run_gh_auth_token()
    details["auth_sources_tried"].append("gh auth token")

    if token:
        details.update(
            {
                "auth_source": "gh auth token",
                "auth_source_kind": "github_cli_secure_store",
                "auth_token_path": "credential_store_or_gh_config",
            }
        )
        return token, details, diagnostics

    if gh_diag:
        diagnostics.append(gh_diag)

    candidate_paths = [Path(args.copilot_auth).expanduser()] if args.copilot_auth else COPILOT_AUTH_CANDIDATES

    for path in candidate_paths:
        details["auth_sources_tried"].append(str(path))

        if not path.exists():
            diagnostics.append(f"missing: {path}")
            continue

        token, token_path, raw_file_data = load_token_from_file(path)
        details[f"file_keys:{path}"] = sorted_keys(raw_file_data)

        if token:
            details.update(
                {
                    "auth_source": str(path),
                    "auth_source_kind": "file",
                    "auth_token_path": token_path,
                }
            )
            return token, details, diagnostics

        if token_path:
            diagnostics.append(token_path)

    return None, details, diagnostics


def report_copilot(args: argparse.Namespace) -> ProviderReport:
    try:
        github_token, auth_details, diagnostics = discover_github_token(args)

        if not github_token:
            return ProviderReport(
                provider="copilot",
                status="unavailable",
                plan="unknown",
                headline="GitHub auth token not found.",
                details=auth_details
                | {
                    "next_step": "Run `gh auth login`, or login to GitHub Copilot in your IDE.",
                    "why_not_error": "No token was found; this is configuration, not a provider failure.",
                },
                diagnostics=diagnostics,
            )

        cached_any = False
        user: dict[str, Any] = {}

        try:
            user, cached = http_json(
                cache_name="github-user",
                cache_ttl=args.cache_ttl,
                no_cache=args.no_cache,
                method="GET",
                url=GITHUB_API_USER_URL,
                headers={
                    "Authorization": f"Bearer {github_token}",
                    "Accept": "application/vnd.github+json",
                    "User-Agent": "ai-usage-lite",
                },
            )
            cached_any = cached_any or cached
        except Exception as e:
            diagnostics.append(f"GitHub /user failed: {e}")

        copilot_token_response: dict[str, Any] = {}
        copilot_token_error: str | None = None

        try:
            copilot_token_response, cached = http_json(
                cache_name="github-copilot-token",
                cache_ttl=args.cache_ttl,
                no_cache=args.no_cache,
                method="GET",
                url=GITHUB_COPILOT_TOKEN_URL,
                headers={
                    "Authorization": f"Bearer {github_token}",
                    "Accept": "application/json",
                    "User-Agent": "ai-usage-lite",
                },
            )
            cached_any = cached_any or cached
        except Exception as e:
            copilot_token_error = str(e)
            diagnostics.append(f"Copilot token endpoint failed: {e}")

        copilot_token = copilot_token_response.get("token")
        token_claims = decode_jwt_payload(copilot_token)
        expires_at = copilot_token_response.get("expires_at") or token_claims.get("exp")
        refresh_in = copilot_token_response.get("refresh_in")
        refresh_at = (
            epoch_to_iso(time.time() + float(refresh_in))
            if isinstance(refresh_in, (int, float))
            else None
        )

        endpoints = copilot_token_response.get("endpoints") or {}
        sku = (
            copilot_token_response.get("sku")
            or copilot_token_response.get("copilot_plan")
            or copilot_token_response.get("plan")
            or token_claims.get("sku")
            or token_claims.get("plan")
        )

        details = auth_details | {
            "github_login": user.get("login"),
            "github_user_id_present": bool(user.get("id")),
            "github_user_type": user.get("type"),
            "github_plan_present": bool(user.get("plan")),
            "copilot_internal_token_endpoint_available": bool(copilot_token_response),
            "copilot_internal_token_error": copilot_token_error,
            "copilot_token_expires_at": (
                epoch_to_iso(expires_at)
                if isinstance(expires_at, (int, float))
                else expires_at
            ),
            "copilot_token_expires_in": duration_until(expires_at),
            "copilot_token_refresh_in_seconds": refresh_in,
            "copilot_token_refresh_at": refresh_at,
            "sku": sku,
            "annotations_enabled": copilot_token_response.get("annotations_enabled"),
            "chat_enabled": copilot_token_response.get("chat_enabled"),
            "code_quote_enabled": copilot_token_response.get("code_quote_enabled"),
            "public_suggestions": copilot_token_response.get("public_suggestions"),
            "endpoints_present": sorted_keys(endpoints),
            "copilot_token_response_keys": sorted_keys(copilot_token_response),
            "note": (
                "This reports Copilot auth/subscription-token metadata. "
                "GitHub does not provide the same stable real-time individual quota endpoint here as Claude/Codex."
            ),
        }

        if args.copilot_usage_url:
            try:
                custom_usage, cached = http_json(
                    cache_name="github-copilot-custom-usage",
                    cache_ttl=args.cache_ttl,
                    no_cache=args.no_cache,
                    method="GET",
                    url=args.copilot_usage_url,
                    headers={
                        "Authorization": f"Bearer {github_token}",
                        "Accept": "application/json",
                        "User-Agent": "ai-usage-lite",
                    },
                )
                cached_any = cached_any or cached
                details["custom_usage_endpoint_available"] = True
                details["custom_usage_response_keys"] = sorted_keys(custom_usage)

                if args.raw:
                    return ProviderReport(
                        provider="copilot",
                        status="partial",
                        plan=str(sku or "active"),
                        headline="Custom Copilot usage endpoint returned data.",
                        details=details,
                        diagnostics=diagnostics,
                        raw={"custom_usage": redact(custom_usage)},
                        cached=cached_any,
                    )
            except Exception as e:
                diagnostics.append(f"Custom Copilot usage endpoint failed: {e}")
                details["custom_usage_endpoint_available"] = False

        status = "partial" if copilot_token_response else "unavailable"
        headline = "Copilot auth found; quota usage endpoint not available."

        if copilot_token_response:
            headline = "Copilot token metadata available; real-time quota not exposed."

        return ProviderReport(
            provider="copilot",
            status=status,
            plan=str(sku or "active" if copilot_token_response else "unknown"),
            headline=headline,
            details=details,
            diagnostics=diagnostics,
            raw={"copilot_token_response": redact(copilot_token_response)} if args.raw else {},
            cached=cached_any,
        )

    except Exception as e:
        return ProviderReport(
            provider="copilot",
            status="error",
            headline="Copilot inspection failed.",
            diagnostics=[str(e)],
        )


def report_opencode(args: argparse.Namespace) -> ProviderReport:
    try:
        auth_file = Path(args.opencode_auth).expanduser()

        details: dict[str, Any] = {
            "auth_file": str(auth_file),
            "usage_endpoint_available": bool(args.opencode_usage_url),
            "note": (
                "OpenCode local credentials are detectable, but OpenCode Zen/Go "
                "does not expose a stable public usage endpoint like Claude/Codex."
            ),
        }

        diagnostics: list[str] = []

        if auth_file.exists():
            auth = read_json(auth_file)
            details["detected_provider_keys"] = sorted_keys(auth)

            provider_summaries = {}

            for provider_key, provider_value in auth.items():
                if isinstance(provider_value, dict):
                    provider_summaries[provider_key] = {
                        "keys_present": sorted_keys(provider_value),
                        "has_token_like_value": any(
                            key in provider_value
                            for key in (
                                "token",
                                "api_key",
                                "apikey",
                                "access",
                                "refresh",
                                "key",
                            )
                        ),
                    }

            details["provider_summaries"] = provider_summaries
        else:
            details["detected_provider_keys"] = []
            diagnostics.append(f"Missing file: {auth_file}")
            diagnostics.append("Run OpenCode `/connect` first.")

        raw: dict[str, Any] = {}
        cached = False

        if args.opencode_usage_url:
            api_key = os.getenv("OPENCODE_API_KEY") or os.getenv("OPENCODE_ZEN_API_KEY")

            if not api_key:
                diagnostics.append(
                    "Set OPENCODE_API_KEY or OPENCODE_ZEN_API_KEY to call --opencode-usage-url."
                )
            else:
                try:
                    data, cached = http_json(
                        cache_name="opencode-custom-usage",
                        cache_ttl=args.cache_ttl,
                        no_cache=args.no_cache,
                        method="GET",
                        url=args.opencode_usage_url,
                        headers={"Authorization": f"Bearer {api_key}"},
                    )
                    details["custom_usage_response_keys"] = sorted_keys(data)

                    if args.raw:
                        raw["custom_usage"] = redact(data)
                except Exception as e:
                    diagnostics.append(f"OpenCode custom usage endpoint failed: {e}")

        return ProviderReport(
            provider="opencode",
            status="partial",
            plan="unknown",
            headline="Credentials detectable; live quota endpoint unavailable.",
            details=details,
            diagnostics=diagnostics,
            raw=raw,
            cached=cached,
        )

    except Exception as e:
        return ProviderReport(
            provider="opencode",
            status="error",
            headline="OpenCode inspection failed.",
            diagnostics=[str(e)],
        )


def style_for_status(status: str) -> str:
    return {
        "ok": "green",
        "partial": "yellow",
        "unavailable": "dim",
        "error": "red bold",
    }.get(status, "white")


def style_for_risk(risk: str | None) -> str:
    return {
        "ok": "green",
        "watch": "yellow",
        "high": "orange1",
        "critical": "red",
        "exhausted": "red bold",
    }.get(risk or "", "white")


def style_for_burn(burn: str | None) -> str:
    return {
        "conserving": "green",
        "steady": "cyan",
        "overspending": "yellow",
    }.get(burn or "", "white")


def pct_bar(pct: float | None, *, width: int = 18, invert: bool = False) -> str:
    if pct is None:
        return "—"

    pct = max(0.0, min(100.0, pct))
    filled = int(round((pct / 100) * width))
    empty = width - filled

    if invert:
        style = "green" if pct >= 50 else "yellow" if pct >= 20 else "red bold"
    else:
        style = "green" if pct < 50 else "yellow" if pct < 85 else "red bold"

    return f"[{style}]{'█' * filled}[/]{'░' * empty} {pct:5.1f}%"


def fmt_burn(window: Window) -> str:
    if not window.burn_status:
        return "—"

    delta = window.burn_delta_points

    if delta is None:
        return window.burn_status

    sign = "+" if delta > 0 else ""
    style = style_for_burn(window.burn_status)

    return f"[{style}]{window.burn_status} {sign}{delta:.1f} pts[/]"


def fmt_value(value: Any) -> str:
    value = redact(value)

    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, indent=2)

    if value is None:
        return "—"

    if isinstance(value, bool):
        return "yes" if value else "no"

    return str(value)


def detail_items(report: ProviderReport, *, include_raw: bool) -> list[tuple[str, Any]]:
    items: list[tuple[str, Any]] = []

    for key, value in report.details.items():
        items.append((key, value))

    if report.diagnostics:
        items.append(("diagnostics", report.diagnostics))

    if include_raw and report.raw:
        for key, value in report.raw.items():
            items.append((f"raw.{key}", value))

    return items


def render_header(args: argparse.Namespace) -> Panel:
    now = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")

    text = Text()
    text.append("AI Usage Dashboard", style="bold")
    text.append(f"  •  generated {now}")
    text.append(f"  •  cache TTL {args.cache_ttl}s")

    if args.no_cache:
        text.append("  •  live", style="yellow")

    if args.raw:
        text.append("  •  sanitized raw payloads enabled", style="yellow")

    return Panel(text, box=box.SIMPLE, padding=(0, 1))


def render_legend() -> Panel:
    legend = Table.grid(padding=(0, 2))
    legend.add_column(style="bold")
    legend.add_column()

    legend.add_row(
        "Status",
        "ok = live quota; partial = useful metadata only; unavailable = not configured; error = unexpected failure",
    )
    legend.add_row(
        "Burn",
        "used% - elapsed%; conserving = slower than time, overspending = faster than time",
    )
    legend.add_row(
        "Risk",
        "ok/watch/high/critical/exhausted combines usage level and burn direction",
    )
    legend.add_row(
        "Raw",
        "secrets are redacted; use --raw for sanitized provider payloads",
    )

    return Panel(legend, title="Legend", box=box.SIMPLE, padding=(0, 1))


def render_overview(reports: list[ProviderReport]) -> Table:
    table = Table(title="Provider Overview", box=box.SIMPLE_HEAVY, expand=True)
    table.add_column("Provider", no_wrap=True)
    table.add_column("State", no_wrap=True)
    table.add_column("Plan", no_wrap=True)
    table.add_column("Headline")
    table.add_column("Evidence", overflow="fold")

    for report in reports:
        evidence = []

        if report.cached:
            evidence.append("cached")

        if report.details.get("auth_source"):
            evidence.append(str(report.details["auth_source"]))
        elif report.details.get("auth_file"):
            evidence.append(str(report.details["auth_file"]))

        if report.diagnostics and report.status in {"error", "unavailable"}:
            evidence.append(report.diagnostics[0])

        table.add_row(
            report.provider,
            f"[{style_for_status(report.status)}]{report.status}[/]",
            report.plan or "—",
            report.headline or "—",
            " | ".join(evidence) if evidence else "—",
        )

    return table


def render_windows(reports: list[ProviderReport]) -> Table:
    table = Table(title="Quota Windows", box=box.SIMPLE_HEAVY, expand=True)
    table.add_column("Provider", no_wrap=True)
    table.add_column("Window", no_wrap=True)
    table.add_column("Used", no_wrap=True)
    table.add_column("Available", no_wrap=True)
    table.add_column("Reset", no_wrap=True)
    table.add_column("Time elapsed", no_wrap=True)
    table.add_column("Burn vs time", no_wrap=True)
    table.add_column("Risk", no_wrap=True)

    had_windows = False

    for report in reports:
        for index, window in enumerate(report.windows):
            had_windows = True

            table.add_row(
                report.provider if index == 0 else "",
                window.name,
                pct_bar(window.used_percent),
                pct_bar(window.remaining_percent, invert=True),
                window.reset_in or "—",
                pct_bar(window.elapsed_percent, width=12),
                fmt_burn(window),
                f"[{style_for_risk(window.risk)}]{window.risk or '—'}[/]",
            )

    if not had_windows:
        table.add_row("—", "—", "—", "—", "—", "—", "—", "—")

    return table


def render_details(reports: list[ProviderReport], *, include_raw: bool) -> list[Panel]:
    panels: list[Panel] = []

    for report in reports:
        table = Table(box=box.SIMPLE, expand=True, show_header=True)
        table.add_column("Field", style="bold", no_wrap=True)
        table.add_column("Value", overflow="fold")

        items = detail_items(report, include_raw=include_raw)

        if not items:
            table.add_row("—", "No details")
        else:
            for key, value in items:
                table.add_row(key, fmt_value(value))

        panels.append(
            Panel(
                table,
                title=f"{report.provider} details",
                border_style=style_for_status(report.status),
                box=box.SIMPLE,
                padding=(0, 1),
            )
        )

    return panels


def render_dashboard(reports: list[ProviderReport], args: argparse.Namespace) -> None:
    console = Console()

    renderables: list[Any] = [
        render_header(args),
        render_legend(),
        render_overview(reports),
        render_windows(reports),
    ]

    if not args.compact:
        renderables.extend(render_details(reports, include_raw=args.raw))

    console.print(Group(*renderables))


def reports_to_json(reports: list[ProviderReport]) -> str:
    return json.dumps(
        [redact(asdict(report)) for report in reports],
        indent=2,
        ensure_ascii=False,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Claude, Codex/Pi, GitHub Copilot and OpenCode usage dashboard.",
    )

    parser.add_argument(
        "--provider",
        choices=["all", "claude", "codex", "copilot", "opencode"],
        default="all",
        help="Provider to report.",
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Print sanitized machine-readable JSON.",
    )

    parser.add_argument(
        "--raw",
        action="store_true",
        help="Include sanitized raw provider payloads.",
    )

    parser.add_argument(
        "--compact",
        action="store_true",
        help="Hide provider detail panels.",
    )

    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Force live API calls.",
    )

    parser.add_argument(
        "--cache-ttl",
        type=int,
        default=DEFAULT_CACHE_TTL_SECONDS,
        help="GET response cache TTL in seconds.",
    )

    parser.add_argument(
        "--codex-auth",
        default=None,
        help="Path to Codex/Pi auth.json. Defaults to ~/.codex/auth.json, then ~/.pi/agent/auth.json.",
    )

    parser.add_argument(
        "--copilot-auth",
        default=None,
        help="Path to GitHub Copilot/GitHub auth file.",
    )

    parser.add_argument(
        "--copilot-token",
        default=None,
        help="GitHub token for Copilot checks. Prefer GH_TOKEN/GITHUB_TOKEN or gh auth token instead.",
    )

    parser.add_argument(
        "--copilot-usage-url",
        default=os.getenv("COPILOT_USAGE_URL"),
        help="Optional custom/future GitHub Copilot usage endpoint.",
    )

    parser.add_argument(
        "--opencode-auth",
        default=str(OPENCODE_AUTH),
        help="Path to OpenCode auth.json.",
    )

    parser.add_argument(
        "--opencode-usage-url",
        default=os.getenv("OPENCODE_USAGE_URL"),
        help="Optional custom/future OpenCode Zen/Go usage endpoint.",
    )

    return parser.parse_args()


def main() -> int:
    args = parse_args()
    reports: list[ProviderReport] = []

    if args.provider in ("all", "claude"):
        reports.append(report_claude(args))

    if args.provider in ("all", "codex"):
        reports.append(report_codex(args))

    if args.provider in ("all", "copilot"):
        reports.append(report_copilot(args))

    if args.provider in ("all", "opencode"):
        reports.append(report_opencode(args))

    if args.json:
        print(reports_to_json(reports))
    else:
        render_dashboard(reports, args)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
