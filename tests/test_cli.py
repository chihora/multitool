import io
import sys
import unittest
from contextlib import redirect_stdout
from importlib.metadata import entry_points, version
from unittest.mock import patch


class CliTests(unittest.TestCase):
    def test_version(self) -> None:
        mt = next(
            entry_point
            for entry_point in entry_points(group="console_scripts")
            if entry_point.name == "mt"
        )
        output = io.StringIO()

        with patch.object(sys, "argv", ["mt", "--version"]), redirect_stdout(output):
            with self.assertRaises(SystemExit) as raised:
                mt.load()()

        self.assertEqual(raised.exception.code, 0)
        self.assertEqual(output.getvalue(), f"mt {version('multitool')}\n")
