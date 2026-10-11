# runfiles_api

A conformance and benchmark suite for Bazel runfiles libraries.

Every Bazel language ruleset ships a runfiles library, and they do not all
behave the same way. This repository documents those differences by running a
single suite of scenarios against a small subject binary built with each
library. It exists to inform; nothing is consumed from it.

## Status

| Language | Library | Status |
|----------|---------|--------|
| C++ | `@rules_cc//cc/runfiles` | [![C++](https://github.com/UebelAndre/runfiles_api/actions/workflows/test-cc.yaml/badge.svg?branch=main)](https://github.com/UebelAndre/runfiles_api/actions/workflows/test-cc.yaml) |
| Go | `@rules_go//go/runfiles` | [![Go](https://github.com/UebelAndre/runfiles_api/actions/workflows/test-go.yaml/badge.svg?branch=main)](https://github.com/UebelAndre/runfiles_api/actions/workflows/test-go.yaml) |
| Java | `@rules_java//java/runfiles` | [![Java](https://github.com/UebelAndre/runfiles_api/actions/workflows/test-java.yaml/badge.svg?branch=main)](https://github.com/UebelAndre/runfiles_api/actions/workflows/test-java.yaml) |
| Python | `@rules_python//python/runfiles` | [![Python](https://github.com/UebelAndre/runfiles_api/actions/workflows/test-python.yaml/badge.svg?branch=main)](https://github.com/UebelAndre/runfiles_api/actions/workflows/test-python.yaml) |
| Rust | `@rules_rust//rust/runfiles` | [![Rust](https://github.com/UebelAndre/runfiles_api/actions/workflows/test-rust.yaml/badge.svg?branch=main)](https://github.com/UebelAndre/runfiles_api/actions/workflows/test-rust.yaml) |
| Shell | `@rules_shell//shell/runfiles` | [![Shell](https://github.com/UebelAndre/runfiles_api/actions/workflows/test-shell.yaml/badge.svg?branch=main)](https://github.com/UebelAndre/runfiles_api/actions/workflows/test-shell.yaml) |

A green badge means the library passes every conformance scenario on every
supported OS and Bazel version. Red means it diverges from the specification
somewhere; the tables below record where, for the versions pinned in
`MODULE.bazel`. These workflows run on pushes to `main` and are informational.
Pull requests are gated by the [CI](.github/workflows/ci.yaml) workflow, which
validates the harness against the reference implementation instead.

Benchmark history is published to the `gh-pages` branch, one chart page per
language: [C++](https://uebelandre.github.io/runfiles_api/bench/cc/),
[Go](https://uebelandre.github.io/runfiles_api/bench/go/),
[Java](https://uebelandre.github.io/runfiles_api/bench/java/),
[Python](https://uebelandre.github.io/runfiles_api/bench/python/),
[Rust](https://uebelandre.github.io/runfiles_api/bench/rust/),
[Shell](https://uebelandre.github.io/runfiles_api/bench/shell/).

## How it works

Each language implements one subject binary that resolves an rlocationpath and
prints the file. The subject is copied out of its runfiles tree into a scratch
directory, launched with a scrubbed environment (every `RUNFILES_*`,
`JAVA_RUNFILES`, `TEST_SRCDIR`, ... variable removed), and given exactly the
discovery inputs a scenario wants to exercise. The harness never uses a
runfiles library itself.

The harness is [`runfiles_api_test.py`](runfiles_api_test.py) (conformance)
and [`runfiles_api_bench.py`](runfiles_api_bench.py) (benchmarks), driven by
the `runfiles_api_test` and `runfiles_api_benchmark` macros in
[`runfiles_api_test.bzl`](runfiles_api_test.bzl).

[`test/reference/runfiles_user.py`](test/reference/runfiles_user.py) is a
reference implementation of the specification with no ruleset dependency. It
must pass every scenario, and CI runs it on every OS and Bazel version so that
a harness or scenario bug is caught independently of library compliance.

### Subject contract

```
subject [--bench ITERATIONS] RLOCATIONPATH...
```

The subject must be a single self-contained file. Interpreted subjects receive
an explicit launcher from the macro (the JDK for the Java deploy jar, the
Python toolchain's interpreter for Python, the shell toolchain's `bash` for
shell), so they must not rely on their Bazel launcher stub.

Without `--bench`, the subject creates a runfiles object, resolves each path
with the library's source repository set to the main repository, and writes the
file's content to stdout. Exit codes:

| Code | Meaning |
|------|---------|
| 0 | Every path resolved and was printed. |
| 1 | Any other error (bad usage, crash, read failure). |
| 2 | The library could not discover runfiles. |
| 3 | Runfiles were discovered but a path did not resolve to an existing file. |
| 5 | `--bench` is not supported (Bash older than 5). |

With `--bench N`, the subject times runfiles creation, then times `N`
repetitions of resolving every path (no file I/O), and prints one JSON object:

```json
{"init_ns": 12345, "lookup_ns": 6789012, "iterations": 1000, "paths": 10}
```

Subjects time themselves so that process startup is excluded.

## Conformance scenarios

The scenarios encode the behavior described by the
[runfiles library design](https://github.com/bazelbuild/proposals/blob/main/designs/2018-07-18-runfiles-libraries.md)
and implemented by the C++ library, which the others were originally ported
from. A cell is empty when the library satisfies the scenario; otherwise it
names the divergence described in the next section. The table is maintained
by hand from the compliance workflow results.

| Scenario | C++ | Go | Java | Python | Rust | Shell |
|----------|-----|----|------|--------|------|-------|
| **Environment-based discovery** | | | | | | |
| No discovery inputs: exit 2 | | | | | | |
| `RUNFILES_DIR` alone | | | | | | |
| `RUNFILES_MANIFEST_FILE` alone | | | J1 | | | |
| Manifest wins when both are set | | | J1 | | | S2 |
| `RUNFILES_MANIFEST_ONLY=1` forces the manifest | | | | | | S2 |
| Empty `RUNFILES_MANIFEST_FILE` is ignored | | | | | | |
| **argv0-based discovery** | | | | | | |
| `<binary>.runfiles/` | | | J2 | P1 | | S1 |
| `<binary>.runfiles/MANIFEST` | | G1 | J2 | P1 | | |
| `<binary>.runfiles_manifest` | | | J2 | P1 | R1 | |
| `<binary>.runfiles/MANIFEST` with empty `RUNFILES_MANIFEST_FILE` | | G1 | J2 | P1 | | |
| Inherited environment wins over `<binary>.runfiles/` | | | | | | |
| **Lookup semantics** | | | | | | |
| Missing file in a directory: exit 3 | | | | | | |
| Missing key in a manifest: exit 3 | | | J1 | | | |
| Path below a manifest directory entry | | | J1 | | R2 | |
| Manifest target containing spaces | | | J1 | | | |
| Escaped manifest entry (key containing spaces) | | | J1 | | R3 | |
| Absolute path returned unchanged | | | | | | |
| `..` segments rejected | | | | | R4 | S3 |
| `./` segments rejected | | | | | R4 | |
| **Repository mapping** | | | | | | |
| Apparent name of an external repo (directory) | | | | | | |
| Apparent name of the main repo maps to `_main` | | | | | | |
| Apparent name of an external repo (manifest) | | | J1 | | | |

### Observed divergences

| Id | Library | Behavior |
|----|---------|----------|
| G1 | Go | Probes `<argv0>.runfiles_manifest` and `<argv0>.runfiles` but never `<argv0>.runfiles/MANIFEST`. |
| J1 | Java | Only reads `RUNFILES_MANIFEST_FILE` when `RUNFILES_MANIFEST_ONLY=1`; otherwise requires `RUNFILES_DIR` or `JAVA_RUNFILES`. |
| J2 | Java | No argv0 discovery. The `java_binary` launcher stub is responsible for exporting `RUNFILES_DIR` / `JAVA_RUNFILES`. |
| P1 | Python | No argv0 discovery. `Runfiles.Create()` returns `None` unless `RUNFILES_MANIFEST_FILE` or `RUNFILES_DIR` is set. |
| R1 | Rust | Probes `<argv0>.runfiles` (and `MANIFEST` inside it) but never `<argv0>.runfiles_manifest`. |
| R2 | Rust | Exact manifest lookups only; does not resolve paths below a directory entry. |
| R3 | Rust | Does not decode escaped manifest entries (lines starting with a space). |
| R4 | Rust | Does not reject non-normalized paths (`./`, `../`). |
| S1 | Shell | Only accepts an adjacent `.runfiles` directory if it contains `bazel_tools/tools/bash/runfiles/runfiles.bash`. |
| S2 | Shell | Prefers `RUNFILES_DIR` over `RUNFILES_MANIFEST_FILE` when both are set, and ignores `RUNFILES_MANIFEST_ONLY`. |
| S3 | Shell | Rejects `../` only at the start or end of a path, not between segments. |

On Bazel 7, `@rules_shell//shell/runfiles` is an alias for
`@bazel_tools//tools/bash/runfiles`; that copy shows the same gaps.

Some divergences are deliberate design choices of the ruleset rather than bugs
(J2 and P1 in particular, where the launcher stub owns discovery). They are listed
because a user who copies a binary out of `bazel-bin` will hit them either way.

## Benchmarks

Each `bench_runfiles` target runs the subject in `--bench` mode against
generated layouts and records the best of several rounds:

| Scenario | Measures |
|----------|----------|
| `directory` | Directory-based creation, hit and miss lookups. |
| `manifest (N entries)` | Manifest parsing and lookups for N = 100, 1 000, 10 000. |
| `repo mapping (N entries)` | `_repo_mapping` parsing and mapped lookups for N = 10, 1 000. |

Three values are reported per scenario: `init` (nanoseconds to create the
runfiles object), `lookup hit`, and `lookup miss` (nanoseconds per lookup).
Results land in `benchmark.json` under the test's undeclared outputs and the
[Benchmark](.github/workflows/benchmark.yaml) workflow publishes them to
`gh-pages` on every push to `main`, so the charts track each library across
the dependency updates Renovate opens.

The numbers are only comparable across versions of the same library on the
same runner type. Comparing languages against each other mostly measures the
languages.

## Running locally

Targets under `test/<lang>/` are tagged with their language and excluded from
wildcard invocations by default, so a plain `bazel test //...` exercises only
the harness (via the reference subject) and the repository's own checks. Opt
into a language integration with its config:

```
bazel test //...                      # harness and repository checks only
bazel test //... --config=rust        # Rust compliance test and benchmark
bazel test //... --config=compliance  # every library's conformance test
bazel test //... --config=benchmark   # every library's benchmark
bazel test //... --config=all         # everything
bazel build //... --config=all        # build everything, run nothing
```

The filter applies to explicitly named targets too, so
`bazel test //test/rust:test_runfiles` needs `--config=rust` as well. Expect
`--config=compliance` and `--config=all` to report failures: every library with
a recorded divergence fails its conformance test.

CI runs every suite on Bazel 7.x, 8.x, and 9.x across Linux, macOS, and
Windows. There is no `.bazelversion`; pick a version with
`USE_BAZEL_VERSION=8.x` if you need a specific one.

## Adding an implementation

1. Add a subject under `test/<lang>/` implementing the contract above.
2. Define `runfiles_api_test` and `runfiles_api_benchmark` targets, passing a
   `launcher` and `tools` if the subject needs an interpreter (see
   `test/java/BUILD.bazel`).
3. Run the conformance test. For every failing scenario, confirm in the
   library's source that the failure is the library's behavior (and not a
   harness bug, which the reference subject would also show) and record it in
   the tables above.
4. Add `build:<lang>` / `test:<lang>` configs to `.bazelrc` and the language to
   the default exclusion list there.
5. Add a `test-<lang>.yaml` workflow like the existing ones and a badge to the
   status table.
