---
name: improve-python-scripts-in-skill
description: >
  Guide for writing Python scripts inside Claude skills using uv and PEP 723
  inline dependency metadata. Use this skill when creating or editing a skill
  that includes a Python script — whether starting from scratch or converting an
  existing script to the uv + PEP 723 pattern. Covers three patterns: (1)
  standalone scripts with inline deps (PEP 723), (2) server+client skills where
  the client auto-launches a local FastAPI server, and (3) migrating existing
  scripts from pip/requirements.txt/pyproject.toml to the self-contained uv
  pattern. Always consult this skill before writing any skill script.
---

# Python Skill Scripts — uv + PEP 723

Skill scripts handle work that is deterministic, repetitive, or too heavy to
inline. This guide shows how to write them so they are fully self-contained and
require no manual setup from the user.

**Prerequisite:** `uv` must be installed.
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Which pattern?

| Situation | Pattern |
|---|---|
| Script runs once, no persistent state | **Standalone (PEP 723)** |
| Script needs a long-running process (DB, ML model, API) | **Server + Client** |

---

## Pattern 1 — Standalone script (PEP 723)

Embed dependency declarations directly in the file. `uv run script.py` installs
them into an isolated ephemeral environment automatically.

```python
#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "httpx>=0.27",
#   "rich>=13.0",
# ]
# ///
"""One-line description."""
from __future__ import annotations
import argparse, sys
from pathlib import Path

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", default="out.csv")
    args = parser.parse_args()
    # ... do work

if __name__ == "__main__":
    main()
```

Claude invokes it as:
```bash
uv run ~/.claude/skills/my-skill/script.py --input foo.csv
```

**No `--with` needed** — deps are in the file. If you can't add the metadata
block (e.g., the script is auto-generated), fall back to:
```bash
uv run --with "httpx>=0.27,rich>=13.0" script.py
```
but prefer PEP 723 — it keeps deps co-located with the code.

Full copy-paste template: `templates/client-only.py`

---

## Pattern 2 — Server + Client (auto-launch)

Use when the skill needs a persistent process: a database connection pool,
a loaded ML model, a web server, etc.

```
skill-dir/
├── SKILL.md
├── client.py      ← Claude runs this; manages server lifecycle
└── server/
    └── main.py    ← FastAPI app; never run directly
```

**How it works:** the client checks `GET /health`, launches the server via
`uv run --with` if it's not alive, waits up to 15 s, then proxies requests
using stdlib `urllib` (so the client itself has zero deps).

Key constants at the top of `client.py`:
```python
_SKILL_DIR   = Path(__file__).resolve().parent   # needed for Popen cwd
_PORT        = int(os.environ.get("MY_SKILL_PORT", "8767"))
_BASE_URL    = f"http://127.0.0.1:{_PORT}"
_SERVER_DEPS = (
    "fastapi>=0.115,"
    "uvicorn[standard]>=0.32,"
    "python-dotenv>=1.0"
)
```

Use ports in 8700–8799 to avoid common conflicts. Document the default port
in SKILL.md.

The server must expose `GET /health → {"status": "ok"}`.

Full copy-paste templates: `templates/server-client/client.py` and
`templates/server-client/server/main.py`

---

## Migrating existing scripts to uv + PEP 723

### From `pip install` comments or a `requirements.txt`

1. Collect all deps and their minimum versions.
2. Add the PEP 723 block at the top of the script (see Pattern 1 above).
3. Delete the `requirements.txt` / install instructions from SKILL.md.
4. Test: `uv run script.py --help` should work with no pre-installed packages.

### From a `pyproject.toml` project (importable package)

If the script currently lives inside a package and uses relative imports:

1. Flatten it into a single `.py` file (or keep helpers alongside it).
2. Replace relative imports with inline helpers or stdlib equivalents.
3. Add the PEP 723 block with all transitive deps you actually use.
4. Test with a clean environment: `uv run script.py --help`.
   PEP 723 scripts are always isolated by uv — no `--isolated` flag needed.

### From `uv run --with` at the call site

Move the dep list from the SKILL.md into the script as a PEP 723 block. Remove
the `--with "..."` from the invocation in SKILL.md.

### From a `.env` file in the project directory

Move credentials to `~/.claude/<skill-name>.env` (see Config section below).
This keeps secrets out of the project directory and makes the skill portable
without the user having to copy files around.

---

## Config / credentials

Read from `~/.claude/<skill-name>.env`; never hardcode or bundle credentials:

```python
_ENV_FILE = Path.home() / ".claude" / "my-skill.env"

def _load_env() -> None:
    if not _ENV_FILE.exists():
        return
    for line in _ENV_FILE.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        os.environ.setdefault(k.strip(), v.strip())
```

Document required keys in SKILL.md under a **Setup** section.

---

## SKILL.md checklist

- [ ] `uv run` invocation shown exactly (no manual venv)
- [ ] **Setup** section lists env file path and required keys (if any)
- [ ] **Output** section says where files land
- [ ] Error recovery note if the server fails to start (server+client only)

## Script checklist

- [ ] PEP 723 block present (standalone) OR client uses stdlib-only (server+client)
- [ ] Server exposes `/health` (server+client)
- [ ] Port overridable via env var (server+client)
- [ ] `start_new_session=True` on `Popen` so server outlives client (server+client)
- [ ] Credentials read from `~/.claude/<skill>.env`, never hardcoded
