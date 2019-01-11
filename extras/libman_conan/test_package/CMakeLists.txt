cmake_minimum_required(VERSION 3.10)
project(LibManTest)

include(${CMAKE_BINARY_DIR}/conan-libman.cmake)
import_packages(spdlog)

add_library(something something.cpp)

# Link the imported dependency. This require fmt::fmt, but libman should have
# created that transitive usage and the compile will succeed
target_link_libraries(something PUBLIC spdlog::spdlog)

export_package(
    REQUIRES meow
    HEADER_ROOTS src
    TARGETS something
    )
