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
set(CPPINTEROP_GIT_TAG "8d624c621a4b95e36ff73ac708c85a768287478f" CACHE STRING "")

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
    set(CPPINTEROP_INSTALL_DIR "${_python_platlib}/cppjit_backend")
else()
    set(CPPINTEROP_INSTALL_DIR "${CMAKE_INSTALL_PREFIX}/cppjit_backend")
endif()

# Include cmake for CppInterOp config and build using ExternalProject.
include(${CMAKE_CURRENT_SOURCE_DIR}/cmake/AddCppInterOp.cmake)
cppjit_add_cppinterop()

# this libcppjit.so merges both cpyrt and the interop wrapper
file(GLOB CPYRT_SOURCES CONFIGURE_DEPENDS src/cpyrt/*.cxx)
set(INTEROP_SOURCES
    src/interop/interop_wrapper.cxx
    src/interop/cppinterop_dispatch.cxx
)

add_library(cppjit SHARED ${CPYRT_SOURCES} ${INTEROP_SOURCES})
add_dependencies(cppjit CppInterOp)


target_compile_definitions(cppjit PRIVATE
    CPPINTEROP_DIR="${CPPINTEROP_INSTALL_DIR}"
    CMAKE_SHARED_LIBRARY_SUFFIX="${CMAKE_SHARED_LIBRARY_SUFFIX}"
)

target_include_directories(cppjit PRIVATE
    # src/ itself resolves the public "cpyrt/*.h" spellings against the
    # flattened src/cpyrt/ directory
    ${CMAKE_CURRENT_SOURCE_DIR}/src
    ${CMAKE_CURRENT_SOURCE_DIR}/src/cpyrt
    ${CMAKE_CURRENT_SOURCE_DIR}/src/interop
    ${CPPINTEROP_INSTALL_DIR}/include
    ${Python_INCLUDE_DIRS}
)

target_compile_options(cppjit PRIVATE
    -Wall -Wno-strict-aliasing -Wno-register
)

if(CMAKE_COMPILER_IS_GNUCXX)
    target_link_options(cppjit PRIVATE -Wl,-Bsymbolic-functions)
endif()

# macOS needs to allow undefined Python symbols
if(APPLE)
    set_target_properties(cppjit PROPERTIES
        LINK_FLAGS "-undefined dynamic_lookup"
        SUFFIX ".so"
    )
endif()

set_target_properties(cppjit PROPERTIES
    OUTPUT_NAME "cppjit"
    PREFIX "lib"
)

# libcppjit.so is installed at the site-packages root (import libcppjit)
install(TARGETS cppjit
    LIBRARY DESTINATION .
)

# install CppInterOp libraries and headers
install(CODE "
    file(GLOB _interop_libs \"${CPPINTEROP_INSTALL_DIR}/lib/libclangCppInterOp*\")
    foreach(_lib \${_interop_libs})
        file(INSTALL \${_lib} DESTINATION \${CMAKE_INSTALL_PREFIX}/cppjit_backend/lib)
    endforeach()
")

install(CODE "
    file(INSTALL \"${CPPINTEROP_INSTALL_DIR}/include/\" DESTINATION \${CMAKE_INSTALL_PREFIX}/cppjit_backend/include)
")

# the public cpyrt API headers keep their installed cpyrt/ prefix
install(FILES
    src/cpyrt/API.h
    src/cpyrt/CommonDefs.h
    src/cpyrt/DispatchPtr.h
    src/cpyrt/PyException.h
    src/cpyrt/Reflex.h
    DESTINATION cppjit_backend/include/cpyrt
)
