# CppJIT

CppJIT is the consolidated monorepo packaging of the compiler-research forks of the [cppyy](https://github.com/wlav/cppyy) package, a Python-C++ interoperability package based on LLVM, leveraging [CppInterOp](https://github.com/compiler-research/CppInterOp) for the Clang-REPL interpreter backend and Compiler-as-a-Service facilities. Star us and stay tuned for pip releases coming summer 2026.

## Build requirements

- LLVM/Clang 21
    -  Installed system-wide (e.g. `apt install llvm-21-dev clang-21`)
    -  Installed via your favourite package manager (e.g. `conda install -c conda-forge "llvmdev=21" "clangdev=21"`)
    -  To use a source build of LLVM, pass the path to pip like `pip install . --config-settings=cmake.define.LLVM_DIR=/path/to/build/lib/cmake/llvm`
- Python 3.12+ with development headers (e.g. `apt install python3.14 python3.14-dev`)
- CMake 3.16+

### Standard installation:

Run `pip install .`

### Development build with CMake:

```bash
mkdir build && cd build
cmake .. -DLLVM_DIR=/path/to/llvm/lib/cmake/llvm -DCMAKE_BUILD_TYPE=Debug
cmake --build . -j$(nproc)
cmake --install . --prefix /path/to/install
```

To currently set up a source build, please look at the instructions at https://github.com/compiler-research/CppInterOp
