# Configures the CppInterOp ExternalProject. Default backend is clang-repl;
# CPPJIT_USE_CLING builds CppInterOp against a provided cling build
include_guard(GLOBAL)
include(ExternalProject)

# Developer toggle: Cling from either ROOT or standalone supplies LLVM_DIR/Clang_DIR
option(CPPJIT_USE_CLING "Build CppInterOp against a prebuilt Cling C++ Interpreter (ROOT)" OFF)
mark_as_advanced(CPPJIT_USE_CLING)

set(Cling_DIR "" CACHE PATH "Cling CMake config dir; derived from LLVM_DIR when empty (cling mode only)")
# Surface Cling_DIR in ccmake/GUI only when cling mode is on.
if(CPPJIT_USE_CLING)
    mark_as_advanced(CLEAR Cling_DIR)
else()
    mark_as_advanced(Cling_DIR)
endif()

function(cppjit_add_cppinterop)
    set(_args
        -DLLVM_DIR=${LLVM_DIR}
        -DCPPINTEROP_ENABLE_TESTING=${CPPJIT_ENABLE_CPPINTEROP_TESTS}
        -DBUILD_SHARED_LIBS=ON
        -DCMAKE_INSTALL_PREFIX=${CPPINTEROP_INSTALL_DIR}
        -DCMAKE_INSTALL_LIBDIR=lib
        -DCMAKE_BUILD_TYPE=${CMAKE_BUILD_TYPE}
        -DCMAKE_CXX_STANDARD=17
    )

    if(CPPJIT_USE_CLING)
        set(_cling_dir "${Cling_DIR}")
        if(NOT _cling_dir)
            # LLVM_DIR is <prefix>/lib/cmake/llvm; cling config sits at the
            # sibling <prefix>/lib/cmake/cling (setup-llvm flavor:cling layout).
            get_filename_component(_prefix "${LLVM_DIR}" DIRECTORY)   # <prefix>/lib/cmake
            get_filename_component(_prefix "${_prefix}" DIRECTORY)    # <prefix>/lib
            get_filename_component(_prefix "${_prefix}" DIRECTORY)    # <prefix>
            set(_cling_dir "${_prefix}/lib/cmake/cling")
        endif()
        message(STATUS "CppInterOp backend: Cling (found at ${_cling_dir})")
        list(APPEND _args
            -DCPPINTEROP_USE_CLING=ON
            -DCPPINTEROP_USE_REPL=OFF
            -DCling_DIR=${_cling_dir}
        )
    else()
        list(APPEND _args
            -DCPPINTEROP_USE_REPL=ON
            -DCPPINTEROP_USE_CLING=OFF
        )
    endif()

    if(Clang_DIR)
        list(APPEND _args -DClang_DIR=${Clang_DIR})
    endif()
    if(CMAKE_C_COMPILER)
        list(APPEND _args -DCMAKE_C_COMPILER=${CMAKE_C_COMPILER})
    endif()
    if(CMAKE_CXX_COMPILER)
        list(APPEND _args -DCMAKE_CXX_COMPILER=${CMAKE_CXX_COMPILER})
    endif()

    ExternalProject_Add(CppInterOp
        GIT_REPOSITORY https://github.com/compiler-research/CppInterOp.git
        GIT_TAG        ${CPPINTEROP_GIT_TAG}
        PREFIX         "${CMAKE_BINARY_DIR}/CppInterOp"
        CMAKE_ARGS     ${_args}
        BUILD_BYPRODUCTS
            "${CPPINTEROP_INSTALL_DIR}/lib/libclangCppInterOp${CMAKE_SHARED_LIBRARY_SUFFIX}"
        LOG_DOWNLOAD   ON
        LOG_CONFIGURE  ON
        LOG_BUILD      ON
        LOG_INSTALL    ON
        LOG_OUTPUT_ON_FAILURE ON
    )
endfunction()
