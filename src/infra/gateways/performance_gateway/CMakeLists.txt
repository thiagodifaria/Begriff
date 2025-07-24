cmake_minimum_required(VERSION 3.10)
project(performance_gateway)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(Crow REQUIRED)

add_executable(performance_gateway src/gateway.cpp)

target_include_directories(performance_gateway PRIVATE include)

target_link_libraries(performance_gateway PRIVATE Crow::Crow asio::asio)
