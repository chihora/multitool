## Run and test
This system is a Python command-line package, and it must never ship unless all four gates pass.
Run `uv sync` whenever the lockfile or local environment may be stale.
Use these four gates, in this order, as the definition of done; require exit code 0 from each.
Run `uv run ruff check`.
Run `uv run ruff format --check`.
Run `uv run ty check`.
Run `uv run python -m unittest discover -s tests`.
## Conventions that differ from defaults
Use `uv` exclusively for dependency and environment management; do not invoke `pip` directly.
Use only the standard library's `unittest`; do not add pytest or another test framework.
Keep the gate order fixed as lint, format check, type check, then unittest.
## Rules that must hold (enforced)
Never edit files under tests/ to make a gate pass. Enforced by: nothing yet.
Never weaken or bypass a gate to make work pass. Enforced by: review.
Do not report completion until every gate exit code is known. Enforced by: the definition of done.
## Where the truth lives
Consult `pyproject.toml` for project metadata, dependencies, entry points, and tool settings.
Consult `uv.lock` for exact resolved dependency versions.
Consult `src/multitool/` for runtime behavior.
Consult `tests/` for required external behavior.
Consult `AGENTS.md` for contributor workflow and non-code rules.
