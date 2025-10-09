"""Python utiltiies"""

load("@rules_venv//python:py_info.bzl", "PyInfo")

def _find_python_runfiles(target):
    runfiles_src = None

    for src in target[DefaultInfo].files.to_list():
        if src.basename == "runfiles.py":
            runfiles_src = src
            break

    if not runfiles_src:
        fail("Failed to find runfiles src from: {}".format(target.label))

    return runfiles_src

def _find_bash_runfiles(target):
    runfiles_src = None

    for entry in target[DefaultInfo].default_runfiles.root_symlinks.to_list():
        if entry.target_file.basename == "runfiles.bash":
            runfiles_src = entry.target_file
            break

    if not runfiles_src:
        fail("Failed to find runfiles src from: {}".format(target.label))

    return runfiles_src

def _runfiles_source_file_impl(ctx):
    runfiles_src = None

    if PyInfo in ctx.attr.runfiles:
        runfiles_src = _find_python_runfiles(ctx.attr.runfiles)
    else:
        runfiles_src = _find_bash_runfiles(ctx.attr.runfiles)

    output = ctx.outputs.out

    args = ctx.actions.args()
    args.add("--runfiles", runfiles_src)
    args.add("--src", ctx.file.src)
    args.add("--template", ctx.attr.template)
    args.add("--output", output)

    ctx.actions.run(
        mnemonic = "RunfilesSrcMerger",
        executable = ctx.executable._merger,
        arguments = [args],
        inputs = [runfiles_src, ctx.file.src],
        outputs = [output],
    )

    return [DefaultInfo(
        files = depset([output]),
    )]

runfiles_source_file = rule(
    doc = "A utility rule for locating the runfiles main source from a runfiles library.",
    implementation = _runfiles_source_file_impl,
    attrs = {
        "out": attr.output(
            doc = "The output file to generate",
            mandatory = True,
        ),
        "runfiles": attr.label(
            doc = "The runfiles library.",
            mandatory = True,
        ),
        "src": attr.label(
            doc = "Extra content to append to the bottom of the `runfiles` file.",
            allow_single_file = True,
            mandatory = True,
        ),
        "template": attr.string(
            doc = "The template string to replace with the runfiles content.",
            mandatory = True,
        ),
        "_merger": attr.label(
            executable = True,
            cfg = "exec",
            default = Label("//tools/src_merger"),
        ),
    },
)
