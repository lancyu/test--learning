cmake_minimum_required(VERSION 3.14)
project(cpp_tests)

set(CMAKE_CXX_STANDARD 17)

find_package(GTest REQUIRED)

enable_testing()

add_executable(test_radar_parser
    test_radar_parser.cpp
    radar_parser.cpp
)
target_link_libraries(test_radar_parser GTest::gtest_main)
add_test(NAME test_radar_parser COMMAND test_radar_parser)