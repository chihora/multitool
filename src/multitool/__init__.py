import argparse
from importlib.metadata import version

from multitool.codec import decode, encode
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
