"""Utilities for producing single-file subjects."""

def _find_runfiles_src(target, basename):
    """Locate the single-file runfiles library source provided by `target`.

    Depending on the ruleset and Bazel version the file is exposed as a plain
    source (e.g. `@bazel_tools//tools/bash/runfiles`), as a default output, or
    only as a root symlink in the target's runfiles.
    """
    candidates = (
        target[DefaultInfo].files.to_list() +
        target[DefaultInfo].default_runfiles.files.to_list()
    )
    for src in candidates:
        if src.basename == basename:
            return src

    for entry in target[DefaultInfo].default_runfiles.root_symlinks.to_list():
        if entry.target_file.basename == basename:
            return entry.target_file

    fail("Failed to find `{}` in: {}".format(basename, target.label))

def _runfiles_source_file_impl(ctx):
    runfiles_src = _find_runfiles_src(ctx.attr.runfiles, ctx.attr.basename)

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
    doc = "Inline a single-file runfiles library into a script so the result can run outside of a runfiles tree.",
    implementation = _runfiles_source_file_impl,
    attrs = {
        "basename": attr.string(
            doc = "The file name of the runfiles library source within `runfiles`.",
            mandatory = True,
        ),
        "out": attr.output(
            doc = "The output file to generate",
            mandatory = True,
        ),
        "runfiles": attr.label(
            doc = "The runfiles library, or its source file directly.",
            allow_files = True,
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
