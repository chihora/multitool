import io
import subprocess
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory
from textwrap import dedent
from unittest.mock import Mock, patch

from multitool import main

GATE_COMMANDS = (
    ("uv", "run", "ruff", "check"),
    ("uv", "run", "ruff", "format", "--check"),
    ("uv", "run", "ty", "check"),
    ("uv", "run", "python", "-m", "unittest", "discover", "-s", "tests"),
)

MIXED_BRANCH_TYPES = dedent(
    """\
    def mixed_branch_types(values, condition):
        if condition:
            pass
        for value in values:
            pass
        while condition:
            break
        try:
            pass
        except RuntimeError:
            pass
        with open("unused"):
            pass
        first = condition and values
        second = condition or values
        third = condition and values
        return condition or values
    """
)


def function_with_branches(name: str, count: int, *, asynchronous: bool = False) -> str:
    prefix = "async " if asynchronous else ""
    lines = [f"{prefix}def {name}(value):"]
    for number in range(count):
        lines.extend((f"    if value == {number}:", "        pass"))
    return "\n".join(lines)


def function_with_lines(name: str, count: int) -> str:
    return "\n".join([f"def {name}():", *["    value = 0"] * (count - 1)])


class HealthTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = TemporaryDirectory()
        self.project = Path(self.temporary_directory.name)
        self.source = self.project / "src" / "fixture" / "checks.py"
        self.write_healthy_project()

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_healthy_project_reports_checks_and_gate_exit_codes(self) -> None:
        exit_code, output, runner = self.run_health((0, 0, 0, 0))

        self.assertEqual(exit_code, 0)
        for check in ("pyproject.toml", "uv.lock", "tests/", "ruff configuration"):
            self.assertIn(f"{check}: ok", output.lower())
        self.assert_gate_report(output, (0, 0, 0, 0))
        self.assert_gate_commands(runner)

    def test_all_missing_project_checks_are_reported_before_failure(self) -> None:
        (self.project / "pyproject.toml").unlink()
        (self.project / "uv.lock").unlink()
        (self.project / "tests").rmdir()

        exit_code, output, runner = self.run_health((0, 0, 0, 0))

        self.assertEqual(exit_code, 1)
        for check in ("pyproject.toml", "uv.lock", "tests/", "ruff configuration"):
            self.assertIn(f"{check}: missing", output.lower())
        self.assert_gate_commands(runner)

    def test_pyproject_without_ruff_table_fails_the_ruff_check(self) -> None:
        (self.project / "pyproject.toml").write_text(
            '[project]\nname = "fixture"\nversion = "0.0.0"\n',
            encoding="utf-8",
        )

        exit_code, output, _ = self.run_health((0, 0, 0, 0))

        self.assertEqual(exit_code, 1)
        self.assertIn("pyproject.toml: ok", output.lower())
        self.assertIn("ruff configuration: missing", output.lower())

    def test_standalone_ruff_configuration_files_are_recognized(self) -> None:
        (self.project / "pyproject.toml").write_text(
            '[project]\nname = "fixture"\nversion = "0.0.0"\n',
            encoding="utf-8",
        )

        for filename in ("ruff.toml", ".ruff.toml"):
            with self.subTest(filename=filename):
                config = self.project / filename
                config.write_text("line-length = 100\n", encoding="utf-8")
                try:
                    exit_code, output, _ = self.run_health((0, 0, 0, 0))

                    self.assertEqual(exit_code, 0)
                    self.assertIn("ruff configuration: ok", output.lower())
                finally:
                    config.unlink()

    def test_failed_gate_reports_every_exit_code_and_exits_one(self) -> None:
        returncodes = (0, 1, 2, 3)

        exit_code, output, runner = self.run_health(returncodes)

        self.assertEqual(exit_code, 1)
        self.assert_gate_report(output, returncodes)
        self.assert_gate_commands(runner)

    def test_ast_limits_include_every_branch_type_and_boundary(self) -> None:
        self.source.write_text(
            "\n\n".join(
                (
                    function_with_branches("at_branch_limit", 8),
                    function_with_branches("over_branch_limit", 9),
                    function_with_branches("async_over_branch_limit", 9, asynchronous=True),
                    MIXED_BRANCH_TYPES,
                    function_with_lines("at_line_limit", 50),
                    function_with_lines("over_line_limit", 51),
                )
            )
            + "\n",
            encoding="utf-8",
        )

        exit_code, output, _ = self.run_health((0, 0, 0, 0))

        self.assertEqual(exit_code, 1)
        for function in (
            "over_branch_limit",
            "async_over_branch_limit",
            "mixed_branch_types",
            "over_line_limit",
        ):
            self.assertIn(function, output)
        for function in ("at_branch_limit", "at_line_limit"):
            self.assertNotIn(function, output)

    def write_healthy_project(self) -> None:
        (self.project / "pyproject.toml").write_text(
            dedent(
                """\
                [project]
                name = "fixture"
                version = "0.0.0"

                [tool.ruff]
                line-length = 100
                """
            ),
            encoding="utf-8",
        )
        (self.project / "uv.lock").touch()
        (self.project / "tests").mkdir()
        self.source.parent.mkdir(parents=True)
        self.source.write_text("def healthy():\n    return True\n", encoding="utf-8")

    def run_health(self, returncodes: tuple[int, int, int, int]) -> tuple[int, str, Mock]:
        results = [
            subprocess.CompletedProcess(command, returncode)
            for command, returncode in zip(GATE_COMMANDS, returncodes, strict=True)
        ]
        output = io.StringIO()
        errors = io.StringIO()
        exit_code = 0

        with (
            patch("subprocess.run", side_effect=results) as runner,
            patch.object(sys, "argv", ["mt", "health", str(self.project)]),
            redirect_stdout(output),
            redirect_stderr(errors),
        ):
            try:
                main()
            except SystemExit as error:
                if isinstance(error.code, int):
                    exit_code = error.code
                elif error.code is not None:
                    exit_code = 1

        return exit_code, output.getvalue(), runner

    def assert_gate_report(self, output: str, returncodes: tuple[int, int, int, int]) -> None:
        for command, returncode in zip(GATE_COMMANDS, returncodes, strict=True):
            self.assertIn(f"{' '.join(command)}: {returncode}", output)

    def assert_gate_commands(self, runner: Mock) -> None:
        self.assertEqual(
            [tuple(call.args[0]) for call in runner.call_args_list],
            list(GATE_COMMANDS),
        )
        for call in runner.call_args_list:
            self.assertEqual(Path(call.kwargs["cwd"]), self.project)


if __name__ == "__main__":
    unittest.main()
