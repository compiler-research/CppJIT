# Runs between the CppInterOp ExternalProject's configure and build steps:
# the sub-configure records its project() name in CMakeCache.txt; reject any
# source tree that does not declare itself CppInterOp.
file(STRINGS "${CPPINTEROP_BINARY_DIR}/CMakeCache.txt" _project_entry
     REGEX "^CMAKE_PROJECT_NAME:STATIC=")
if(NOT _project_entry)
    message(FATAL_ERROR
        "No CMAKE_PROJECT_NAME recorded in ${CPPINTEROP_BINARY_DIR}/CMakeCache.txt "
        "— the CppInterOp sub-configure did not complete")
endif()
string(REGEX REPLACE "^CMAKE_PROJECT_NAME:STATIC=" "" _project_name "${_project_entry}")
if(NOT _project_name STREQUAL "CppInterOp")
    message(FATAL_ERROR
        "The provided source path override declares project '${_project_name}', "
        "not CppInterOp")
endif()
