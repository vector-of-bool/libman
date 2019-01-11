cmake_minimum_required(VERSION 3.13)
project(HelloLibrary)

include(${LIBMAN_INCLUDE})

add_library(say-hello)
file(GLOB_RECURSE sources src/*)
target_sources(say-hello PRIVATE ${sources})
set_property(TARGET say-hello PROPERTY LIBMAN_NAME hello)

export_package(
    ADD_TO_ALL
    NAMESPACE say
    TARGETS say-hello
    HEADER_ROOTS src
    )
