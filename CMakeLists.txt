cmake_minimum_required(VERSION 3.16)
project(CppJIT LANGUAGES C CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

include(ExternalProject)
include(GNUInstallDirs)

# This option won't make a lot of sense since we only ship the shared library in site-packages
# Perhaps this should permanently be OFF and users can build their own CppInterOp if they want to run the tests?
option(CPPJIT_ENABLE_CPPINTEROP_TESTS "enable CppInterOp tests" OFF)
set(CPPINTEROP_GIT_TAG "main" CACHE STRING "")

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

set(_interop_cmake_args
    -DLLVM_DIR=${LLVM_DIR}
    -DCPPINTEROP_USE_REPL=ON
    -DCPPINTEROP_USE_CLING=OFF
    -DCPPINTEROP_ENABLE_TESTING=${CPPJIT_ENABLE_CPPINTEROP_TESTS}
    -DBUILD_SHARED_LIBS=ON
    -DCMAKE_INSTALL_PREFIX=${CPPINTEROP_INSTALL_DIR}
    -DCMAKE_INSTALL_LIBDIR=lib
    -DCMAKE_BUILD_TYPE=${CMAKE_BUILD_TYPE}
    -DCMAKE_CXX_STANDARD=17
)
if(Clang_DIR)
    list(APPEND _interop_cmake_args -DClang_DIR=${Clang_DIR})
endif()
if(CMAKE_C_COMPILER)
    list(APPEND _interop_cmake_args -DCMAKE_C_COMPILER=${CMAKE_C_COMPILER})
endif()
if(CMAKE_CXX_COMPILER)
    list(APPEND _interop_cmake_args -DCMAKE_CXX_COMPILER=${CMAKE_CXX_COMPILER})
endif()

ExternalProject_Add(CppInterOp
    GIT_REPOSITORY https://github.com/compiler-research/CppInterOp.git
    GIT_TAG        ${CPPINTEROP_GIT_TAG}
    GIT_SHALLOW    ON
    PREFIX         "${CMAKE_BINARY_DIR}/CppInterOp"
    CMAKE_ARGS     ${_interop_cmake_args}
    BUILD_BYPRODUCTS
        "${CPPINTEROP_INSTALL_DIR}/lib/libclangCppInterOp${CMAKE_SHARED_LIBRARY_SUFFIX}"
    LOG_DOWNLOAD   ON
    LOG_CONFIGURE  ON
    LOG_BUILD      ON
    LOG_INSTALL    ON
    LOG_OUTPUT_ON_FAILURE ON
)

# this libcppyy.so merges both CPyCppyy and clingwrapper
file(GLOB CPYCPPYY_SOURCES CONFIGURE_DEPENDS src/CPyCppyy/src/*.cxx)
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
    ${CMAKE_CURRENT_SOURCE_DIR}/src/CPyCppyy/include
    ${CMAKE_CURRENT_SOURCE_DIR}/src/CPyCppyy/src
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

install(DIRECTORY src/CPyCppyy/include/CPyCppyy
    DESTINATION cppjit/cppyy_backend/include
)
