"""
Structured audit logger — writes every agent action to a JSONL file.
Each line is a self-contained JSON record: timestamp, event type, payload.
"""
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path


_LOG_FILE = "agent_audit.jsonl"
_FMT = "%(asctime)s [%(levelname)s] %(message)s"


def _setup_console_logger() -> logging.Logger:
    logger = logging.getLogger("agent")
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(_FMT))
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger


_console = _setup_console_logger()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _append(record: dict):
    with open(_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def log_request(user_id: str, message: str, mode: str = "chat"):
    record = {"ts": _now(), "event": "request", "user_id": user_id, "mode": mode, "message": message[:500]}
    _append(record)
    _console.info(f"[{user_id}] {mode}: {message[:80]}")


def log_response(user_id: str, response: str, tool_calls: int = 0, duration_ms: int = 0):
    record = {"ts": _now(), "event": "response", "user_id": user_id, "tool_calls": tool_calls,
              "duration_ms": duration_ms, "response_len": len(response)}
    _append(record)
    _console.info(f"[{user_id}] response ({len(response)} chars, {tool_calls} tools, {duration_ms}ms)")


def log_tool_call(user_id: str, tool_name: str, inputs: dict):
    record = {"ts": _now(), "event": "tool_call", "user_id": user_id, "tool": tool_name, "inputs": inputs}
    _append(record)
    _console.info(f"[{user_id}] tool: {tool_name}")


def log_error(user_id: str, error: str):
    record = {"ts": _now(), "event": "error", "user_id": user_id, "error": error}
    _append(record)
    _console.error(f"[{user_id}] ERROR: {error}")


def log_auth(user_id: str, success: bool, ip: str = ""):
    record = {"ts": _now(), "event": "auth", "user_id": user_id, "success": success, "ip": ip}
    _append(record)
    level = _console.info if success else _console.warning
    level(f"auth {'OK' if success else 'FAIL'} user={user_id} ip={ip}")
