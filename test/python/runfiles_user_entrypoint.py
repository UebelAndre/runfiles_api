"""A small binary for accessing runfiles.

Implements the runfiles_api subject contract; see `README.md`.
"""

import argparse
import json
import sys
import time
from pathlib import Path

from python.runfiles import Runfiles

EXIT_NO_RUNFILES = 2
EXIT_NOT_FOUND = 3

SOURCE_REPO = ""
"""The subject is built in the main repository."""


def parse_args() -> argparse.Namespace:
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--bench",
        type=int,
        metavar="ITERATIONS",
        help="Time ITERATIONS lookups of each path and print JSON instead of content.",
    )
    parser.add_argument(
        "paths",
        nargs="+",
        help="The runfiles paths to resolve (e.g., 'workspace/path/to/file.txt')",
    )
    return parser.parse_args()


def main() -> None:
    """The main entrypoint."""
    args = parse_args()

    start = time.perf_counter_ns()
    try:
        runfiles = Runfiles.Create()
    except OSError as err:
        print(f"Failed to locate runfiles: {err}", file=sys.stderr)
        sys.exit(EXIT_NO_RUNFILES)
    init_ns = time.perf_counter_ns() - start

    if runfiles is None:
        print("Failed to locate runfiles", file=sys.stderr)
        sys.exit(EXIT_NO_RUNFILES)

    if args.bench is not None:
        start = time.perf_counter_ns()
        for _ in range(args.bench):
            for path in args.paths:
                runfiles.Rlocation(path, SOURCE_REPO)
        lookup_ns = time.perf_counter_ns() - start
        print(
            json.dumps(
                {
                    "init_ns": init_ns,
                    "lookup_ns": lookup_ns,
                    "iterations": args.bench,
                    "paths": len(args.paths),
                }
            )
        )
        return

    for path in args.paths:
        resolved = runfiles.Rlocation(path, SOURCE_REPO)
        if not resolved or not Path(resolved).is_file():
            print(f"Failed to locate runfile: {path}", file=sys.stderr)
            sys.exit(EXIT_NOT_FOUND)
        sys.stdout.write(Path(resolved).read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
