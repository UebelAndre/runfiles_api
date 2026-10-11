"""Macros for testing and benchmarking a runfiles implementation."""

load("@rules_venv//python/pytest:defs.bzl", "py_pytest_test")

def _subject_test(name, src, binary, lang, launcher, tools, subject_env, env, kind, **kwargs):
    """Define a pytest target that runs `src` against a subject binary.

    The target is tagged with `kind` (`compliance` or `benchmark`) and `lang`
    so `.bazelrc` configs can select it; see CONTRIBUTING.md.
    """
    test_env = {
        "RUNFILES_CONFORMANCE_LANG": lang,
        "RUNFILES_CONFORMANCE_LAUNCHER": json.encode(launcher),
        "RUNFILES_CONFORMANCE_SUBJECT": "$(rlocationpath {})".format(binary),
        "RUNFILES_CONFORMANCE_SUBJECT_ENV": json.encode(subject_env),
    }
    test_env.update(env)

    py_pytest_test(
        name = name,
        srcs = [src],
        deps = [Label("//harness")],
        data = [binary] + tools,
        toolchains = tools,
        env = test_env,
        tags = [kind, lang] + kwargs.pop("tags", []),
        **kwargs
    )

def runfiles_conformance_test(
        name,
        binary,
        lang,
        launcher = [],
        tools = [],
        subject_env = {},
        env = {},
        **kwargs):
    """Create a test that validates a runfiles implementation against the subject contract.

    See `CONTRIBUTING.md` for the contract the `binary` must implement.

    Args:
        name: The name of the test target.
        binary: The subject binary. It is copied out of the runfiles tree before
            being launched, so it must be a single self-contained file.
        lang: An identifier for the implementation under test (e.g. `rust`),
            reported alongside results.
        launcher: Command prefix used to launch `binary`. Flags and absolute
            paths are passed through, anything else is an rlocationpath, and
            `$(VAR)` make variables from `tools` are expanded.
        tools: Targets providing make variables and runfiles for `launcher`.
        subject_env: Environment variables the subject's interpreter needs in
            every scenario (e.g. `TCL_LIBRARY`). Values are resolved like
            `launcher` elements.
        env: Additional environment variables for the test.
        **kwargs: Additional arguments passed to `py_pytest_test`.
    """
    _subject_test(
        name,
        Label("//:runfiles_conformance_test.py"),
        binary,
        lang,
        launcher,
        tools,
        subject_env,
        env,
        kind = "compliance",
        **kwargs
    )

def runfiles_conformance_benchmark(
        name,
        binary,
        lang,
        launcher = [],
        tools = [],
        subject_env = {},
        iterations = 1000,
        rounds = 5,
        env = {},
        timeout = "long",
        **kwargs):
    """Create a test that benchmarks a runfiles implementation.

    Results are written to `benchmark.json` in the test's undeclared outputs in
    the `customSmallerIsBetter` format used by `benchmark-action/github-action-benchmark`.

    Args:
        name: The name of the test target.
        binary: The subject binary. See `runfiles_conformance_test`.
        lang: An identifier for the implementation under test (e.g. `rust`).
        launcher: Command prefix used to launch `binary`. See `runfiles_conformance_test`.
        tools: Targets providing make variables and runfiles for `launcher`.
        subject_env: See `runfiles_conformance_test`.
        iterations: The number of times each lookup is repeated per round.
        rounds: The number of subject invocations per scenario. The minimum is reported.
        env: Additional environment variables for the test.
        timeout: The test timeout.
        **kwargs: Additional arguments passed to `py_pytest_test`.
    """
    bench_env = {
        "RUNFILES_CONFORMANCE_BENCH_ITERATIONS": str(iterations),
        "RUNFILES_CONFORMANCE_BENCH_ROUNDS": str(rounds),
    }
    bench_env.update(env)

    _subject_test(
        name,
        Label("//:runfiles_conformance_bench.py"),
        binary,
        lang,
        launcher,
        tools,
        subject_env,
        bench_env,
        kind = "benchmark",
        timeout = timeout,
        **kwargs
    )
