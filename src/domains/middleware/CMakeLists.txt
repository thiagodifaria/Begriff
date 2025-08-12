# Versão mínima do CMake
cmake_minimum_required(VERSION 3.10)

# Nome do projeto
project(MiddlewareServices CXX)

# Define o padrão C++ para C++17
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Forçar o uso dos módulos FindBoost.cmake do CMake
set(Boost_NO_BOOST_CMAKE ON)

# Encontra as bibliotecas necessárias
find_package(Boost REQUIRED COMPONENTS system)
find_package(OpenSSL REQUIRED)
# CORREÇÃO: Adiciona a busca pela biblioteca Threads (pthread)
find_package(Threads REQUIRED)

# Adiciona os diretórios de include para bibliotecas do sistema
include_directories(${Boost_INCLUDE_DIRS})

# Define o executável para o serviço de reconciliação
add_executable(reconciliation reconciliation.cpp)

# Define o executável para o serviço de criptografia
add_executable(crypto crypto.cpp)

# Vincula as bibliotecas e diretórios de include para CADA executável
target_include_directories(reconciliation PRIVATE /app/crow/include)
# CORREÇÃO: Adiciona a biblioteca Threads::Threads à lista de bibliotecas vinculadas
target_link_libraries(reconciliation PRIVATE Boost::system Threads::Threads)

target_include_directories(crypto PRIVATE /app/crow/include)
# CORREÇÃO: Adiciona a biblioteca Threads::Threads à lista de bibliotecas vinculadas
target_link_libraries(crypto PRIVATE Boost::system OpenSSL::SSL OpenSSL::Crypto Threads::Threads)