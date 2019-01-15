cmake_minimum_required(VERSION 3.10)

list(INSERT CMAKE_MODULE_PATH 0 "${CMAKE_CURRENT_SOURCE_DIR}/cmake")

project(libman
    VERSION 0.0.1
    DESCRIPTION "A portable way to represent libraries in a dependency tree"
    )

include(libman)

# Global options

# Randomly pick between using vcpkg or Conan, to ensure that we are always able
# to build with either
include(pmm.cmake)
string(RANDOM LENGTH 1 ALPHABET 01 use_vcpkg)
if((use_vcpkg OR LIBMAN_USE_VCPKG) AND NOT CONAN_EXPORTED)
    pmm(VCPKG
        REVISION 43deeaf0c8b6086310ee753be2e93c941f7ffd75
        REQUIRES catch2
        )
else()
    pmm(CONAN)
    conan_set_find_paths()
endif()

# We also want the community modules
pmm(CMakeCM ROLLING)

find_package(Catch2 REQUIRED)

option(BUILD_SPEC "Build the specification document" ON)
if(BUILD_SPEC)
    find_package(Bikeshed)
endif()
add_subdirectory(data)


add_subdirectory(src)

option(BUILD_TESTING "Build tests" ON)
if(BUILD_TESTING AND (PROJECT_SOURCE_DIR STREQUAL CMAKE_SOURCE_DIR))
    enable_testing()
    add_subdirectory(tests)
endif()

add_subdirectory(extras)

option(BUILD_DOCS "Build the documentation" ON)
if(BUILD_DOCS)
    add_subdirectory(docs)
endif()

export_package(NAMESPACE libman)
export_library(libman HEADER_ROOTS src)
