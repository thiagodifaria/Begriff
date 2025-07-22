cmake_minimum_required(VERSION 3.10)
project(performance_gateway)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

add_executable(performance_gateway src/gateway.cpp)

# Assuming Crow is available to be linked
# In a real scenario, you might use find_package(Crow) or add_subdirectory(path/to/crow)
target_link_libraries(performance_gateway PRIVATE crow)
