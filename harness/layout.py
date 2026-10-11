"""Helpers for building mock runfiles layouts."""

from __future__ import annotations

from pathlib import Path
from typing import Mapping


def make_runfiles_dir(root: Path, files: Mapping[str, str]) -> Path:
    """Create a directory-based runfiles tree.

    Args:
        root: The runfiles root to create.
        files: A mapping of rlocationpath to file content.

    Returns:
        `root`.
    """
    root.mkdir(parents=True, exist_ok=True)
    for rlocationpath, content in files.items():
        path = root / rlocationpath
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8", newline="\n")
    return root


def manifest_path(path: Path) -> str:
    """Render a path the way Bazel writes it into a runfiles manifest."""
    return path.as_posix()


def write_manifest(manifest: Path, entries: Mapping[str, Path]) -> Path:
    """Write a runfiles manifest.

    Args:
        manifest: The manifest file to write.
        entries: A mapping of rlocationpath to the real path of the runfile.

    Returns:
        `manifest`.
    """
    manifest.parent.mkdir(parents=True, exist_ok=True)
    # Bazel writes manifests with `\n` on every platform; `newline` stops Python
    # from translating to CRLF on Windows, which the libraries do not expect.
    manifest.write_text(
        "".join(f"{key} {manifest_path(path)}\n" for key, path in entries.items()),
        encoding="utf-8",
        newline="\n",
    )
    return manifest


def make_manifest(
    root: Path, files: Mapping[str, str], manifest: Path | None = None
) -> Path:
    """Create files under `root` and a manifest pointing at them.

    Args:
        root: A directory to hold the real files.
        files: A mapping of rlocationpath to file content.
        manifest: Where to write the manifest. Defaults to `root / "MANIFEST"`.

    Returns:
        The path to the manifest.
    """
    files_dir = make_runfiles_dir(root / "files", files)
    entries = {key: files_dir / key for key in files}
    return write_manifest(manifest or root / "MANIFEST", entries)
