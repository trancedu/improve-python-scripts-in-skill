"""my-skill server — started automatically by client.py via uv.

Never run this directly. The client launches it with:
    uv run --with <_SERVER_DEPS> uvicorn main:app --host 127.0.0.1 --port <PORT>
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Load env from ~/.claude/my-skill.env on startup
load_dotenv(Path.home() / ".claude" / "my-skill.env")

app = FastAPI(title="my-skill")


# ---------------------------------------------------------------------------
# Health — required by client._ensure_server()
# ---------------------------------------------------------------------------

@app.get("/health")
def health():
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Info
# ---------------------------------------------------------------------------

@app.get("/info")
def info():
    return {"version": "0.1.0"}


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

class RunRequest(BaseModel):
    input: str
    limit: int = 100


@app.post("/run")
def run(req: RunRequest):
    # Replace with actual logic
    return {"result": f"processed {req.input!r}", "limit": req.limit}
