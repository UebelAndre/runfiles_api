"""Runfiles API benchmark scenarios.

Each scenario builds a runfiles layout, invokes the subject in benchmark mode
several times, and records the best observed initialization and per-lookup
times. Subjects time themselves (see `README.md`), so process startup is
excluded.

Results are written to `benchmark.json` in the test's undeclared outputs in
the `customSmallerIsBetter` format consumed by
`benchmark-action/github-action-benchmark`. They are only meaningful when
compared across versions of the same implementation on the same hardware.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator, Mapping, Sequence

import pytest

from harness.layout import make_runfiles_dir, write_manifest
from harness.subject import (
    EXIT_BENCH_UNSUPPORTED,
    EXIT_OK,
    Subject,
    load_subject,
    run,
)

ITERATIONS = int(os.environ.get("RUNFILES_API_BENCH_ITERATIONS", "1000"))
"""How many times each lookup is repeated within one subject invocation."""

ROUNDS = int(os.environ.get("RUNFILES_API_BENCH_ROUNDS", "5"))
"""How many times each scenario invokes the subject. The minimum is reported."""

LOOKUPS = 10
"""How many distinct paths are looked up per iteration."""

MANIFEST_SIZES = (100, 1_000, 10_000)
"""Manifest entry counts to benchmark."""

REPO_MAPPING_SIZES = (10, 1_000)
"""Repository mapping entry counts to benchmark."""


@dataclass(frozen=True)
class Timing:
    """The best timings observed across all rounds of one invocation shape."""

    init_ns: int
    """Nanoseconds to create the runfiles object."""

    lookup_ns: float
    """Nanoseconds per individual lookup."""


@pytest.fixture(name="subject", scope="session")
def subject_fixture(tmp_path_factory: pytest.TempPathFactory) -> Subject:
    """The subject under test. No benchmark touches its directory, so one copy suffices."""
    return load_subject(tmp_path_factory.mktemp("subject"))


@pytest.fixture(name="results", scope="session")
def results_fixture(
    tmp_path_factory: pytest.TempPathFactory,
) -> Iterator[list[dict[str, Any]]]:
    """Collect results and write `benchmark.json` once the session ends."""
    results: list[dict[str, Any]] = []
    yield results

    outputs = os.environ.get("TEST_UNDECLARED_OUTPUTS_DIR")
    output_dir = Path(outputs) if outputs else tmp_path_factory.mktemp("bench")
    output_file = output_dir / "benchmark.json"
    output_file.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")

    width = max((len(entry["name"]) for entry in results), default=0)
    print()
    for entry in results:
        print(f"{entry['name']:<{width}}  {entry['value']:>14,.1f} {entry['unit']}")
    print(f"\nWrote {output_file}")


def bench(subject: Subject, paths: Sequence[str], env: Mapping[str, str]) -> Timing:
    """Run the subject in benchmark mode `ROUNDS` times and keep the best timings."""
    inits: list[int] = []
    lookups: list[float] = []

    for _ in range(ROUNDS):
        result = run(subject, ["--bench", str(ITERATIONS), *paths], env=env)
        if result.returncode == EXIT_BENCH_UNSUPPORTED:
            pytest.skip(result.stderr.strip() or "subject does not support --bench")
        assert result.returncode == EXIT_OK, result

        data = json.loads(result.stdout)
        inits.append(int(data["init_ns"]))
        lookups.append(
            int(data["lookup_ns"]) / (int(data["iterations"]) * int(data["paths"]))
        )

    return Timing(init_ns=min(inits), lookup_ns=min(lookups))


@dataclass(frozen=True)
class Layout:
    """A runfiles layout to benchmark."""

    scenario: str
    """The name reported for this layout."""

    hits: Sequence[str]
    """Paths that resolve in the layout."""

    misses: Sequence[str]
    """Paths that do not resolve in the layout."""

    env: Mapping[str, str]
    """Environment variables pointing the subject at the layout."""


def record(results: list[dict[str, Any]], subject: Subject, layout: Layout) -> None:
    """Benchmark hits and misses for one layout and append the results."""
    hit = bench(subject, layout.hits, layout.env)
    miss = bench(subject, layout.misses, layout.env)

    extra = f"{subject.lang}, iterations={ITERATIONS}, rounds={ROUNDS}"
    results.extend(
        [
            {
                "name": f"{layout.scenario} / init",
                "unit": "ns",
                "value": min(hit.init_ns, miss.init_ns),
                "extra": extra,
            },
            {
                "name": f"{layout.scenario} / lookup hit",
                "unit": "ns/lookup",
                "value": round(hit.lookup_ns, 1),
                "extra": extra,
            },
            {
                "name": f"{layout.scenario} / lookup miss",
                "unit": "ns/lookup",
                "value": round(miss.lookup_ns, 1),
                "extra": extra,
            },
        ]
    )


def data_keys(count: int, subdir: str = "data") -> list[str]:
    """Generate `count` rlocationpaths in the main repository."""
    return [f"runfiles_api/{subdir}/{i:06d}.txt" for i in range(count)]


MISSES = data_keys(LOOKUPS, "missing")
"""Paths that never exist in any layout."""


def test_bench_directory(
    subject: Subject, tmp_path: Path, results: list[dict[str, Any]]
) -> None:
    """Directory-based lookups."""
    hits = data_keys(LOOKUPS)
    runfiles_dir = make_runfiles_dir(tmp_path / "runfiles", {key: key for key in hits})
    record(
        results,
        subject,
        Layout("directory", hits, MISSES, {"RUNFILES_DIR": str(runfiles_dir)}),
    )


@pytest.mark.parametrize("size", MANIFEST_SIZES)
def test_bench_manifest(
    subject: Subject, tmp_path: Path, results: list[dict[str, Any]], size: int
) -> None:
    """Manifest-based lookups as the manifest grows."""
    keys = data_keys(size)
    files_dir = tmp_path / "files"
    manifest = write_manifest(
        tmp_path / "MANIFEST", {key: files_dir / key for key in keys}
    )
    # RUNFILES_MANIFEST_ONLY is what Bazel sets alongside the manifest on
    # Windows, and the Java library requires it to use the manifest at all.
    env = {"RUNFILES_MANIFEST_FILE": str(manifest), "RUNFILES_MANIFEST_ONLY": "1"}
    record(
        results,
        subject,
        Layout(f"manifest ({size} entries)", keys[-LOOKUPS:], MISSES, env),
    )


@pytest.mark.parametrize("size", REPO_MAPPING_SIZES)
def test_bench_repo_mapping(
    subject: Subject, tmp_path: Path, results: list[dict[str, Any]], size: int
) -> None:
    """Directory-based lookups through a repository mapping as the mapping grows."""
    mapping = "".join(f",repo_{i:06d},repo_{i:06d}+\n" for i in range(size))
    hits = [f"repo_{i:06d}/data.txt" for i in range(LOOKUPS)]
    misses = [f"unmapped_{i:06d}/data.txt" for i in range(LOOKUPS)]
    files = {"_repo_mapping": mapping}
    files.update({f"repo_{i:06d}+/data.txt": hit for i, hit in enumerate(hits)})
    runfiles_dir = make_runfiles_dir(tmp_path / "runfiles", files)
    record(
        results,
        subject,
        Layout(
            f"repo mapping ({size} entries)",
            hits,
            misses,
            {"RUNFILES_DIR": str(runfiles_dir)},
        ),
    )
