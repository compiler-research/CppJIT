cmake_minimum_required(VERSION 3.16)
project(CppJIT LANGUAGES C CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

include(ExternalProject)
include(GNUInstallDirs)

# This option won't make a lot of sense since we only ship the shared library in site-packages
# Perhaps this should permanently be OFF and users can build their own CppInterOp if they want to run the tests?
option(CPPJIT_ENABLE_CPPINTEROP_TESTS "enable CppInterOp tests" OFF)
set(CPPINTEROP_GIT_REPOSITORY "https://github.com/compiler-research/CppInterOp.git" CACHE STRING "")
set(CPPINTEROP_GIT_TAG "3103be92baa66a5e78e3a7c6207d83d4623ca956" CACHE STRING "")

set(Python_FIND_VIRTUALENV ONLY)
find_package(Python COMPONENTS Interpreter Development)
if(NOT Python_FOUND)
    set(Python_FIND_VIRTUALENV STANDARD)
    find_package(Python COMPONENTS Interpreter Development)
endif()
if(NOT Python_Development_FOUND)
    message(FATAL_ERROR "Python development headers not found")
endif()

set(_llvm_hints "")

if(DEFINED ENV{CONDA_PREFIX})
    list(APPEND _llvm_hints "$ENV{CONDA_PREFIX}/lib/cmake/llvm")
    list(APPEND _llvm_hints "$ENV{CONDA_PREFIX}/lib/cmake/clang")
endif()

if(NOT DEFINED LLVM_DIR)
    find_package(LLVM CONFIG QUIET HINTS ${_llvm_hints})
    if(NOT LLVM_FOUND)
        message(FATAL_ERROR
            "llvm-config not found, please install LLVM 21 (llvmdev, clangdev) using your system package manager or conda.\n"
            "As an alternative, you can pass -DLLVM_DIR=/path/to/llvm/lib/cmake/llvm to pip\n"
            "(pip: --config-settings=cmake.define.LLVM_DIR=...)")
    endif()
else()
    find_package(LLVM REQUIRED CONFIG HINTS "${LLVM_DIR}")
endif()

# somewhat derive Clang_DIR
if(NOT DEFINED Clang_DIR)
    get_filename_component(_llvm_cmake_dir "${LLVM_DIR}" DIRECTORY)
    if(EXISTS "${_llvm_cmake_dir}/clang/ClangConfig.cmake")
        set(Clang_DIR "${_llvm_cmake_dir}/clang")
    elseif(EXISTS "${LLVM_DIR}/../clang/ClangConfig.cmake")
        set(Clang_DIR "${LLVM_DIR}/../clang")
    endif()
endif()
if(DEFINED Clang_DIR)
    find_package(Clang CONFIG HINTS "${Clang_DIR}")
endif()

message(STATUS "Found LLVM ${LLVM_VERSION} at ${LLVM_DIR}")
if(LLVM_VERSION VERSION_LESS "20.0")
    message(WARNING "LLVM ${LLVM_VERSION} detected. Minimum supported version is 21. Build may fail.")
endif()
if(Clang_FOUND)
    message(STATUS "Found Clang at ${Clang_DIR}")
endif()

# build CppInterOp, we should expose the option to use pre-installed CppInterOp for example using conda

# CPPINTEROP_DIR should resolve to the final installed location at runtime.
# ask for site-packages path; fall back to CMAKE_INSTALL_PREFIX for standalone builds.
execute_process(
    COMMAND ${Python_EXECUTABLE} -c "import sysconfig; print(sysconfig.get_path('platlib'))"
    OUTPUT_VARIABLE _python_platlib
    OUTPUT_STRIP_TRAILING_WHITESPACE
)
if(_python_platlib)
    set(CPPINTEROP_INSTALL_DIR "${_python_platlib}/cppjit/cppyy_backend")
else()
    set(CPPINTEROP_INSTALL_DIR "${CMAKE_INSTALL_PREFIX}/cppjit/cppyy_backend")
endif()

# Include cmake for CppInterOp config and build using ExternalProject.
include(${CMAKE_CURRENT_SOURCE_DIR}/cmake/AddCppInterOp.cmake)
cppjit_add_cppinterop()

# this libcppyy.so merges both CPyCppyy and clingwrapper
file(GLOB CPYCPPYY_SOURCES CONFIGURE_DEPENDS src/CPyCppyy/*.cxx)
set(BACKEND_SOURCES
    src/backend/clingwrapper.cxx
    src/backend/cppinterop_dispatch.cxx
)

add_library(cppyy SHARED ${CPYCPPYY_SOURCES} ${BACKEND_SOURCES})
add_dependencies(cppyy CppInterOp)


target_compile_definitions(cppyy PRIVATE
    CPPINTEROP_DIR="${CPPINTEROP_INSTALL_DIR}"
    CMAKE_SHARED_LIBRARY_SUFFIX="${CMAKE_SHARED_LIBRARY_SUFFIX}"
)

target_include_directories(cppyy PRIVATE
    # src/ itself resolves the public "CPyCppyy/*.h" spellings against the
    # flattened src/CPyCppyy/ directory
    ${CMAKE_CURRENT_SOURCE_DIR}/src
    ${CMAKE_CURRENT_SOURCE_DIR}/src/CPyCppyy
    ${CMAKE_CURRENT_SOURCE_DIR}/src/backend
    ${CPPINTEROP_INSTALL_DIR}/include
    ${Python_INCLUDE_DIRS}
)

target_compile_options(cppyy PRIVATE
    -Wall -Wno-strict-aliasing -Wno-register
)

if(CMAKE_COMPILER_IS_GNUCXX)
    target_link_options(cppyy PRIVATE -Wl,-Bsymbolic-functions)
endif()

# macOS needs to allow undefined Python symbols
if(APPLE)
    set_target_properties(cppyy PROPERTIES
        LINK_FLAGS "-undefined dynamic_lookup"
        SUFFIX ".so"
    )
endif()

set_target_properties(cppyy PROPERTIES
    OUTPUT_NAME "cppyy"
    PREFIX "lib"
)

# libcppyy.so is installed in cppjit/ root (import cppjit.libcppyy)
install(TARGETS cppyy
    LIBRARY DESTINATION cppjit
)

# install CppInterOp libraries and headers
install(CODE "
    file(GLOB _interop_libs \"${CPPINTEROP_INSTALL_DIR}/lib/libclangCppInterOp*\")
    foreach(_lib \${_interop_libs})
        file(INSTALL \${_lib} DESTINATION \${CMAKE_INSTALL_PREFIX}/cppjit/cppyy_backend/lib)
    endforeach()
")

install(CODE "
    file(INSTALL \"${CPPINTEROP_INSTALL_DIR}/include/\" DESTINATION \${CMAKE_INSTALL_PREFIX}/cppjit/cppyy_backend/include)
")

# the public CPyCppyy API headers keep their installed CPyCppyy/ prefix
install(FILES
    src/CPyCppyy/API.h
    src/CPyCppyy/CommonDefs.h
    src/CPyCppyy/DispatchPtr.h
    src/CPyCppyy/PyException.h
    src/CPyCppyy/Reflex.h
    DESTINATION cppjit/cppyy_backend/include/CPyCppyy
)
