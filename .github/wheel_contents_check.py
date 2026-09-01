"""Fail when a wheel holds a file outside the install-layout allowlist.

Usage: python wheel_contents_check.py <wheel> [<wheel> ...]"""

import fnmatch
import sys
import zipfile

# fnmatch's * crosses path separators, so one pattern covers a subtree.
ALLOWED = [
    "cppjit/*.py",
    "cppjit/libcppjit.so",
    "cppjit/interop/lib/libclangCppInterOp*",
    "cppjit/interop/lib/clang/*",
    "cppjit/interop/include/*",
    "cppjit-*.dist-info/*",
]


def check(path):
    # directory entries (trailing slash) carry no content
    members = [m for m in zipfile.ZipFile(path).namelist() if not m.endswith("/")]
    bad = [m for m in members if not any(fnmatch.fnmatch(m, p) for p in ALLOWED)]
    for member in bad:
        print(f"{path}: unexpected member {member}")
    return not bad


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    sys.exit(0 if all([check(path) for path in sys.argv[1:]]) else 1)
