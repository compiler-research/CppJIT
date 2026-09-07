# cppjit 0.1.0a1 Release Notes

This document contains the release notes for cppjit 0.1.0a1, an
automatic Python-C++ interoperability layer and bindings generator
built on [CppInterOp](https://github.com/compiler-research/CppInterOp)
and the [LLVM](https://llvm.org) compiler infrastructure.

This release supports Python 3.12-3.14 and LLVM 21-22.

## Highlights

- cppjit 0.1.0a1 is the first prerelease of cppjit, the successor of
  [cppyy](https://github.com/wlav/cppyy) rebuilt on CppInterOp and the
  clang-repl C++ interpreter in LLVM.
- The release installs from PyPI with `pip install cppjit` and ships
  wheels for Linux x86_64/aarch64 and macOS arm64/x86_64 on Python
  3.12-3.14, built with the LLVM 21 toolchain.
- This first prerelease establishes the build system, test, and
  packaging infrastructure of the new monorepo, with planned
  improvements, documentation, and benchmarks in the next beta
  release.

## Changes from cppyy

The user-facing Python layer is mostly unchanged from cppyy: `cppdef`,
`include`, `gbl`, and the pythonization machinery work as before. The
changes are in the compiler layer underneath:

- New backend:
  [CppInterOp](https://github.com/compiler-research/CppInterOp) and
  the clang-repl incremental compiler replace Cling and its patched
  LLVM. clang-repl is the upstreamed evolution of Cling, so cppjit
  builds against stock LLVM releases with no custom patches.
- Compiler-derived bindings: string-based type lookups give way to
  opaque handles on the Clang AST, and type conversion and overload
  resolution follow Clang's own rules.
- One package: the cppyy, CPyCppyy, and cppyy-backend distribution
  stack is consolidated into a single package and repository, built
  with scikit-build-core and published to PyPI through trusted
  publishing.
- Supported platforms: CPython 3.12-3.14 on Linux x86_64/aarch64 and
  macOS arm64/x86_64. cppyy's PyPy support is not carried over.
  Windows is not supported with this release but is a planned future
  development
  ([#89](https://github.com/compiler-research/cppjit/issues/89)).

## Contributors

Special thanks to everyone who contributed to this release:

- Aaron Jomy
- Emery Conrad
- Grigori Rybkine
- Jonas Rembser
- Kerem Şahin
- Vassil Vassilev
- Vipul Cariappa
- Wim Lavrijsen

And all past contributors to the now-archived compiler-research
forks of cppyy, CPyCppyy and cppyy-backend.
