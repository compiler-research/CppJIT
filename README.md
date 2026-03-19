# CppJIT

CppJIT is the consolidated monorepo packaging of the compiler-research forks of the [cppyy](https://github.com/wlav/cppyy) package, a Python-C++ interoperability package based on LLVM, with [CppInterOp](https://github.com/compiler-research/CppInterOp) as the
interpreter backend and Compiler-as-a-Service facilities. Star us and stay tuned for pip releases this summer.

## Build requirements

- LLVM/Clang 19–21 (21 recommended)
- Python 3.8+ with development headers
- CMake 3.16+

## Installation

### Option 1: System LLVM

If LLVM is installed system-wide (e.g. `apt install llvm-21-dev clang-21`):

```bash
pip install .
```

### Option 2: Conda LLVM

```bash
conda install -c conda-forge llvmdev clangdev
pip install .
```

### Option 3: Custom LLVM build

```bash
pip install . --config-settings=cmake.define.LLVM_DIR=/path/to/llvm/lib/cmake/llvm
```

### Direct CMake build (development)

```bash
mkdir build && cd build
cmake .. -DLLVM_DIR=/path/to/llvm/lib/cmake/llvm -DCMAKE_BUILD_TYPE=Debug
cmake --build . -j$(nproc)
cmake --install . --prefix /path/to/install
```
