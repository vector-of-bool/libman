cmake_minimum_required(VERSION 3.13)
project(SimpleApplication)

include(${LIBMAN_INCLUDE})
import_packages(HelloLibrary)

add_executable(say-hello main.cpp)
target_link_libraries(say-hello PRIVATE say::hello)
