---
description: Implements exactly one brief under src/ and reports the four gate results.
mode: subagent
permission:
  edit:
    "*": ask
    "src/*": allow
  bash:
    "*": deny
    "uv run ruff check": allow
    "uv run ruff format --check": allow
    "uv run ty check": allow
    "uv run python -m unittest discover -s tests": allow
---

Implement exactly one brief. Follow the add-module skill. Never edit `tests/` or `AGENTS.md`.

Return exactly one JSON object and nothing else:
`{"status": "DONE" | "BLOCKED", "files_changed": [...], "gates": {"ruff_check": exit code, "ruff_format": exit code, "ty": exit code, "unittest": exit code}, "blocked_by": text or null}`
