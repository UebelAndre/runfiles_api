# Runfiles library specification

This document states the behavior a Bazel runfiles library is expected to
have. There is no upstream specification; the C++ library in Bazel was the
original and the others were ported from it with varying fidelity. The
scenarios in [`runfiles_conformance_test.py`](runfiles_conformance_test.py)
test each statement below, and
[`test/reference/runfiles_user.py`](test/reference/runfiles_user.py) is a
minimal implementation that satisfies all of them. Where this document, the
scenarios, and the reference implementation disagree, it is a bug here.

Statements are tagged with the scenario that tests them, e.g. `[dir_env]`
refers to `test_runfiles_dir_env`.

## Terms

- **rlocationpath**: a slash-separated path whose first segment is a
  repository name, e.g. `rules_foo/pkg/file.txt`. Always relative.
- **Runfiles directory**: a tree on disk in which an rlocationpath is a
  relative path to the file.
- **Runfiles manifest**: a text file mapping rlocationpaths to absolute paths.
- **Source repository**: the repository the calling code was built in. It
  determines how apparent repository names are resolved.

## Discovery

A library decides where runfiles are by checking, in order:

1. `RUNFILES_MANIFEST_FILE`, if set and non-empty: manifest-based.
   `[manifest_env]` `[manifest_env_takes_precedence_over_dir_env]`
2. `RUNFILES_DIR`, if set and non-empty: directory-based. `[dir_env]`
3. The program's own location, given `argv0`:
   1. `<argv0>.runfiles/MANIFEST`, if a file: manifest-based.
      `[adjacent_runfiles_dir_with_manifest]`
   2. `<argv0>.runfiles_manifest`, if a file: manifest-based.
      `[adjacent_runfiles_manifest]`
   3. `<argv0>.runfiles`, if a directory: directory-based.
      `[adjacent_runfiles_dir]`
4. Otherwise discovery fails. `[no_runfiles]`

Consequences:

- An empty variable is the same as an unset one.
  `[empty_manifest_env_falls_back_to_dir_env]`
  `[adjacent_runfiles_dir_with_empty_manifest_env]`
- `RUNFILES_MANIFEST_ONLY=1` with `RUNFILES_MANIFEST_FILE` selects the
  manifest; this is already implied by the order above. `[manifest_only_env]`
- Variables inherited from a parent process win over the program's own
  `.runfiles`. This is what lets a binary launched from another binary's
  `data` find the parent's runfiles tree.
  `[env_takes_precedence_over_adjacent_runfiles_dir]`

## Manifest format

One entry per line: an rlocationpath, one space, and the absolute path of the
file. The target is everything after the first space, so it may itself
contain spaces. `[manifest_target_path_with_spaces]`

A line starting with a space is escaped. In the key, space, newline, and
backslash are written `\s`, `\n`, and `\b`; in the target, newline and
backslash are written `\n` and `\b`. `[manifest_escaped_entry]`

An entry may name a directory. A path below it resolves to the corresponding
path below the target. `[manifest_directory_entry]`

Lines end with `\n` on every platform.

## Lookup

`rlocation(path)` resolves an rlocationpath to a filesystem path, or reports
that it cannot:

1. An empty path cannot be resolved.
2. An absolute path is returned unchanged. `[absolute_path_returned_unchanged]`
3. A path that starts with `./` or `../`, ends with `/.` or `/..`, or contains
   `/./`, `/../`, or `//` is rejected, even if it would resolve on disk.
   `[rejects_parent_directory_segments]` `[rejects_current_directory_segments]`
4. The repository mapping is applied (next section).
5. Directory-based: the result is `<directory>/<path>`, without checking that
   it exists. `[dir_env]` `[missing_runfile_dir_env]`
6. Manifest-based: the exact key, else the longest key that is a parent
   directory of the path, with the remainder appended; else unresolved.
   `[manifest_env]` `[missing_runfile_manifest_env]` `[manifest_directory_entry]`

## Repository mapping

With Bzlmod, code refers to repositories by *apparent* names while runfiles
are laid out by *canonical* names. The runfiles root may contain a
`_repo_mapping` file with lines of the form

```
<source canonical>,<apparent>,<target canonical>
```

When resolving `<apparent>/<rest>`, a library looks up
`(source repository, apparent)` and, if found, resolves
`<target canonical>/<rest>` instead. `[repo_mapping_dir_env]`
`[repo_mapping_manifest_env]` If there is no entry the path is used as given,
since it may already be canonical. The main repository's canonical name in
runfiles paths is `_main`. `[repo_mapping_main_repo_dir_env]`

The source repository for code in the main repository is the empty string.

## Not yet specified

These areas exist in some libraries and are not covered by scenarios. They are
candidates for future statements, not guarantees.

- The variables a library should set when launching a child process.
- The compact `_repo_mapping` format produced by
  `--incompatible_compact_repo_mapping_manifest`.
- Legacy variables (`TEST_SRCDIR`, `JAVA_RUNFILES`).
- Windows path and case handling.

## Conformance matrix

Results for the versions pinned in `MODULE.bazel`. An empty cell means the
library satisfies the scenario; otherwise it names the divergence listed
below. Maintained by hand from the compliance workflows.

| Scenario | C++ | Go | Java | Python | Rust | Shell |
|----------|-----|----|------|--------|------|-------|
| **Discovery** | | | | | | |
| `no_runfiles` | | | | | | |
| `runfiles_dir_env` | | | | | | |
| `runfiles_manifest_env` | | | J1 | | | |
| `manifest_env_takes_precedence_over_dir_env` | | | J1 | | | S2 |
| `manifest_only_env` | | | | | | S2 |
| `empty_manifest_env_falls_back_to_dir_env` | | | | | | |
| `adjacent_runfiles_dir` | | | J2 | P1 | | S1 |
| `adjacent_runfiles_dir_with_manifest` | | G1 | J2 | P1 | | |
| `adjacent_runfiles_manifest` | | | J2 | P1 | R1 | |
| `adjacent_runfiles_dir_with_empty_manifest_env` | | G1 | J2 | P1 | | |
| `env_takes_precedence_over_adjacent_runfiles_dir` | | | | | | |
| **Lookup** | | | | | | |
| `missing_runfile_dir_env` | | | | | | |
| `missing_runfile_manifest_env` | | | J1 | | | |
| `manifest_directory_entry` | | | J1 | | R2 | |
| `manifest_target_path_with_spaces` | | | J1 | | | |
| `manifest_escaped_entry` | | | J1 | | R3 | |
| `absolute_path_returned_unchanged` | | | | | | |
| `rejects_parent_directory_segments` | | | | | R4 | S3 |
| `rejects_current_directory_segments` | | | | | R4 | |
| **Repository mapping** | | | | | | |
| `repo_mapping_dir_env` | | | | | | |
| `repo_mapping_main_repo_dir_env` | | | | | | |
| `repo_mapping_manifest_env` | | | J1 | | | |

| Id | Library | Divergence |
|----|---------|------------|
| G1 | Go | Probes `<argv0>.runfiles_manifest` and `<argv0>.runfiles` but never `<argv0>.runfiles/MANIFEST`. |
| J1 | Java | Only reads `RUNFILES_MANIFEST_FILE` when `RUNFILES_MANIFEST_ONLY=1`; otherwise requires `RUNFILES_DIR` or `JAVA_RUNFILES`. |
| J2 | Java | No argv0 discovery. The `java_binary` launcher stub exports `RUNFILES_DIR` / `JAVA_RUNFILES` instead. |
| P1 | Python | No argv0 discovery. `Runfiles.Create()` returns `None` unless `RUNFILES_MANIFEST_FILE` or `RUNFILES_DIR` is set. |
| R1 | Rust | Probes `<argv0>.runfiles` (and `MANIFEST` inside it) but never `<argv0>.runfiles_manifest`. |
| R2 | Rust | Exact manifest lookups only; does not resolve paths below a directory entry. |
| R3 | Rust | Does not decode escaped manifest entries. |
| R4 | Rust | Does not reject non-normalized paths (`./`, `../`). |
| S1 | Shell | Only accepts an adjacent `.runfiles` directory if it contains `bazel_tools/tools/bash/runfiles/runfiles.bash`. |
| S2 | Shell | Prefers `RUNFILES_DIR` over `RUNFILES_MANIFEST_FILE` when both are set, and ignores `RUNFILES_MANIFEST_ONLY`. |
| S3 | Shell | Rejects `../` only at the start or end of a path, not between segments. |

J2 and P1 are deliberate: those rulesets put discovery in the launcher stub
rather than the library. They are listed because a binary copied out of
`bazel-bin` hits them all the same. On Bazel 7, `@rules_shell//shell/runfiles`
is an alias for `@bazel_tools//tools/bash/runfiles`, which shows the same
divergences.
