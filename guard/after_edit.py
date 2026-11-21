import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RECEIPT_PATH = PROJECT_ROOT / ".receipts" / "after-edit.jsonl"


def main() -> int:
    path = sys.argv[1]
    result = subprocess.run(
        ["uv", "run", "ruff", "format", path],
        cwd=PROJECT_ROOT,
        check=False,
    )
    receipt = {
        "time": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "path": path,
        "exit_code": result.returncode,
    }
    RECEIPT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with RECEIPT_PATH.open("a", encoding="utf-8") as receipts:
        receipts.write(json.dumps(receipt, separators=(",", ":")) + "\n")
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
