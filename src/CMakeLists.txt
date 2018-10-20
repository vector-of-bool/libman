add_library(
    libman
    lm/lm.hpp
    lm/lm.cpp
    )
add_library(lm::libman ALIAS libman)
target_include_directories(libman
    PUBLIC $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}>
    )

target_link_libraries(libman PUBLIC Boost::filesystem)
