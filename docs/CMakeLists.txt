find_program(SPHINX_BUILD_EXECUTABLE sphinx-build DOC "Path to sphinx-build, for documentation")

if(NOT SPHINX_BUILD_EXECUTABLE)
    message(STATUS "No sphinx-build, so we will not generate the documentation")
    return()
endif()

get_filename_component(doc_build_dir "${CMAKE_CURRENT_BINARY_DIR}/html" ABSOLUTE)

file(GLOB_RECURSE doc_files CONFIGURE_DEPENDS "*")
add_custom_command(
    OUTPUT "${doc_build_dir}/index.html"
    DEPENDS ${doc_files}
    COMMAND "${SPHINX_BUILD_EXECUTABLE}"
        -b html
        -q
        -j6
        -W
        "${CMAKE_CURRENT_SOURCE_DIR}"
        "${doc_build_dir}"
    COMMENT "Generating documentation"
    )
add_custom_target(lm-docs ALL DEPENDS "${doc_build_dir}/index.html")
