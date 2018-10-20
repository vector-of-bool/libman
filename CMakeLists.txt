cmake_minimum_required(VERSION 3.10)

list(INSERT CMAKE_MODULE_PATH 0 "${CMAKE_CURRENT_SOURCE_DIR}/cmake")

project(libman
    VERSION 0.0.1
    DESCRIPTION "A portable way to represent libraries in a dependency tree"
    )

# Randomly pick between using vcpkg or Conan, to ensure that we are always able
# to build with either
include(pmm.cmake)
string(RANDOM LENGTH 1 ALPHABET 01 use_vcpkg)
if(use_vcpkg OR LIBMAN_USE_VCPKG)
    pmm(VCPKG
        REVISION 43deeaf0c8b6086310ee753be2e93c941f7ffd75
        REQUIRES boost-filesystem catch2
        )
else()
    pmm(CONAN)
    conan_set_find_paths()
endif()

find_package(Boost 1.68 REQUIRED filesystem)
find_package(Catch2 REQUIRED)

add_subdirectory(src)

option(BUILD_TESTING "Build tests" ON)
if(BUILD_TESTING AND (PROJECT_SOURCE_DIR STREQUAL CMAKE_SOURCE_DIR))
    enable_testing()
    add_subdirectory(tests)
endif()

add_subdirectory(extras)

add_subdirectory(docs)
