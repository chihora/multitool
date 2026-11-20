import ast
import subprocess
import tomllib
from pathlib import Path

GATE_COMMANDS = (
    ("uv", "run", "ruff", "check"),
    ("uv", "run", "ruff", "format", "--check"),
    ("uv", "run", "ty", "check"),
    ("uv", "run", "python", "-m", "unittest", "discover", "-s", "tests"),
)

_MAX_BRANCHES = 8
_MAX_FUNCTION_LINES = 50
_BRANCH_NODES = (
    ast.If,
    ast.For,
    ast.AsyncFor,
    ast.While,
    ast.Try,
    ast.TryStar,
    ast.With,
    ast.AsyncWith,
    ast.BoolOp,
    ast.IfExp,
    ast.Match,
)
_NESTED_SCOPES = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)


def run_health(path: str | Path) -> bool:
    project = Path(path)
    checks = _project_checks(project)
    for name, passed in checks:
        print(f"{name}: {'ok' if passed else 'missing'}")

    issues = _source_issues(project)
    for issue in issues:
        print(issue)

    gates_passed = _run_gates(project)
    return all(passed for _, passed in checks) and not issues and gates_passed


def _project_checks(project: Path) -> tuple[tuple[str, bool], ...]:
    return (
        ("pyproject.toml", (project / "pyproject.toml").is_file()),
        ("uv.lock", (project / "uv.lock").is_file()),
        ("tests/", (project / "tests").is_dir()),
        ("ruff configuration", _has_ruff_configuration(project)),
    )


def _has_ruff_configuration(project: Path) -> bool:
    if any((project / name).is_file() for name in ("ruff.toml", ".ruff.toml")):
        return True

    try:
        configuration = tomllib.loads((project / "pyproject.toml").read_text(encoding="utf-8"))
    except OSError, tomllib.TOMLDecodeError:
        return False

    tools = configuration.get("tool")
    return isinstance(tools, dict) and isinstance(tools.get("ruff"), dict)


def _source_issues(project: Path) -> list[str]:
    source = project / "src"
    if not source.is_dir():
        return []

    issues: list[str] = []
    for source_file in sorted(source.rglob("*.py")):
        issues.extend(_file_issues(project, source_file))
    return issues


def _file_issues(project: Path, source_file: Path) -> list[str]:
    relative_path = source_file.relative_to(project)
    try:
        tree = ast.parse(source_file.read_text(encoding="utf-8"), filename=str(relative_path))
    except (OSError, UnicodeError, SyntaxError) as error:
        return [f"{relative_path}: unable to inspect source: {error}"]

    issues: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            issues.extend(_function_issues(relative_path, node))
    return issues


def _function_issues(
    source_file: Path, function: ast.FunctionDef | ast.AsyncFunctionDef
) -> list[str]:
    issues: list[str] = []
    branch_count = _branch_count(function)
    line_count = (function.end_lineno or function.lineno) - function.lineno + 1
    location = f"{source_file}:{function.lineno}: {function.name}"

    if branch_count > _MAX_BRANCHES:
        issues.append(f"{location}: {branch_count} branches (maximum {_MAX_BRANCHES})")
    if line_count > _MAX_FUNCTION_LINES:
        issues.append(f"{location}: {line_count} lines (maximum {_MAX_FUNCTION_LINES})")
    return issues


def _branch_count(function: ast.FunctionDef | ast.AsyncFunctionDef) -> int:
    branches = 0
    pending: list[ast.AST] = list(function.body)
    while pending:
        node = pending.pop()
        if isinstance(node, _NESTED_SCOPES):
            continue
        branches += isinstance(node, _BRANCH_NODES)
        pending.extend(ast.iter_child_nodes(node))
    return branches


def _run_gates(project: Path) -> bool:
    passed = True
    for command in GATE_COMMANDS:
        try:
            returncode = subprocess.run(command, cwd=project).returncode
        except OSError:
            returncode = 1
        print(f"{' '.join(command)}: {returncode}")
        passed = returncode == 0 and passed
    return passed
