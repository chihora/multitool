import argparse
from importlib.metadata import version

from multitool.codec import decode, encode


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

    args = parser.parse_args()
    if args.command == "echo":
        print(" ".join(args.text))
    elif args.command == "codec":
        operation = encode if args.direction == "encode" else decode
        print(operation(args.scheme, args.text))
