"""Suite-wide pytest infrastructure.

Tests within a file share interpreter state (cppdefs, loaded dictionaries,
pythonizations), so distributed runs must keep whole files on one worker.
"""


def pytest_configure(config):
    # -n implies --dist load; any granularity finer than per-file splits
    # same-file tests across interpreters. Remap every sub-file mode to
    # loadfile ("each" and "no" are whole-file-safe already).
    if config.getoption("numprocesses", None) and config.getoption("dist", "no") in (
        "load",
        "worksteal",
        "loadscope",
        "loadgroup",
    ):
        config.option.dist = "loadfile"
