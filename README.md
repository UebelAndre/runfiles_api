# runfiles-conformance

Conformance tests and benchmarks for Bazel runfiles libraries.

Every language ruleset ships its own runfiles library and they do not behave
the same. [SPEC.md](SPEC.md) states the behavior they are expected to share,
[`test/reference/`](test/reference/) implements it, and the table below shows
how each library measures up for the versions pinned in `MODULE.bazel`.

## Conformance

| Library | Status | Passing | Diverges from the spec |
|---------|--------|---------|------------------------|
| C++ `@rules_cc//cc/runfiles` | [![C++](https://github.com/UebelAndre/runfiles-conformance/actions/workflows/test-cc.yaml/badge.svg?branch=main)](https://github.com/UebelAndre/runfiles-conformance/actions/workflows/test-cc.yaml) | 22 / 22 | |
| Go `@rules_go//go/runfiles` | [![Go](https://github.com/UebelAndre/runfiles-conformance/actions/workflows/test-go.yaml/badge.svg?branch=main)](https://github.com/UebelAndre/runfiles-conformance/actions/workflows/test-go.yaml) | 20 / 22 | Never reads `<binary>.runfiles/MANIFEST`. |
| Java `@rules_java//java/runfiles` | [![Java](https://github.com/UebelAndre/runfiles-conformance/actions/workflows/test-java.yaml/badge.svg?branch=main)](https://github.com/UebelAndre/runfiles-conformance/actions/workflows/test-java.yaml) | 11 / 22 | Ignores `RUNFILES_MANIFEST_FILE` unless `RUNFILES_MANIFEST_ONLY=1`. No argv0 discovery. |
| Python `@rules_python//python/runfiles` | [![Python](https://github.com/UebelAndre/runfiles-conformance/actions/workflows/test-python.yaml/badge.svg?branch=main)](https://github.com/UebelAndre/runfiles-conformance/actions/workflows/test-python.yaml) | 18 / 22 | No argv0 discovery. |
| Rust `@rules_rust//rust/runfiles` | [![Rust](https://github.com/UebelAndre/runfiles-conformance/actions/workflows/test-rust.yaml/badge.svg?branch=main)](https://github.com/UebelAndre/runfiles-conformance/actions/workflows/test-rust.yaml) | 17 / 22 | Never reads `<binary>.runfiles_manifest`. No manifest directory entries or escaping. Accepts `./` and `../`. |
| Shell `@rules_shell//shell/runfiles` | [![Shell](https://github.com/UebelAndre/runfiles-conformance/actions/workflows/test-shell.yaml/badge.svg?branch=main)](https://github.com/UebelAndre/runfiles-conformance/actions/workflows/test-shell.yaml) | 18 / 22 | Prefers `RUNFILES_DIR` over a manifest. Requires a `bazel_tools` marker inside `<binary>.runfiles`. Accepts `../` between segments. |

A red badge means the library fails at least one scenario. The scenario by
scenario breakdown is in [SPEC.md](SPEC.md#conformance-matrix).

## Benchmarks

Per-library timings of runfiles creation and lookups, tracked across dependency
updates:
[C++](https://uebelandre.github.io/runfiles-conformance/bench/cc/) ·
[Go](https://uebelandre.github.io/runfiles-conformance/bench/go/) ·
[Java](https://uebelandre.github.io/runfiles-conformance/bench/java/) ·
[Python](https://uebelandre.github.io/runfiles-conformance/bench/python/) ·
[Rust](https://uebelandre.github.io/runfiles-conformance/bench/rust/) ·
[Shell](https://uebelandre.github.io/runfiles-conformance/bench/shell/) ·
[Reference](https://uebelandre.github.io/runfiles-conformance/bench/reference/).
Numbers are only comparable across versions of the same library.

## Running

```
bazel test //...                      # the harness against the reference implementation
bazel test //... --config=rust        # one library's conformance test and benchmark
bazel test //... --config=compliance  # every library's conformance test
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for the subject contract, the other
configs, and how to add a library.
