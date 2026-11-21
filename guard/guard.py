import json
import re
import shlex
import sys
from datetime import UTC, datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RECEIPT_PATH = PROJECT_ROOT / ".receipts" / "tool-calls.jsonl"

BLOCK_REASON = "blocked: modifications under tests/ are not allowed"
_PATCH_TOOLS = frozenset(("apply_patch", "patch"))
_FILE_TOOLS = frozenset(("edit", "write", *_PATCH_TOOLS))
_SHELL_TOOLS = frozenset(("bash", "shell"))
_PATH_KEYS = ("path", "filePath", "file_path", "target", "target_path")
_PATCH_PATH = re.compile(
    r"^\*\*\* (?:Add File|Update File|Delete File|Move to): (.+)$", re.MULTILINE
)
_COMMAND_BOUNDARY = frozenset(("|", "&", ";"))
_ALL_PATH_WRITERS = frozenset(
    (
        "add-content",
        "chmod",
        "del",
        "erase",
        "mkdir",
        "new-item",
        "out-file",
        "remove-item",
        "rm",
        "rmdir",
        "set-content",
        "touch",
        "truncate",
        "unlink",
    )
)
_DESTINATION_WRITERS = frozenset(("copy", "copy-item", "cp", "install", "move", "move-item", "mv"))


def _read_request() -> dict[str, object] | None:
    try:
        value: object = json.load(sys.stdin)
    except json.JSONDecodeError, OSError:
        return None
    if not isinstance(value, dict):
        return None
    return {str(key): item for key, item in value.items()}


def _arguments(request: dict[str, object]) -> dict[str, object]:
    value = request.get("args")
    if not isinstance(value, dict):
        return {}
    return {str(key): item for key, item in value.items()}


def _tool_paths(tool: str, arguments: dict[str, object]) -> list[str]:
    paths: list[str] = []
    for key in _PATH_KEYS:
        value = arguments.get(key)
        if isinstance(value, str):
            paths.append(value)
    if tool in _PATCH_TOOLS:
        for patch in arguments.values():
            if isinstance(patch, str):
                paths.extend(_PATCH_PATH.findall(patch))
    return list(dict.fromkeys(paths))


def _under_tests(value: str) -> bool:
    cleaned = value.strip().strip("\"'").replace("\\", "/")
    if not cleaned:
        return False
    candidate = Path(cleaned)
    if not candidate.is_absolute():
        candidate = PROJECT_ROOT / candidate
    try:
        candidate.resolve(strict=False).relative_to((PROJECT_ROOT / "tests").resolve())
    except ValueError:
        return False
    return True


def _shell_tokens(command: str) -> list[str]:
    lexer = shlex.shlex(command, posix=False, punctuation_chars="|&;<>")
    lexer.commenters = ""
    lexer.whitespace_split = True
    try:
        return list(lexer)
    except ValueError:
        return command.split()


def _command_segments(tokens: list[str]) -> list[list[str]]:
    segments: list[list[str]] = [[]]
    for token in tokens:
        if token and set(token) <= _COMMAND_BOUNDARY:
            segments.append([])
        else:
            segments[-1].append(token)
    return [segment for segment in segments if segment]


def _command_name(token: str) -> str:
    name = token.strip("\"'").replace("\\", "/").rsplit("/", 1)[-1].lower()
    return name.removesuffix(".exe")


def _redirects_to_tests(tokens: list[str]) -> bool:
    for index, token in enumerate(tokens[:-1]):
        if ">" in token and set(token) <= frozenset((">", "&")):
            if _under_tests(tokens[index + 1]):
                return True
    return False


def _in_place_sed_writes_tests(segment: list[str]) -> bool:
    names = [_command_name(token) for token in segment]
    if "sed" not in names:
        return False
    in_place = any(token == "--in-place" or token.startswith("-i") for token in segment)
    return in_place and any(_under_tests(token) for token in segment)


def _utility_writes_tests(segment: list[str]) -> bool:
    names = [_command_name(token) for token in segment]
    if "tee" in names:
        tee_index = names.index("tee")
        return any(_under_tests(token) for token in segment[tee_index + 1 :])
    if any(name in _ALL_PATH_WRITERS for name in names):
        return any(_under_tests(token) for token in segment)
    for index, name in enumerate(names):
        if name in _DESTINATION_WRITERS:
            operands = [token for token in segment[index + 1 :] if not token.startswith("-")]
            return bool(operands) and _under_tests(operands[-1])
    return False


def _shell_writes_tests(command: str) -> bool:
    tokens = _shell_tokens(command)
    if _redirects_to_tests(tokens):
        return True
    return any(
        _in_place_sed_writes_tests(segment) or _utility_writes_tests(segment)
        for segment in _command_segments(tokens)
    )


def _decision(tool: str, arguments: dict[str, object]) -> tuple[str | None, str | None, str]:
    command_value = arguments.get("command")
    command = command_value if isinstance(command_value, str) else None
    paths = _tool_paths(tool, arguments)
    path = paths[0] if paths else None

    if tool in _FILE_TOOLS:
        blocked_path = next((candidate for candidate in paths if _under_tests(candidate)), None)
        return blocked_path or path, None, "block" if blocked_path else "allow"
    if tool in _SHELL_TOOLS:
        return None, command, "block" if command and _shell_writes_tests(command) else "allow"
    return path, command, "allow"


def _append_receipt(tool: str, path: str | None, command: str | None, decision: str) -> None:
    receipt: dict[str, object] = {
        "time": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "tool": tool,
        "decision": decision,
    }
    receipt["command" if command is not None else "path"] = command if command is not None else path
    RECEIPT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with RECEIPT_PATH.open("a", encoding="utf-8") as receipts:
        receipts.write(json.dumps(receipt, separators=(",", ":")) + "\n")


def main() -> int:
    request = _read_request()
    if request is None:
        _append_receipt("", None, None, "block")
        print("blocked: expected one JSON object with tool and args")
        return 2

    tool_value = request.get("tool")
    tool = tool_value.lower() if isinstance(tool_value, str) else ""
    path, command, decision = _decision(tool, _arguments(request))
    _append_receipt(tool, path, command, decision)
    if decision == "block":
        print(BLOCK_REASON)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
