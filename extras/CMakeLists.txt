option(BUILD_PYTHON_LIB "Build the python library" ON)
if(BUILD_PYTHON_LIB)
    add_subdirectory(libman-py)
endif()
