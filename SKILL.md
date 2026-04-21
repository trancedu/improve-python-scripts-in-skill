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

# Python Skill Scripts — uv

**Prerequisite:** `uv` must be installed (`curl -LsSf https://astral.sh/uv/install.sh | sh`).

## Which pattern?

| Situation | Pattern |
|---|---|
| Ad-hoc one-liner Claude runs inline | `uv run --with "pkg" -c "..."` |
| Reusable script file in the skill | **PEP 723** — deps embedded in file |
| Needs a persistent process (DB, model, API) | **Server + Client** |

---

## Ad-hoc (no script file)

For throwaway code Claude runs directly — no file needed:

```bash
uv run --with "httpx" -c "import httpx; print(httpx.get('https://example.com').status_code)"
```

---

## Standalone script (PEP 723)

Embed deps in the file. `uv run script.py` installs them automatically into an isolated environment.

```python
#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx>=0.27", "rich>=13.0"]
# ///
import argparse, httpx

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    args = parser.parse_args()
    print(httpx.get(args.url).status_code)

if __name__ == "__main__":
    main()
```

Claude invokes it as:
```bash
uv run ~/.claude/skills/my-skill/script.py --url https://example.com
```

Full template: `templates/standalone.py`

---

## Server + Client (auto-launch)

Use when the skill needs a persistent process. The client is zero-dep stdlib only; it checks `/health`, launches the server via `uv run --with` if needed, then proxies requests.

```
skill-dir/
├── SKILL.md
├── client.py      ← Claude runs this
└── server/
    └── main.py    ← FastAPI app
```

Full templates: `templates/server-client/client.py` and `templates/server-client/server/main.py`

Key rules:
- Server must expose `GET /health → {"status": "ok"}`
- Use ports 8700–8799; make port overridable via env var
- `start_new_session=True` on `Popen` so server outlives client
