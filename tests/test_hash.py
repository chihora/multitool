import io
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from multitool import main
from multitool.hash import hash_file, hash_text


class HashTests(unittest.TestCase):
    def test_hash_text_for_each_algorithm(self) -> None:
        expected = {
            "sha256": "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824",
            "md5": "5d41402abc4b2a76b9719d911017c592",
        }

        for algorithm, digest in expected.items():
            with self.subTest(algorithm=algorithm):
                self.assertEqual(hash_text(algorithm, "hello"), digest)

    def test_hash_file(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory, "input.bin")
            path.write_bytes(b"hello")

            self.assertEqual(hash_file("md5", path), "5d41402abc4b2a76b9719d911017c592")

    def test_hash_string_command(self) -> None:
        output = self.run_command("sha256", "hello")

        self.assertEqual(
            output,
            "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824\n",
        )

    def test_hash_file_command(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory, "input.bin")
            path.write_bytes(b"hello")

            output = self.run_command("md5", "--file", str(path))

        self.assertEqual(output, "5d41402abc4b2a76b9719d911017c592\n")

    def test_verify_matching_digest_succeeds(self) -> None:
        digest = "5d41402abc4b2a76b9719d911017c592"

        output = self.run_command("md5", "hello", "--verify", digest)

        self.assertEqual(output, f"{digest}\n")

    def test_verify_mismatch_exits_with_code_1(self) -> None:
        with patch.object(
            sys,
            "argv",
            ["mt", "hash", "md5", "hello", "--verify", "0" * 32],
        ):
            with redirect_stdout(io.StringIO()), self.assertRaises(SystemExit) as raised:
                main()

        self.assertEqual(raised.exception.code, 1)

    def run_command(self, *arguments: str) -> str:
        output = io.StringIO()

        with patch.object(sys, "argv", ["mt", "hash", *arguments]):
            with redirect_stdout(output):
                main()

        return output.getvalue()
