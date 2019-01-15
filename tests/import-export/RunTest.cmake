set(BINDIR_BASE "${LIBMAN_BIN}/test-import-export")

function(build_project name dir)
    get_filename_component(dir "${CMAKE_CURRENT_LIST_DIR}/${dir}" ABSOLUTE)
    get_filename_component(bindir "${BINDIR_BASE}/${name}/build" ABSOLUTE)
    file(REMOVE_RECURSE "${bindir}")
    execute_process(
        COMMAND "${CMAKE_COMMAND}"
            -G "${GENERATOR}"
            -D LIBMAN_INCLUDE=${LIBMAN_SRC}/cmake/libman.cmake
            -D CMAKE_BUILD_TYPE=${CONFIG}
            ${ARGN}
            -S "${dir}"
            -B "${bindir}"
        RESULT_VARIABLE retc
        )

    if(retc)
        message(FATAL_ERROR "Configure failed [${retc}]")
    endif()

    execute_process(
        COMMAND "${CMAKE_COMMAND}"
            --build ${bindir}
            --config ${CONFIG}
        RESULT_VARIABLE retc
        )

    if(retc)
        message(FATAL_ERROR "Build failed [${retc}]")
    endif()
endfunction()

build_project(say-hello-library library)

string(CONFIGURE [[
Type: Index

Package: HelloLibrary; @BINDIR_BASE@/say-hello-library/build/HelloLibrary.libman-export/HelloLibrary.lmp
]] lmi @ONLY)

set(gen_index "${BINDIR_BASE}/test-index.lmi")
file(WRITE "${gen_index}" "${lmi}")

build_project(say-hello-app app -D LIBMAN_INDEX=${gen_index})
