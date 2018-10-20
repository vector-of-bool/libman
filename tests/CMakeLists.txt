include(Catch)

add_library(lm-tests-base STATIC test-main.cpp)
target_link_libraries(lm-tests-base PUBLIC Catch2::Catch2)
