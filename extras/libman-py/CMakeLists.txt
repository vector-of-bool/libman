option(BUILD_LIBMAN_PY "Build the Python components" ON)
if(NOT BUILD_LIBMAN_PY)
    return()
endif()

option(DEFINE_LIBMAN_PY_TESTS "Defined the libman-py tests" ON)

find_program(TOX_EXECUTABLE tox DOC "Path to tox, for running Python tests")

find_package(Python3 COMPONENTS Interpreter)
find_program(WHEEL_EXECUTABLE wheel)

if(NOT TARGET Python3::Interpreter)
    message(SEND_ERROR "No Python, so libman-py cannot be built")
    return()
endif()

get_target_property(py Python3::Interpreter LOCATION)
execute_process(
    COMMAND "${py}" -m wheel --help
    OUTPUT_VARIABLE out
    ERROR_VARIABLE out
    RESULT_VARIABLE rc
    )
if(rc)
    message(SEND_ERROR "The chosen Python (${py}) does not have the 'wheel' module installed, but it is required")
    return()
endif()

file(GLOB_RECURSE sources
    CONFIGURE_DEPENDS
    FOLLOW_SYMLINKS false
    "libman/*.py"
    setup.py
    Pipfile
    Pipfile.lock
    mypy.ini
    .pylintrc
    tox.ini
    )

get_filename_component(wheel_stamp "${CMAKE_CURRENT_BINARY_DIR}/libman-wheel.stamp" ABSOLUTE)

add_custom_command(
    OUTPUT "${wheel_stamp}"
    DEPENDS ${sources}
    COMMAND Python3::Interpreter setup.py -q bdist_wheel
    COMMAND ${CMAKE_COMMAND} -E touch ${wheel_stamp}
    WORKING_DIRECTORY "${CMAKE_CURRENT_LIST_DIR}"
    COMMENT "Generating libman-py wheel"
    )

add_custom_target(libman-wheel ALL DEPENDS "${wheel_stamp}")

if(NOT DEFINE_LIBMAN_PY_TESTS)
    return()
endif()

if(NOT TOX_EXECUTABLE)
    message(SEND_ERROR "No `tox` installed, so we can't run the tests.")
else()
    add_test(
        NAME py.tox.libman-py
        COMMAND "${TOX_EXECUTABLE}"
        WORKING_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}"
        )
endif()
