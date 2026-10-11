"""Runfiles API conformance scenarios.

Every scenario launches the subject from a scratch directory with a controlled
environment and filesystem layout, then asserts on its exit code and output.
The subject contract is documented in `README.md`. The reference subject in
`test/reference/` is expected to pass every scenario; the per-language subjects
fail exactly where their library diverges from it.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from harness.layout import (
    make_manifest,
    make_runfiles_dir,
    manifest_path,
    write_manifest,
)
from harness.subject import (
    EXIT_NO_RUNFILES,
    EXIT_NOT_FOUND,
    EXIT_OK,
    Result,
    Subject,
    load_subject,
    run,
)

KEY = "runfiles_api/test_data.txt"
"""The rlocationpath used by most scenarios."""

CONTENT = "runfiles_api test data"
"""The content of the runfile used by most scenarios."""


@pytest.fixture(name="subject")
def subject_fixture(tmp_path: Path) -> Subject:
    """The subject under test, copied into this test's scratch directory."""
    return load_subject(tmp_path)


def assert_content(result: Result, content: str) -> None:
    """Assert that the subject succeeded and printed exactly `content`."""
    assert result.returncode == EXIT_OK, result
    assert result.stdout.strip() == content, result


def assert_failure(result: Result, returncode: int | None = None) -> None:
    """Assert that the subject failed without printing any runfile content."""
    if returncode is None:
        assert result.returncode != EXIT_OK, result
    else:
        assert result.returncode == returncode, result
    assert CONTENT not in result.stdout, result


def adjacent_runfiles_dir(subject: Subject) -> Path:
    """The `<binary>.runfiles` directory Bazel would create next to the subject."""
    return Path(f"{subject.path}.runfiles")


# ---------------------------------------------------------------------------
# Environment-based discovery
# ---------------------------------------------------------------------------


def test_no_runfiles(subject: Subject) -> None:
    """Without any discovery inputs the subject reports that runfiles are unavailable."""
    result = run(subject, [KEY])
    assert_failure(result, EXIT_NO_RUNFILES)


def test_runfiles_dir_env(subject: Subject, tmp_path: Path) -> None:
    """`RUNFILES_DIR` alone enables directory-based lookups."""
    runfiles_dir = make_runfiles_dir(tmp_path / "runfiles", {KEY: CONTENT})
    result = run(subject, [KEY], env={"RUNFILES_DIR": str(runfiles_dir)})
    assert_content(result, CONTENT)


def test_runfiles_manifest_env(subject: Subject, tmp_path: Path) -> None:
    """`RUNFILES_MANIFEST_FILE` alone enables manifest-based lookups."""
    manifest = make_manifest(tmp_path / "manifest", {KEY: CONTENT})
    result = run(subject, [KEY], env={"RUNFILES_MANIFEST_FILE": str(manifest)})
    assert_content(result, CONTENT)


def test_manifest_env_takes_precedence_over_dir_env(
    subject: Subject, tmp_path: Path
) -> None:
    """When both variables are set, the manifest is used."""
    runfiles_dir = make_runfiles_dir(tmp_path / "runfiles", {KEY: "from directory"})
    manifest = make_manifest(tmp_path / "manifest", {KEY: "from manifest"})
    result = run(
        subject,
        [KEY],
        env={
            "RUNFILES_DIR": str(runfiles_dir),
            "RUNFILES_MANIFEST_FILE": str(manifest),
        },
    )
    assert_content(result, "from manifest")


def test_manifest_only_env(subject: Subject, tmp_path: Path) -> None:
    """`RUNFILES_MANIFEST_ONLY=1` forces the manifest even when a directory is available."""
    runfiles_dir = make_runfiles_dir(tmp_path / "runfiles", {KEY: "from directory"})
    manifest = make_manifest(tmp_path / "manifest", {KEY: "from manifest"})
    result = run(
        subject,
        [KEY],
        env={
            "RUNFILES_DIR": str(runfiles_dir),
            "RUNFILES_MANIFEST_FILE": str(manifest),
            "RUNFILES_MANIFEST_ONLY": "1",
        },
    )
    assert_content(result, "from manifest")


def test_empty_manifest_env_falls_back_to_dir_env(
    subject: Subject, tmp_path: Path
) -> None:
    """An empty `RUNFILES_MANIFEST_FILE` is treated as unset."""
    runfiles_dir = make_runfiles_dir(tmp_path / "runfiles", {KEY: CONTENT})
    result = run(
        subject,
        [KEY],
        env={"RUNFILES_DIR": str(runfiles_dir), "RUNFILES_MANIFEST_FILE": ""},
    )
    assert_content(result, CONTENT)


# ---------------------------------------------------------------------------
# argv0-based discovery
# ---------------------------------------------------------------------------


def test_adjacent_runfiles_dir(subject: Subject) -> None:
    """A `<binary>.runfiles` directory is discovered without any environment variables."""
    make_runfiles_dir(adjacent_runfiles_dir(subject), {KEY: CONTENT})
    result = run(subject, [KEY])
    assert_content(result, CONTENT)


def test_adjacent_runfiles_dir_with_manifest(subject: Subject, tmp_path: Path) -> None:
    """A `<binary>.runfiles/MANIFEST` file is discovered without any environment variables."""
    make_manifest(
        tmp_path / "data",
        {KEY: CONTENT},
        manifest=adjacent_runfiles_dir(subject) / "MANIFEST",
    )
    result = run(subject, [KEY])
    assert_content(result, CONTENT)


def test_adjacent_runfiles_manifest(subject: Subject, tmp_path: Path) -> None:
    """A `<binary>.runfiles_manifest` file is discovered without any environment variables.

    This is the layout Bazel produces on Windows when runfiles trees are disabled.
    """
    make_manifest(
        tmp_path / "data",
        {KEY: CONTENT},
        manifest=Path(f"{subject.path}.runfiles_manifest"),
    )
    result = run(subject, [KEY])
    assert_content(result, CONTENT)


def test_adjacent_runfiles_dir_with_empty_manifest_env(
    subject: Subject, tmp_path: Path
) -> None:
    """An empty `RUNFILES_MANIFEST_FILE` does not disable argv0 discovery."""
    make_manifest(
        tmp_path / "data",
        {KEY: CONTENT},
        manifest=adjacent_runfiles_dir(subject) / "MANIFEST",
    )
    result = run(subject, [KEY], env={"RUNFILES_MANIFEST_FILE": ""})
    assert_content(result, CONTENT)


def test_env_takes_precedence_over_adjacent_runfiles_dir(
    subject: Subject, tmp_path: Path
) -> None:
    """Variables inherited from a parent process win over the subject's own runfiles.

    This is what makes `data` dependencies on other binaries work.
    """
    make_runfiles_dir(adjacent_runfiles_dir(subject), {KEY: "from adjacent"})
    runfiles_dir = make_runfiles_dir(tmp_path / "runfiles", {KEY: "from env"})
    result = run(subject, [KEY], env={"RUNFILES_DIR": str(runfiles_dir)})
    assert_content(result, "from env")


# ---------------------------------------------------------------------------
# Lookup semantics
# ---------------------------------------------------------------------------


def test_missing_runfile_dir_env(subject: Subject, tmp_path: Path) -> None:
    """Looking up an unknown path in a directory reports that the runfile is missing."""
    runfiles_dir = make_runfiles_dir(tmp_path / "runfiles", {KEY: CONTENT})
    result = run(
        subject, ["runfiles_api/missing.txt"], env={"RUNFILES_DIR": str(runfiles_dir)}
    )
    assert_failure(result, EXIT_NOT_FOUND)


def test_missing_runfile_manifest_env(subject: Subject, tmp_path: Path) -> None:
    """Looking up an unknown key in a manifest reports that the runfile is missing."""
    manifest = make_manifest(tmp_path / "manifest", {KEY: CONTENT})
    result = run(
        subject,
        ["runfiles_api/missing.txt"],
        env={"RUNFILES_MANIFEST_FILE": str(manifest)},
    )
    assert_failure(result, EXIT_NOT_FOUND)


def test_manifest_directory_entry(subject: Subject, tmp_path: Path) -> None:
    """A path below a directory entry in the manifest resolves through that entry."""
    data_dir = make_runfiles_dir(tmp_path / "data", {"nested/test_data.txt": CONTENT})
    manifest = write_manifest(tmp_path / "MANIFEST", {"runfiles_api/data": data_dir})
    result = run(
        subject,
        ["runfiles_api/data/nested/test_data.txt"],
        env={"RUNFILES_MANIFEST_FILE": str(manifest)},
    )
    assert_content(result, CONTENT)


def test_manifest_target_path_with_spaces(subject: Subject, tmp_path: Path) -> None:
    """A manifest entry whose target path contains spaces (legacy format)."""
    data_dir = make_runfiles_dir(
        tmp_path / "dir with spaces", {"test data.txt": CONTENT}
    )
    manifest = write_manifest(tmp_path / "MANIFEST", {KEY: data_dir / "test data.txt"})
    result = run(subject, [KEY], env={"RUNFILES_MANIFEST_FILE": str(manifest)})
    assert_content(result, CONTENT)


def test_manifest_escaped_entry(subject: Subject, tmp_path: Path) -> None:
    """A manifest entry using Bazel's escaped format.

    Lines whose key or target contains a space, newline, or backslash start
    with a space. In the key, those characters are escaped as `\\s`, `\\n`,
    and `\\b`; in the target only newlines and backslashes are escaped.
    """
    key = "runfiles_api/test data.txt"
    data_dir = make_runfiles_dir(
        tmp_path / "dir with spaces", {"test data.txt": CONTENT}
    )
    manifest = tmp_path / "MANIFEST"
    manifest.write_text(
        f" {key.replace(' ', chr(92) + 's')} "
        f"{manifest_path(data_dir / 'test data.txt')}\n",
        encoding="utf-8",
        newline="\n",
    )
    result = run(subject, [key], env={"RUNFILES_MANIFEST_FILE": str(manifest)})
    assert_content(result, CONTENT)


def test_absolute_path_returned_unchanged(subject: Subject, tmp_path: Path) -> None:
    """An absolute path is returned as-is without consulting the runfiles."""
    runfiles_dir = make_runfiles_dir(tmp_path / "runfiles", {})
    absolute = tmp_path / "absolute.txt"
    absolute.write_text(CONTENT, encoding="utf-8")
    result = run(subject, [str(absolute)], env={"RUNFILES_DIR": str(runfiles_dir)})
    assert_content(result, CONTENT)


def test_rejects_parent_directory_segments(subject: Subject, tmp_path: Path) -> None:
    """Paths containing `..` are rejected even if they would resolve on disk."""
    runfiles_dir = make_runfiles_dir(tmp_path / "runfiles", {KEY: CONTENT})
    (runfiles_dir / "runfiles_api" / "sub").mkdir()
    result = run(
        subject,
        ["runfiles_api/sub/../test_data.txt"],
        env={"RUNFILES_DIR": str(runfiles_dir)},
    )
    assert_failure(result)


def test_rejects_current_directory_segments(subject: Subject, tmp_path: Path) -> None:
    """Paths containing `./` segments are rejected even if they would resolve on disk."""
    runfiles_dir = make_runfiles_dir(tmp_path / "runfiles", {KEY: CONTENT})
    result = run(
        subject,
        ["runfiles_api/./test_data.txt"],
        env={"RUNFILES_DIR": str(runfiles_dir)},
    )
    assert_failure(result)


# ---------------------------------------------------------------------------
# Repository mapping
# ---------------------------------------------------------------------------

REPO_MAPPING = ",other_repo,other_repo+\n,runfiles_api,_main\n"
"""A `_repo_mapping` for a main repository depending on `other_repo`."""


def test_repo_mapping_dir_env(subject: Subject, tmp_path: Path) -> None:
    """An apparent repository name is mapped to its canonical directory."""
    runfiles_dir = make_runfiles_dir(
        tmp_path / "runfiles",
        {
            "_repo_mapping": REPO_MAPPING,
            "other_repo+/test_data.txt": CONTENT,
        },
    )
    result = run(
        subject, ["other_repo/test_data.txt"], env={"RUNFILES_DIR": str(runfiles_dir)}
    )
    assert_content(result, CONTENT)


def test_repo_mapping_main_repo_dir_env(subject: Subject, tmp_path: Path) -> None:
    """The main repository's apparent name is mapped to `_main`."""
    runfiles_dir = make_runfiles_dir(
        tmp_path / "runfiles",
        {
            "_repo_mapping": REPO_MAPPING,
            "_main/test_data.txt": CONTENT,
        },
    )
    result = run(subject, [KEY], env={"RUNFILES_DIR": str(runfiles_dir)})
    assert_content(result, CONTENT)


def test_repo_mapping_manifest_env(subject: Subject, tmp_path: Path) -> None:
    """Repository mapping is applied to manifest-based lookups."""
    manifest = make_manifest(
        tmp_path / "manifest",
        {
            "_repo_mapping": REPO_MAPPING,
            "other_repo+/test_data.txt": CONTENT,
        },
    )
    result = run(
        subject,
        ["other_repo/test_data.txt"],
        env={"RUNFILES_MANIFEST_FILE": str(manifest)},
    )
    assert_content(result, CONTENT)
