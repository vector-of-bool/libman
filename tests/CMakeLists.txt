include(Catch)

add_library(lm-tests-base STATIC test-main.cpp)
target_link_libraries(lm-tests-base PUBLIC Catch2::Catch2)

set(test_dirs
    just-include
    import-empty
    import-simple
    export-simple
    )

foreach(test_dir IN LISTS test_dirs)
    get_filename_component(test_dir_abs "${test_dir}" ABSOLUTE)
    set(test_dir_bin "${CMAKE_CURRENT_BINARY_DIR}/build-${test_dir}")
    add_test(
        NAME "libman.project.${test_dir}"
        COMMAND "${CMAKE_COMMAND}"
            -D LIBMAN_SRC=${PROJECT_SOURCE_DIR}
            -D LIBMAN_BIN=${PROJECT_BINARY_DIR}
            -D TEST_SRC_DIR=${test_dir_abs}
            -D TEST_BIN_DIR=${test_dir_bin}
            -D GENERATOR=${CMAKE_GENERATOR}
            -D CONFIG=$<CONFIG>
            -P "${CMAKE_CURRENT_SOURCE_DIR}/RunProjectTest.cmake"
        )
endforeach()

add_test(
    NAME libman.export-then-import
    COMMAND "${CMAKE_COMMAND}"
        -D LIBMAN_SRC=${PROJECT_SOURCE_DIR}
        -D LIBMAN_BIN=${PROJECT_BINARY_DIR}
        -D GENERATOR=${CMAKE_GENERATOR}
        -D CONFIG=$<CONFIG>
        -P "${CMAKE_CURRENT_SOURCE_DIR}/import-export/RunTest.cmake"
    )
