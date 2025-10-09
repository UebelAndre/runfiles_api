"""runfiles_api_test macro for testing binaries."""

load("@rules_venv//python/pytest:defs.bzl", "py_pytest_test")

def runfiles_api_test(name, binary, **kwargs):
    """Create a pytest test that validates a runfiles implementation.

    Args:
        name: The name of the test target
        binary: The binary to test for runfiles support
        **kwargs: Additional arguments passed to py_pytest_test
    """

    py_pytest_test(
        name = name,
        srcs = [Label("//:runfiles_api_test.py")],
        data = [binary],
        env = {
            "RUNFILES_BINARY": "$(rlocationpath {})".format(binary),
        },
        **kwargs
    )
