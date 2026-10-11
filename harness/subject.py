"""Launch a runfiles subject under controlled conditions.

The harness itself runs inside a Bazel test and therefore inside a runfiles
tree. Everything in this module exists to keep that tree from leaking into the
subject: the subject binary is copied to a scratch directory, discovery-related
environment variables are stripped, and the subject is located without using
any runfiles library.

The subject contract (command line, exit codes, benchmark output) is documented
in `README.md`.
"""

from __future__ import annotations

import functools
import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

EXIT_OK = 0
"""The subject succeeded."""

EXIT_ERROR = 1
"""The subject failed for a reason unrelated to runfiles (usage, I/O, crash)."""

EXIT_NO_RUNFILES = 2
"""The subject could not discover any runfiles."""

EXIT_NOT_FOUND = 3
"""Runfiles were discovered but the requested runfile could not be resolved."""

EXIT_BENCH_UNSUPPORTED = 5
"""The subject does not support benchmark mode."""

SCRUBBED_ENV_VARS = frozenset(
    {
        "JAVA_RUNFILES",
        "PYTHON_RUNFILES",
        "REPOSITORY_NAME",
        "TEST_SRCDIR",
        "TEST_WORKSPACE",
    }
)
"""Environment variables never inherited by subjects."""

SCRUBBED_ENV_PREFIXES = ("RUNFILES_",)
"""Environment variable prefixes never inherited by subjects."""


def clean_environment() -> dict[str, str]:
    """Return the harness environment with all runfiles discovery inputs removed.

    Everything else (`PATH`, `HOME`, `SYSTEMROOT`, temp dirs) is kept so that
    interpreters and JVMs can start normally.
    """
    return {
        key: value
        for key, value in os.environ.items()
        if key not in SCRUBBED_ENV_VARS and not key.startswith(SCRUBBED_ENV_PREFIXES)
    }


@functools.cache
def locate_runfile(rlocationpath: str) -> Path:
    """Locate a runfile of the harness without using a runfiles library.

    Args:
        rlocationpath: The runfiles path (e.g., `workspace/path/to/file`).

    Returns:
        The absolute path to the runfile.

    Raises:
        FileNotFoundError: If the runfile cannot be located.
    """
    for var in ("RUNFILES_DIR", "TEST_SRCDIR"):
        if root := os.environ.get(var):
            path = Path(root) / rlocationpath
            if path.exists():
                return path

    if manifest := os.environ.get("RUNFILES_MANIFEST_FILE"):
        if Path(manifest).exists():
            with open(manifest, "r", encoding="utf-8") as handle:
                for line in handle:
                    parts = line.rstrip("\n").split(" ", 1)
                    if len(parts) == 2 and parts[0] == rlocationpath:
                        return Path(parts[1])

    raise FileNotFoundError(f"Failed to locate runfile: {rlocationpath}")


@functools.cache
def resolve_launcher_element(element: str) -> str:
    """Resolve one element of a launcher command.

    Flags and absolute paths are passed through; anything else is an
    rlocationpath of the harness.
    """
    if element.startswith("-") or os.path.isabs(element):
        return element
    return str(locate_runfile(element))


@dataclass(frozen=True)
class Subject:
    """A runfiles implementation under test."""

    lang: str
    """The identifier of the implementation (e.g. `rust`)."""

    path: Path
    """The copy of the subject binary in the scratch directory."""

    launcher: tuple[str, ...]
    """The command prefix used to launch `path`."""

    def command(self, args: Sequence[str]) -> list[str]:
        """Build the full command line for invoking the subject."""
        return [*self.launcher, str(self.path), *args]


def load_subject(scratch: Path) -> Subject:
    """Copy the subject binary described by the environment into `scratch`.

    Args:
        scratch: A directory unique to the current test.

    Returns:
        The subject, ready to be launched.
    """
    lang = os.environ.get("RUNFILES_API_LANG")
    rlocationpath = os.environ.get("RUNFILES_API_SUBJECT")
    launcher_json = os.environ.get("RUNFILES_API_LAUNCHER", "[]")
    if not lang or not rlocationpath:
        raise RuntimeError(
            "RUNFILES_API_LANG and RUNFILES_API_SUBJECT must be set. "
            "Use the `runfiles_api_test` macro to define tests."
        )

    source = locate_runfile(rlocationpath)

    scratch_dir = scratch / "subject"
    scratch_dir.mkdir(parents=True, exist_ok=True)
    copy = scratch_dir / source.name
    shutil.copy2(source, copy)
    copy.chmod(0o755)

    launcher = tuple(
        resolve_launcher_element(element) for element in json.loads(launcher_json)
    )

    return Subject(lang=lang, path=copy, launcher=launcher)


@dataclass(frozen=True)
class Result:
    """The outcome of a subject invocation."""

    command: tuple[str, ...]
    env: Mapping[str, str]
    returncode: int
    stdout: str
    stderr: str

    def __str__(self) -> str:
        return "\n".join(
            [
                f"command: {' '.join(self.command)}",
                f"exit code: {self.returncode}",
                *(f"env: {key}={value!r}" for key, value in sorted(self.env.items())),
                f"stdout: {self.stdout!r}",
                f"stderr: {self.stderr!r}",
            ]
        )


def run(
    subject: Subject,
    args: Sequence[str],
    env: Mapping[str, str] | None = None,
    cwd: Path | None = None,
    timeout: float = 600.0,
) -> Result:
    """Invoke the subject with a scrubbed environment.

    Args:
        subject: The subject to invoke.
        args: Arguments passed after the subject binary.
        env: Environment variables to set on top of the scrubbed environment.
            These are the only runfiles discovery inputs the subject will see.
        cwd: The working directory for the subject.
        timeout: Seconds to wait before killing the subject.

    Returns:
        The captured result.
    """
    full_env = clean_environment()
    overrides = dict(env or {})
    full_env.update(overrides)

    command = subject.command(args)
    proc = subprocess.run(
        command,
        env=full_env,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=timeout,
    )

    return Result(
        command=tuple(command),
        env=overrides,
        returncode=proc.returncode,
        stdout=proc.stdout.decode("utf-8", errors="replace"),
        stderr=proc.stderr.decode("utf-8", errors="replace"),
    )
