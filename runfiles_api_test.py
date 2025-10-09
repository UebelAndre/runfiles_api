"""Runfiles API test suite - runs against any binary.

This test suite validates that binaries correctly implement the runfiles API
by invoking them with different environment configurations and directory structures.

Binary Interface:
    All binaries must accept a single command-line argument: an rlocationpath
    (e.g., "workspace/path/to/file"). The binary resolves this path using the
    runfiles API and prints the file contents to stdout.

    Example:
        $ ./runfiles_user runfiles_api/test/data/sample.txt
        This is test data for runfiles API testing.
        ...
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


def minimal_runfiles(rlocationpath: str) -> Path:
    """Locate a runfile without using any runfiles API.

    This is a minimal implementation that directly checks environment variables
    and filesystem locations to find runfiles, used only for test setup.

    Args:
        rlocationpath: The runfiles path (e.g., "workspace/path/to/file")

    Returns:
        The absolute path to the runfile, or None if not found
    """
    # Try RUNFILES_DIR
    if runfiles_dir := os.environ.get("RUNFILES_DIR"):
        path = Path(runfiles_dir) / rlocationpath
        if path.exists():
            return path

    # Try TEST_SRCDIR
    if test_srcdir := os.environ.get("TEST_SRCDIR"):
        path = Path(test_srcdir) / rlocationpath
        if path.exists():
            return path

    # Try RUNFILES_MANIFEST_FILE
    if manifest_file := os.environ.get("RUNFILES_MANIFEST_FILE"):
        if Path(manifest_file).exists():
            with open(manifest_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    parts = line.split(" ", 1)
                    if len(parts) == 2 and parts[0] == rlocationpath:
                        return Path(parts[1])

    raise FileNotFoundError(f"Failed to locate runfile: {rlocationpath}")


@pytest.fixture(name="binary_under_test")
def binary_under_test_fixture(tmp_path: Path) -> Path:
    """Fixture that provides the path to the binary under test.

    Returns a copy of the binary in a unique temporary directory.
    """
    # Get the binary rlocation path from RUNFILES_USER environment variable
    runfiles_user = os.environ.get("RUNFILES_BINARY")
    if not runfiles_user:
        pytest.fail("RUNFILES_BINARY environment variable not set")

    # Use minimal_runfiles to locate the binary
    binary_path = minimal_runfiles(runfiles_user)
    if not binary_path:
        pytest.fail(f"Could not locate binary at: {runfiles_user}")

    # Create a copy of the binary in a unique temp directory
    binary_copy_dir = tmp_path / "binary"
    binary_copy_dir.mkdir(parents=True, exist_ok=True)
    binary_copy = binary_copy_dir / binary_path.name
    shutil.copy2(binary_path, binary_copy)
    binary_copy.chmod(0o755)

    return binary_copy


@pytest.fixture(name="runfiles_dir")
def runfiles_dir_fixture(tmp_path: Path) -> Path:
    """Produces a mock `RUNFILES_DIR` that points to generated runfiles."""
    # Create a runfiles directory structure
    runfiles_dir = tmp_path / "runfiles"
    runfiles_dir.mkdir(parents=True)

    # Create test data file in the runfiles directory
    test_file = runfiles_dir / "runfiles_api" / "test_data.txt"
    test_file.parent.mkdir(parents=True, exist_ok=True)
    test_file.write_text("Test data content", encoding="utf-8")

    return runfiles_dir


@pytest.fixture(name="runfiles_manifest")
def runfiles_manifest_fixture(tmp_path: Path) -> Path:
    """Produces a mock `RUNFILES_MANIFEST` that points to generated runfiles."""
    # Create actual files in a separate location
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True)

    test_file = data_dir / "test_data.txt"
    test_file.write_text("Test data content", encoding="utf-8")

    # Create manifest file that maps rlocationpaths to actual file paths
    manifest_file = tmp_path / "MANIFEST"
    manifest_content = f"runfiles_api/test_data.txt {test_file}\n"
    manifest_file.write_text(manifest_content, encoding="utf-8")

    return manifest_file


def binary_args(binary: Path) -> list[str]:
    """Produce arguments for a subprocess of a given binary."""

    if binary.name.endswith(".py"):
        return [sys.executable, "-B", "-s", "-P", str(binary)]

    if binary.name.endswith(".sh"):
        bash = shutil.which("bash")
        if not bash:
            bash = shutil.which("bash.exe")
        if not bash:
            bash = "/bin/bash"
        return [bash, str(binary)]

    return [str(binary)]


def test_no_runfiles(binary_under_test: Path) -> None:
    """Test that no files are found if no runfiles envs or paths are available."""
    # The binary should fail to locate runfiles
    result = subprocess.run(
        binary_args(binary_under_test) + ["runfiles_api/test_data.txt"],
        env={},
        stderr=subprocess.STDOUT,
        stdout=subprocess.PIPE,
        text=True,
        check=False,
    )

    # Expect non-zero exit code since runfiles cannot be found
    assert result.returncode != 0, "Binary should fail when no runfiles are available"


def test_runfiles_dir_env(binary_under_test: Path, runfiles_dir: Path) -> None:
    """Test that runfiles are able to locate using RUNFILES_DIR environment variable."""
    # Run the binary with the runfiles directory
    result = subprocess.run(
        binary_args(binary_under_test) + ["runfiles_api/test_data.txt"],
        env={"RUNFILES_DIR": str(runfiles_dir)},
        stderr=subprocess.STDOUT,
        stdout=subprocess.PIPE,
        text=True,
        check=False,
    )

    # Verify the binary successfully read the file
    assert result.returncode == 0, result.stdout
    assert (
        "Test data content" in result.stdout
    ), f"Expected content not found in output: {result.stdout}"


def test_runfiles_manifest_env(
    binary_under_test: Path, runfiles_manifest: Path
) -> None:
    """Test that runfiles are able to locate using RUNFILES_MANIFEST_FILE."""
    # Run the binary with the manifest file
    result = subprocess.run(
        binary_args(binary_under_test) + ["runfiles_api/test_data.txt"],
        env={"RUNFILES_MANIFEST_FILE": str(runfiles_manifest)},
        stderr=subprocess.STDOUT,
        stdout=subprocess.PIPE,
        text=True,
        check=False,
    )

    # Verify the binary successfully read the file
    assert result.returncode == 0, result.stdout
    assert (
        "Test data content" in result.stdout
    ), f"Expected content not found in output: {result.stdout}"


def test_runfiles_dir_no_manifest(binary_under_test: Path) -> None:
    """Test that a binary in isolation with a `{name}.runfiles` directory can be used for runfiles without a `MANIFEST` file."""
    # Create {binary_name}.runfiles directory adjacent to the binary
    binary_name = binary_under_test.name
    runfiles_subdir = binary_under_test.parent / f"{binary_name}.runfiles"
    runfiles_subdir.mkdir(parents=True)

    # Create test data in the runfiles directory
    test_file = runfiles_subdir / "runfiles_api" / "test_data.txt"
    test_file.parent.mkdir(parents=True, exist_ok=True)
    test_file.write_text("Test data content", encoding="utf-8")

    # Run binary with clean environment (no runfiles env vars)
    result = subprocess.run(
        binary_args(binary_under_test) + ["runfiles_api/test_data.txt"],
        env={},
        stderr=subprocess.STDOUT,
        stdout=subprocess.PIPE,
        text=True,
        check=False,
    )

    # Verify the binary successfully found and read the file
    assert result.returncode == 0, result.stdout
    assert (
        "Test data content" in result.stdout
    ), f"Expected content not found in output: {result.stdout}"


def test_runfiles_dir_with_manifest(binary_under_test: Path, tmp_path: Path) -> None:
    """Test that a binary in isolation with a `{name}.runfiles` directory can be used for runfiles with a `MANIFEST` file."""
    # Create {binary_name}.runfiles directory adjacent to the binary
    binary_name = binary_under_test.name
    runfiles_subdir = binary_under_test.parent / f"{binary_name}.runfiles"
    runfiles_subdir.mkdir(parents=True)

    # Create test data in a separate location
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True)
    test_file = data_dir / "test_data.txt"
    test_file.write_text("Test data content", encoding="utf-8")

    # Create MANIFEST file in the .runfiles directory
    manifest_file = runfiles_subdir / "MANIFEST"
    manifest_content = f"runfiles_api/test_data.txt {test_file}\n"
    manifest_file.write_text(manifest_content, encoding="utf-8")

    # Run binary with clean environment (no runfiles env vars)
    result = subprocess.run(
        binary_args(binary_under_test) + ["runfiles_api/test_data.txt"],
        env={},
        stderr=subprocess.STDOUT,
        stdout=subprocess.PIPE,
        text=True,
        check=False,
    )

    # Verify the binary successfully found and read the file
    assert result.returncode == 0, result.stdout
    assert (
        "Test data content" in result.stdout
    ), f"Expected content not found in output: {result.stdout}"


def test_runfiles_dir_empty_manifest_env(
    binary_under_test: Path, tmp_path: Path
) -> None:
    """Test that runfiles directories are used in cases where a manifest environment variable is defined but is empty"""
    # Create {binary_name}.runfiles directory adjacent to the binary
    binary_name = binary_under_test.name
    runfiles_subdir = binary_under_test.parent / f"{binary_name}.runfiles"
    runfiles_subdir.mkdir(parents=True)

    # Create test data in a separate location
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True)
    test_file = data_dir / "test_data.txt"
    test_file.write_text("Test data content", encoding="utf-8")

    # Create MANIFEST file in the .runfiles directory
    manifest_file = runfiles_subdir / "MANIFEST"
    manifest_content = f"runfiles_api/test_data.txt {test_file}\n"
    manifest_file.write_text(manifest_content, encoding="utf-8")

    # Run binary with clean environment (no runfiles env vars)
    result = subprocess.run(
        binary_args(binary_under_test) + ["runfiles_api/test_data.txt"],
        env={"RUNFILES_MANIFEST_FILE": ""},
        stderr=subprocess.STDOUT,
        stdout=subprocess.PIPE,
        text=True,
        check=False,
    )

    # Verify the binary successfully found and read the file
    assert result.returncode == 0, result.stdout
    assert (
        "Test data content" in result.stdout
    ), f"Expected content not found in output: {result.stdout}"
