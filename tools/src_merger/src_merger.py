"""A tool for embedding the runfiles api into another source."""

import argparse
from pathlib import Path


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--runfiles", type=Path, required=True, help="The runfiles source file."
    )

    parser.add_argument(
        "--src", type=Path, required=True, help="The source file to embed."
    )

    parser.add_argument(
        "--template",
        type=str,
        required=True,
        help="The template to replace in `src` with `runfiles`.",
    )

    parser.add_argument("--output", type=Path, required=True, help="The output file.")

    return parser.parse_args()


def main() -> None:
    """The main entrypoint."""
    args = parse_args()

    runfiles_content = args.runfiles.read_text(encoding="utf-8")
    content = args.src.read_text(encoding="utf-8")

    content = content.replace(args.template, runfiles_content)

    args.output.write_text(content, encoding="utf-8")


if __name__ == "__main__":
    main()
