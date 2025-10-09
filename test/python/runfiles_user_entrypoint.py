"""A simple Python binary for testing runfiles API.

This binary takes a runfiles path as an argument, resolves it via the runfiles
API, and prints the file contents.
"""

import argparse
import platform
from pathlib import Path

from python.runfiles import Runfiles


def parse_args() -> argparse.Namespace:
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "path", help="The runfiles path to resolve (e.g., 'workspace/path/to/file.txt')"
    )
    return parser.parse_args()


def rlocation(runfiles: Runfiles, rlocationpath: str) -> Path:
    """Look up a runfile and ensure the file exists

    Args:
        runfiles: The runfiles object
        rlocationpath: The runfile key

    Returns:
        The requested runifle.
    """
    # TODO: https://github.com/periareon/rules_venv/issues/37
    source_repo = None
    if platform.system() == "Windows":
        source_repo = ""
    runfile = runfiles.Rlocation(rlocationpath, source_repo)
    if not runfile:
        raise FileNotFoundError(f"Failed to find runfile: {rlocationpath}")
    path = Path(runfile)
    if not path.exists():
        raise FileNotFoundError(f"Runfile does not exist: ({rlocationpath}) {path}")
    return path


def main() -> None:
    """The main entrypoint."""
    args = parse_args()

    runfiles = Runfiles.Create()
    if not runfiles:
        raise EnvironmentError("Failed to locate runfiles")

    path = rlocation(runfiles, args.path)

    print(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
