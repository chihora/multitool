import argparse
from importlib.metadata import version


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

    args = parser.parse_args()
    if args.command == "echo":
        print(" ".join(args.text))
