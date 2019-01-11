cmake_minimum_required(VERSION 3.13)
project(TestProject)

include(${LIBMAN_INCLUDE})

add_library(some-library
    src/simple.cpp
    src/simple.hpp
    )

export_package(
    ADD_TO_ALL
    TARGETS some-library
    HEADER_ROOTS src
    )
