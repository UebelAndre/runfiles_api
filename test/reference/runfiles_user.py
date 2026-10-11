"""A reference runfiles implementation, packaged as a subject.

This subject depends on no ruleset's runfiles library. It implements exactly
the behavior the conformance scenarios expect, so it documents that behavior
as code and lets CI validate the harness independently of any ruleset. If a
scenario and this implementation disagree, one of them is wrong.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Mapping

EXIT_NO_RUNFILES = 2
EXIT_NOT_FOUND = 3

SOURCE_REPO = ""
"""The subject is built in the main repository."""


def _parse_manifest(path: str) -> dict[str, str]:
    """Parse a runfiles manifest, including Bazel's escaped line format."""
    entries: dict[str, str] = {}
    with open(path, encoding="utf-8", newline="\n") as handle:
        for raw in handle:
            line = raw.rstrip("\n")
            if not line:
                continue
            if line.startswith(" "):
                # Spaces, newlines, and backslashes are escaped in the key;
                # newlines and backslashes in the target.
                key, _, target = line[1:].partition(" ")
                key = key.replace("\\s", " ").replace("\\n", "\n").replace("\\b", "\\")
                target = target.replace("\\n", "\n").replace("\\b", "\\")
            else:
                key, _, target = line.partition(" ")
            entries[key] = target or key
    return entries


def _is_normalized(path: str) -> bool:
    """Whether `path` is free of `.`/`..` segments and empty segments."""
    return not (
        path.startswith(("./", "../"))
        or path.endswith(("/.", "/.."))
        or any(part in path for part in ("/./", "/../", "//"))
    )


class Runfiles:
    """Directory- or manifest-based runfiles lookup with repository mapping."""

    def __init__(self, directory: str | None, manifest: dict[str, str] | None):
        self._directory = directory
        self._manifest = manifest
        self._repo_mapping = self._load_repo_mapping()

    @classmethod
    def create(cls, argv0: str, env: Mapping[str, str]) -> Runfiles | None:
        """Discover runfiles from the environment, then from `argv0`."""
        if manifest := env.get("RUNFILES_MANIFEST_FILE"):
            return cls(None, _parse_manifest(manifest))
        if directory := env.get("RUNFILES_DIR"):
            return cls(directory, None)

        for candidate in (f"{argv0}.runfiles/MANIFEST", f"{argv0}.runfiles_manifest"):
            if os.path.isfile(candidate):
                return cls(None, _parse_manifest(candidate))
        if os.path.isdir(f"{argv0}.runfiles"):
            return cls(f"{argv0}.runfiles", None)

        return None

    def _unmapped(self, path: str) -> str | None:
        """Resolve a canonical rlocationpath without consulting the repo mapping."""
        if self._directory is not None:
            return os.path.join(self._directory, path)

        assert self._manifest is not None
        if path in self._manifest:
            return self._manifest[path]

        # A file below a directory entry is only listed via that directory.
        prefix = path
        while "/" in prefix:
            prefix = prefix.rpartition("/")[0]
            if prefix in self._manifest:
                return self._manifest[prefix] + path[len(prefix) :]
        return None

    def _load_repo_mapping(self) -> dict[tuple[str, str], str]:
        location = self._unmapped("_repo_mapping")
        if not location or not os.path.isfile(location):
            return {}

        mapping = {}
        for line in Path(location).read_text(encoding="utf-8").splitlines():
            source, apparent, canonical = line.split(",", 2)
            mapping[(source, apparent)] = canonical
        return mapping

    def rlocation(self, path: str, source_repo: str) -> str | None:
        """Resolve an rlocationpath as seen from `source_repo`."""
        if not path:
            return None
        if os.path.isabs(path):
            return path
        if not _is_normalized(path):
            return None

        apparent, sep, remainder = path.partition("/")
        if sep:
            canonical = self._repo_mapping.get((source_repo, apparent))
            if canonical is not None:
                path = f"{canonical}/{remainder}"

        return self._unmapped(path)


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
    runfiles = Runfiles.create(sys.argv[0], os.environ)
    init_ns = time.perf_counter_ns() - start

    if runfiles is None:
        print("Failed to locate runfiles", file=sys.stderr)
        sys.exit(EXIT_NO_RUNFILES)

    if args.bench is not None:
        start = time.perf_counter_ns()
        for _ in range(args.bench):
            for path in args.paths:
                runfiles.rlocation(path, SOURCE_REPO)
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
        resolved = runfiles.rlocation(path, SOURCE_REPO)
        if not resolved or not Path(resolved).is_file():
            print(f"Failed to locate runfile: {path}", file=sys.stderr)
            sys.exit(EXIT_NOT_FOUND)
        sys.stdout.write(Path(resolved).read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
