file(REMOVE_RECURSE "${TEST_BIN_DIR}")
execute_process(
    COMMAND "${CMAKE_COMMAND}"
        -G "${GENERATOR}"
        -D LIBMAN_INCLUDE=${LIBMAN_SRC}/cmake/libman.cmake
        -D CMAKE_BUILD_TYPE=${CONFIG}
        -S "${TEST_SRC_DIR}"
        -B "${TEST_BIN_DIR}"
    RESULT_VARIABLE retc
    )

if(retc)
    message(FATAL_ERROR "Configure failed [${retc}]")
endif()

execute_process(
    COMMAND "${CMAKE_COMMAND}"
        --build ${TEST_BIN_DIR}
        --config ${CONFIG}
    RESULT_VARIABLE retc
    )

if(retc)
    message(FATAL_ERROR "Build failed [${retc}]")
endif()
