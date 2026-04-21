#!/usr/bin/env python3
"""my-skill client — delegates work to a local FastAPI server (auto-started)."""
from __future__ import annotations
import argparse, json, os, subprocess, sys, time, urllib.error, urllib.request
from pathlib import Path

_SKILL_DIR   = Path(__file__).resolve().parent
_PORT        = int(os.environ.get("MY_SKILL_PORT", "8767"))
_BASE_URL    = f"http://127.0.0.1:{_PORT}"
_SERVER_DEPS = "fastapi>=0.115,uvicorn[standard]>=0.32"


def _alive() -> bool:
    try:
        urllib.request.urlopen(f"{_BASE_URL}/health", timeout=2)
        return True
    except Exception:
        return False


def _ensure_server() -> None:
    if _alive():
        return
    subprocess.Popen(
        ["uv", "run", "--with", _SERVER_DEPS,
         "uvicorn", "main:app", "--host", "127.0.0.1", "--port", str(_PORT)],
        cwd=str(_SKILL_DIR / "server"),
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    print(f"Starting server on port {_PORT}...", file=sys.stderr)
    for _ in range(30):
        time.sleep(0.5)
        if _alive():
            return
    print("ERROR: server failed to start", file=sys.stderr)
    sys.exit(1)


def _post(path: str, payload: dict) -> dict:
    body = json.dumps(payload).encode()
    req = urllib.request.Request(
        f"{_BASE_URL}{path}", data=body,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        print(f"ERROR {e.code}: {e.read().decode()}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    args = parser.parse_args()
    _ensure_server()
    result = _post("/run", {"input": args.input})
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
