"""
API key authentication + per-key rate limiting.

Keys are stored in API_KEYS env var as a comma-separated list, or in a
.api_keys file (one key per line, optionally as key:user_id pairs).

Rate limit: configurable requests per minute per key (default 20).
"""
import os
import time
from collections import defaultdict
from pathlib import Path

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

from agent import logger as audit

_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)
_RATE_LIMIT = int(os.getenv("RATE_LIMIT_RPM", "20"))  # requests per minute


def _load_keys() -> dict[str, str]:
    """Returns {api_key: user_id}."""
    keys: dict[str, str] = {}

    # From environment variable
    env_keys = os.getenv("API_KEYS", "")
    for entry in env_keys.split(","):
        entry = entry.strip()
        if ":" in entry:
            k, uid = entry.split(":", 1)
            keys[k.strip()] = uid.strip()
        elif entry:
            keys[entry] = entry[:8]

    # From .api_keys file
    key_file = Path(".api_keys")
    if key_file.exists():
        for line in key_file.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if ":" in line:
                k, uid = line.split(":", 1)
                keys[k.strip()] = uid.strip()
            else:
                keys[line] = line[:8]

    # Dev fallback — only active when no keys are configured
    if not keys:
        dev_key = "dev-key-local"
        keys[dev_key] = "dev"

    return keys


# In-memory sliding window: {api_key: [timestamp, ...]}
_windows: dict[str, list[float]] = defaultdict(list)


def _check_rate_limit(api_key: str):
    now = time.time()
    window = _windows[api_key]
    # Drop timestamps older than 60s
    _windows[api_key] = [t for t in window if now - t < 60]
    if len(_windows[api_key]) >= _RATE_LIMIT:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded: {_RATE_LIMIT} requests/minute",
        )
    _windows[api_key].append(now)


def require_api_key(api_key: str = Security(_HEADER)) -> str:
    """FastAPI dependency — validates key and enforces rate limit. Returns user_id."""
    keys = _load_keys()
    if not api_key or api_key not in keys:
        audit.log_auth(api_key or "anonymous", success=False)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key. Pass it as X-API-Key header.",
        )
    _check_rate_limit(api_key)
    user_id = keys[api_key]
    audit.log_auth(user_id, success=True)
    return user_id
