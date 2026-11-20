import argparse
import hmac
from importlib.metadata import version
from pathlib import Path

from multitool.codec import decode, encode
from multitool.hash import hash_file, hash_text
from multitool.units import convert


def main() -> None:
    parser = argparse.ArgumentParser(prog="mt")
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {version('multitool')}",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)
    echo_parser = subparsers.add_parser("echo", help="print text")
    echo_parser.add_argument("text", nargs="+", help="text to print")

    codec_parser = subparsers.add_parser("codec", help="encode or decode text")
    codec_parser.add_argument("scheme", choices=("rot13", "base64", "hex"))
    codec_parser.add_argument("direction", choices=("encode", "decode"))
    codec_parser.add_argument("text")

    units_parser = subparsers.add_parser("units", help="convert a value between units")
    units_parser.add_argument("value", type=float)
    units_parser.add_argument("from_unit", metavar="from")
    units_parser.add_argument("to_unit", metavar="to")

    hash_parser = subparsers.add_parser("hash", help="hash text or a file")
    hash_parser.add_argument("algorithm", choices=("sha256", "md5"))
    hash_input = hash_parser.add_mutually_exclusive_group(required=True)
    hash_input.add_argument("text", nargs="?", help="text to hash")
    hash_input.add_argument("--file", type=Path, help="file to hash")
    hash_parser.add_argument("--verify", metavar="DIGEST", help="exit 1 if the digest differs")

    args = parser.parse_args()
    if args.command == "echo":
        print(" ".join(args.text))
    elif args.command == "codec":
        operation = encode if args.direction == "encode" else decode
        print(operation(args.scheme, args.text))
    elif args.command == "units":
        try:
            result = convert(args.value, args.from_unit, args.to_unit)
            print(f"{result:.1f}" if args.from_unit in ("C", "F", "K") else result)
        except ValueError as error:
            units_parser.error(str(error))
    elif args.command == "hash":
        try:
            digest = (
                hash_file(args.algorithm, args.file)
                if args.file is not None
                else hash_text(args.algorithm, args.text)
            )
        except OSError as error:
            hash_parser.error(str(error))

        print(digest)
        if args.verify is not None and not hmac.compare_digest(digest, args.verify.lower()):
            raise SystemExit(1)
