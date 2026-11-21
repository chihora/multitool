import json
import shutil
import subprocess
import sys
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import cast

GUARD_SOURCE = Path(__file__).resolve().parents[1] / "guard" / "guard.py"
BLOCK_REASON = "blocked: modifications under tests/ are not allowed\n"


class GuardTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = TemporaryDirectory()
        self.project = Path(self.temporary_directory.name)
        self.guard = self.project / "guard" / "guard.py"
        self.guard.parent.mkdir()
        shutil.copyfile(GUARD_SOURCE, self.guard)

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_file_tools_block_paths_under_tests(self) -> None:
        cases = (
            ("edit", {"path": "tests/test_edit.py"}, "tests/test_edit.py"),
            ("write", {"filePath": "tests\\nested\\test_write.py"}, "tests\\nested\\test_write.py"),
            (
                "patch",
                {
                    "patchText": "*** Begin Patch\n"
                    "*** Update File: src/example.py\n"
                    "*** Update File: tests/test_patch.py\n"
                    "*** End Patch"
                },
                "tests/test_patch.py",
            ),
        )

        for tool, arguments, blocked_path in cases:
            with self.subTest(tool=tool):
                result = self.run_guard(tool, arguments)

                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, BLOCK_REASON)
                self.assertEqual(result.stderr, "")
                receipt = self.receipts()[-1]
                self.assertEqual(receipt["tool"], tool)
                self.assertEqual(receipt["path"], blocked_path)
                self.assertEqual(receipt["decision"], "block")

    def test_shell_blocks_common_writes_into_tests(self) -> None:
        commands = (
            "sed -i 's/old/new/' tests/test_example.py",
            "printf changed > tests/test_example.py",
            "printf changed | tee tests/test_example.py",
        )

        for command in commands:
            with self.subTest(command=command):
                result = self.run_guard("shell", {"command": command})

                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, BLOCK_REASON)
                receipt = self.receipts()[-1]
                self.assertEqual(receipt["command"], command)
                self.assertEqual(receipt["decision"], "block")

    def test_non_test_edits_and_read_only_test_commands_are_allowed(self) -> None:
        cases = (
            ("edit", {"path": "src/multitool/example.py"}),
            ("write", {"filePath": "docs/example.md"}),
            ("patch", {"patchText": "*** Update File: src/multitool/example.py\n"}),
            ("shell", {"command": "python -m unittest discover -s tests"}),
            ("shell", {"command": "cp tests/test_guard.py scratch/test_guard.py"}),
        )

        for tool, arguments in cases:
            with self.subTest(tool=tool, arguments=arguments):
                result = self.run_guard(tool, arguments)

                self.assertEqual(result.returncode, 0)
                self.assertEqual(result.stdout, "")
                self.assertEqual(result.stderr, "")
                self.assertEqual(self.receipts()[-1]["decision"], "allow")

    def test_every_call_appends_a_json_receipt_with_utc_time(self) -> None:
        self.run_guard("edit", {"path": "src/example.py"})
        self.run_guard("edit", {"path": "tests/test_example.py"})

        receipts = self.receipts()
        self.assertEqual(len(receipts), 2)
        for receipt in receipts:
            timestamp = receipt["time"]
            self.assertIsInstance(timestamp, str)
            parsed = datetime.fromisoformat(cast(str, timestamp).replace("Z", "+00:00"))
            self.assertEqual(parsed.utcoffset(), timedelta(0))

    def run_guard(self, tool: str, arguments: dict[str, str]) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(self.guard)],
            input=json.dumps({"tool": tool, "args": arguments}),
            text=True,
            capture_output=True,
            cwd=self.project,
            check=False,
        )

    def receipts(self) -> list[dict[str, object]]:
        receipt_file = self.project / ".receipts" / "tool-calls.jsonl"
        return [
            cast(dict[str, object], json.loads(line))
            for line in receipt_file.read_text(encoding="utf-8").splitlines()
        ]


if __name__ == "__main__":
    unittest.main()
