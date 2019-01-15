cmake_minimum_required(VERSION 3.13)
project(ImportSimple)

include(${LIBMAN_INCLUDE})
import_packages(SimplePackage)

add_executable(test-exe main.cpp)

target_link_libraries(test-exe PRIVATE SuperSimple::Meow)
