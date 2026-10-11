# runfiles-conformance

Conformance tests and benchmarks for Bazel runfiles libraries.

Every language ruleset ships its own runfiles library and they do not behave
the same. [SPEC.md](SPEC.md) states the behavior they are expected to share,
[`test/reference/`](test/reference/) implements it, and the badges below show
whether each library conforms at the version pinned in `MODULE.bazel`.

## Conformance

| Library | Status |
|---------|--------|
| C++ `@rules_cc//cc/runfiles` | [![C++](https://github.com/UebelAndre/runfiles-conformance/actions/workflows/test-cc.yaml/badge.svg?branch=main)](https://github.com/UebelAndre/runfiles-conformance/actions/workflows/test-cc.yaml) |
| Go `@rules_go//go/runfiles` | [![Go](https://github.com/UebelAndre/runfiles-conformance/actions/workflows/test-go.yaml/badge.svg?branch=main)](https://github.com/UebelAndre/runfiles-conformance/actions/workflows/test-go.yaml) |
| Java `@rules_java//java/runfiles` | [![Java](https://github.com/UebelAndre/runfiles-conformance/actions/workflows/test-java.yaml/badge.svg?branch=main)](https://github.com/UebelAndre/runfiles-conformance/actions/workflows/test-java.yaml) |
| Python `@rules_python//python/runfiles` | [![Python](https://github.com/UebelAndre/runfiles-conformance/actions/workflows/test-python.yaml/badge.svg?branch=main)](https://github.com/UebelAndre/runfiles-conformance/actions/workflows/test-python.yaml) |
| Rust `@rules_rust//rust/runfiles` | [![Rust](https://github.com/UebelAndre/runfiles-conformance/actions/workflows/test-rust.yaml/badge.svg?branch=main)](https://github.com/UebelAndre/runfiles-conformance/actions/workflows/test-rust.yaml) |
| Shell `@rules_shell//shell/runfiles` | [![Shell](https://github.com/UebelAndre/runfiles-conformance/actions/workflows/test-shell.yaml/badge.svg?branch=main)](https://github.com/UebelAndre/runfiles-conformance/actions/workflows/test-shell.yaml) |
| Perl `@rules_perl//perl/runfiles` | [![Perl](https://github.com/UebelAndre/runfiles-conformance/actions/workflows/test-perl.yaml/badge.svg?branch=main)](https://github.com/UebelAndre/runfiles-conformance/actions/workflows/test-perl.yaml) |
| PowerShell `@rules_powershell//powershell/runfiles` | [![PowerShell](https://github.com/UebelAndre/runfiles-conformance/actions/workflows/test-powershell.yaml/badge.svg?branch=main)](https://github.com/UebelAndre/runfiles-conformance/actions/workflows/test-powershell.yaml) |
| Batch `@rules_batch//batch/runfiles` | [![Batch](https://github.com/UebelAndre/runfiles-conformance/actions/workflows/test-batch.yaml/badge.svg?branch=main)](https://github.com/UebelAndre/runfiles-conformance/actions/workflows/test-batch.yaml) |
| Julia `@rules_julia//julia/runfiles` | [![Julia](https://github.com/UebelAndre/runfiles-conformance/actions/workflows/test-julia.yaml/badge.svg?branch=main)](https://github.com/UebelAndre/runfiles-conformance/actions/workflows/test-julia.yaml) |
| Tcl `@rules_tcl//tcl/runfiles` | [![Tcl](https://github.com/UebelAndre/runfiles-conformance/actions/workflows/test-tcl.yaml/badge.svg?branch=main)](https://github.com/UebelAndre/runfiles-conformance/actions/workflows/test-tcl.yaml) |

A red badge means the library fails at least one scenario. Click it for the
latest run; the test log names each failing scenario. Batch runs on Windows
only.

## Benchmarks

Per-library timings of runfiles creation and lookups, tracked across dependency
updates:
[C++](https://uebelandre.github.io/runfiles-conformance/bench/cc/) ·
[Go](https://uebelandre.github.io/runfiles-conformance/bench/go/) ·
[Java](https://uebelandre.github.io/runfiles-conformance/bench/java/) ·
[Python](https://uebelandre.github.io/runfiles-conformance/bench/python/) ·
[Rust](https://uebelandre.github.io/runfiles-conformance/bench/rust/) ·
[Shell](https://uebelandre.github.io/runfiles-conformance/bench/shell/) ·
[Perl](https://uebelandre.github.io/runfiles-conformance/bench/perl/) ·
[PowerShell](https://uebelandre.github.io/runfiles-conformance/bench/powershell/) ·
[Julia](https://uebelandre.github.io/runfiles-conformance/bench/julia/) ·
[Tcl](https://uebelandre.github.io/runfiles-conformance/bench/tcl/) ·
[Reference](https://uebelandre.github.io/runfiles-conformance/bench/reference/).
Batch is Windows-only and reports benchmarking as unsupported.
Numbers are only comparable across versions of the same library.

## Running

```
bazel test //...                      # the harness against the reference implementation
bazel test //... --config=rust        # one library's conformance test and benchmark
bazel test //... --config=compliance  # every library's conformance test
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for the subject contract, the other
configs, and how to add a library.
