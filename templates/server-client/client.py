#!/usr/bin/env python3
"""my-skill client — delegates heavy work to a local FastAPI server.

Usage:
    python client.py --task TASK --name NAME [--limit N]

Server starts automatically on first use via uv (no manual setup needed).
Config: ~/.claude/my-skill.env
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants — edit these for each new skill
# ---------------------------------------------------------------------------

_SKILL_DIR = Path(__file__).resolve().parent
_ENV_FILE  = Path.home() / ".claude" / "my-skill.env"
_PORT      = int(os.environ.get("MY_SKILL_PORT", "8767"))
_BASE_URL  = f"http://127.0.0.1:{_PORT}"

# All server-side deps in one comma-joined string passed to `uv run --with`
_SERVER_DEPS = (
    "fastapi>=0.115,"
    "uvicorn[standard]>=0.32,"
    "python-dotenv>=1.0"
    # add more here, e.g. "sqlalchemy>=2.0,pymysql>=1.1"
)


# ---------------------------------------------------------------------------
# Env loading
# ---------------------------------------------------------------------------

def _load_env() -> None:
    if not _ENV_FILE.exists():
        return
    for line in _ENV_FILE.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        os.environ.setdefault(k.strip(), v.strip())


# ---------------------------------------------------------------------------
# Server management
# ---------------------------------------------------------------------------

def _ensure_server() -> None:
    """Start the server if not already running, then wait for it to be ready."""
    def alive() -> bool:
        try:
            urllib.request.urlopen(f"{_BASE_URL}/health", timeout=2)
            return True
        except Exception:
            return False

    if alive():
        return  # already running

    subprocess.Popen(
        ["uv", "run", "--with", _SERVER_DEPS,
         "uvicorn", "main:app", "--host", "127.0.0.1", "--port", str(_PORT)],
        cwd=str(_SKILL_DIR / "server"),
        env={**os.environ, "PYTHONPATH": str(_SKILL_DIR / "server")},
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,  # server outlives this client process
    )

    print(f"Starting server on port {_PORT}...", file=sys.stderr)
    for _ in range(30):  # up to 15 s
        time.sleep(0.5)
        if alive():
            print("Server ready.", file=sys.stderr)
            return

    print(
        f"ERROR: server did not start on port {_PORT}.\n"
        f"Check that uv is installed and {_ENV_FILE} is configured.",
        file=sys.stderr,
    )
    sys.exit(1)


# ---------------------------------------------------------------------------
# HTTP helpers (stdlib only — client has zero extra deps)
# ---------------------------------------------------------------------------

def _post(path: str, payload: dict) -> dict:
    body = json.dumps(payload).encode()
    req = urllib.request.Request(
        f"{_BASE_URL}{path}",
        data=body,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode(errors="replace")
        print(f"ERROR {exc.code}: {detail}", file=sys.stderr)
        sys.exit(1)


def _get(path: str) -> dict:
    try:
        with urllib.request.urlopen(f"{_BASE_URL}{path}", timeout=10) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        print(f"ERROR {exc.code}: {exc.read().decode()}", file=sys.stderr)
        sys.exit(1)


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_info(args: argparse.Namespace) -> None:
    result = _get("/info")
    print(json.dumps(result, indent=2))


def cmd_run(args: argparse.Namespace) -> None:
    result = _post("/run", {"input": args.input, "limit": args.limit})
    # write result to a file, print summary, etc.
    print(json.dumps(result, indent=2))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    _load_env()

    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("info", help="Show server info")

    p_run = sub.add_parser("run", help="Run a task")
    p_run.add_argument("--input", required=True)
    p_run.add_argument("--limit", type=int, default=100)

    args = parser.parse_args()
    _ensure_server()

    if args.command == "info":
        cmd_info(args)
    elif args.command == "run":
        cmd_run(args)


if __name__ == "__main__":
    main()
