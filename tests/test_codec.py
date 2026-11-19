import io
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import patch

from multitool import main
from multitool.codec import decode, encode


class CodecTests(unittest.TestCase):
    def test_round_trip_for_every_scheme(self) -> None:
        for scheme in ("rot13", "base64", "hex"):
            with self.subTest(scheme=scheme):
                self.assertEqual(decode(scheme, encode(scheme, "café")), "café")

    def test_codec_command(self) -> None:
        output = io.StringIO()

        with patch.object(sys, "argv", ["mt", "codec", "base64", "encode", "café"]):
            with redirect_stdout(output):
                main()

        self.assertEqual(output.getvalue(), "Y2Fmw6k=\n")

    def test_unknown_scheme_exits_with_code_2(self) -> None:
        self.assert_cli_error("unknown", "encode", "text")

    def test_unknown_direction_exits_with_code_2(self) -> None:
        self.assert_cli_error("rot13", "unknown", "text")

    def assert_cli_error(self, scheme: str, direction: str, text: str) -> None:
        with patch.object(sys, "argv", ["mt", "codec", scheme, direction, text]):
            with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as raised:
                main()

        self.assertEqual(raised.exception.code, 2)
