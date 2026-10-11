"""Rules which expose interpreter locations to the runfiles harness.

The harness launches subjects from a scratch directory outside of any runfiles
tree, so interpreted subjects (Java, Python, shell) need an explicit interpreter.
These rules surface the toolchain's interpreter as a make variable (an
rlocationpath, or an absolute path for the shell toolchain) and carry the
interpreter's files as runfiles.
"""

def _rlocationpath(runfiles_path, workspace_name):
    """Convert a runfiles-relative path (`../repo/x` or `x`) into an rlocationpath."""
    if runfiles_path.startswith("../"):
        return runfiles_path[len("../"):]
    return "{}/{}".format(workspace_name, runfiles_path)

def _java_launcher_impl(ctx):
    java_runtime = ctx.toolchains["@bazel_tools//tools/jdk:runtime_toolchain_type"].java_runtime
    java = _rlocationpath(java_runtime.java_executable_runfiles_path, ctx.workspace_name)

    return [
        platform_common.TemplateVariableInfo({"JAVA_RLOCATIONPATH": java}),
        DefaultInfo(runfiles = ctx.runfiles(transitive_files = java_runtime.files)),
    ]

java_launcher = rule(
    doc = "Exposes the current Java runtime as the `JAVA_RLOCATIONPATH` make variable.",
    implementation = _java_launcher_impl,
    toolchains = ["@bazel_tools//tools/jdk:runtime_toolchain_type"],
)

def _python_launcher_impl(ctx):
    runtime = ctx.toolchains["@rules_python//python:toolchain_type"].py3_runtime

    if runtime.interpreter:
        python = _rlocationpath(runtime.interpreter.short_path, ctx.workspace_name)
        runfiles = ctx.runfiles(
            files = [runtime.interpreter],
            transitive_files = runtime.files,
        )
    else:
        python = runtime.interpreter_path
        runfiles = ctx.runfiles()

    return [
        platform_common.TemplateVariableInfo({"PYTHON_RLOCATIONPATH": python}),
        DefaultInfo(runfiles = runfiles),
    ]

python_launcher = rule(
    doc = "Exposes the current Python runtime as the `PYTHON_RLOCATIONPATH` make variable.",
    implementation = _python_launcher_impl,
    toolchains = ["@rules_python//python:toolchain_type"],
)

def _shell_launcher_impl(ctx):
    bash = ctx.toolchains["@bazel_tools//tools/sh:toolchain_type"].path

    return [
        platform_common.TemplateVariableInfo({"BASH_PATH": bash}),
        DefaultInfo(),
    ]

shell_launcher = rule(
    doc = "Exposes the current shell toolchain's interpreter as the `BASH_PATH` make variable.",
    implementation = _shell_launcher_impl,
    toolchains = ["@bazel_tools//tools/sh:toolchain_type"],
)
