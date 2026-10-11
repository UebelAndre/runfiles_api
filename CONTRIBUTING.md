# Contributing

## How the harness works

Each language implements one *subject*: a small program that resolves an
rlocationpath with that language's runfiles library and prints the file. The
harness ([`runfiles_conformance_test.py`](runfiles_conformance_test.py)) copies
the subject out of its runfiles tree into a scratch directory, strips every
discovery-related variable from the environment (`RUNFILES_*`,
`JAVA_RUNFILES`, `TEST_SRCDIR`, ...), lays out exactly the files and variables
a scenario calls for, and checks the subject's exit code and output. The
harness never uses a runfiles library itself.

Targets are declared with the `runfiles_conformance_test` and
`runfiles_conformance_benchmark` macros from
[`runfiles_conformance_test.bzl`](runfiles_conformance_test.bzl).

## Subject contract

```
subject [--bench ITERATIONS] RLOCATIONPATH...
```

The subject must be a single self-contained file. Interpreted subjects get an
explicit launcher from the macro (`launcher` and `tools` attributes; see
[`test/java/BUILD.bazel`](test/java/BUILD.bazel)), so they must not rely on
their Bazel launcher stub.

Without `--bench`, the subject creates a runfiles object with the source
repository set to the main repository, resolves each path, and writes the
file's content to stdout. Exit codes:

| Code | Meaning |
|------|---------|
| 0 | Every path resolved and was printed. |
| 1 | Any other error (bad usage, crash, read failure). |
| 2 | The library could not discover runfiles. |
| 3 | Runfiles were discovered but a path did not resolve to an existing file. |
| 5 | `--bench` is not supported (Bash older than 5). |

With `--bench N`, the subject times runfiles creation, then times `N`
repetitions of resolving every path with no file I/O, and prints one JSON
object:

```json
{"init_ns": 12345, "lookup_ns": 6789012, "iterations": 1000, "paths": 10}
```

Subjects time themselves so that process startup is excluded.

## Running locally

Targets under `test/<lang>/` are tagged with their language and excluded from
wildcard invocations by default. Opt in with a config:

```
bazel test //...                      # harness (via the reference subject) and repo checks
bazel test //... --config=rust        # Rust conformance test and benchmark
bazel test //... --config=compliance  # every library's conformance test
bazel test //... --config=benchmark   # every library's benchmark
bazel test //... --config=all         # everything
bazel build //... --config=all        # build everything, run nothing
```

The filter applies to explicitly named targets too, so
`bazel test //test/rust:test_runfiles` needs `--config=rust`. Expect
`--config=compliance` and `--config=all` to report failures: a non-conforming
library fails its conformance test.

There is no `.bazelversion`. CI covers Bazel 7.x, 8.x, and 9.x on Linux,
macOS, and Windows; use `USE_BAZEL_VERSION=8.x` to pick one locally.

## CI

- **CI** gates pull requests. It runs the reference subject's conformance test
  and benchmark on every OS and Bazel version and builds every target. It
  never depends on a library's compliance.
- **Test &lt;language&gt;** workflows produce the badges. They run on pushes
  to `main` and on demand, and are red whenever the library fails a scenario.
  The job log is the record of which scenarios fail.
- **Benchmark** runs on pushes to `main` and publishes to the `gh-pages`
  branch.

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
Results land in `benchmark.json` under the test's undeclared outputs.

## Adding a scenario

1. State the behavior in [SPEC.md](SPEC.md) and tag it with the scenario name.
2. Implement it in the reference subject if it does not already satisfy it.
3. Add the test. It must pass against the reference subject.
4. Run `--config=compliance`. For each library that fails the new scenario,
   confirm in its source that the failure is the library's behavior and not a
   harness bug.

## Adding a library

1. Add a subject under `test/<lang>/` implementing the contract above.
2. Define `runfiles_conformance_test` and `runfiles_conformance_benchmark`
   targets, tagging the subject binary with `<lang>`.
3. Add `build:<lang>` / `test:<lang>` configs to `.bazelrc` and the language to
   the default exclusion list there.
4. Add a `test-<lang>.yaml` workflow like the existing ones and a row to the
   README table.
