cmake_minimum_required(VERSION 3.16)
project(performance_gateway)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Encontra a biblioteca Boost e seus componentes
find_package(Boost REQUIRED COMPONENTS system thread filesystem)

# Configurações específicas para o Crow
set(CROW_BUILD_EXAMPLES OFF CACHE BOOL "Build Crow examples")
set(CROW_BUILD_TESTS OFF CACHE BOOL "Build Crow tests")

# Adiciona o código-fonte do Crow como um subdiretório
add_subdirectory(Crow)

# Define nosso executável principal
add_executable(performance_gateway src/gateway.cpp)

# Adiciona os diretórios de include
target_include_directories(performance_gateway PRIVATE
    "${CMAKE_CURRENT_SOURCE_DIR}/include"
    "${CMAKE_CURRENT_SOURCE_DIR}/Crow/include"
)

# Linka as bibliotecas
target_link_libraries(performance_gateway PRIVATE
    Crow::Crow
    Boost::system
    Boost::thread
    Boost::filesystem
    pthread
)