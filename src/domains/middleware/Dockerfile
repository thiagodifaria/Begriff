# Estágio de build: um ambiente completo para compilar C++, COBOL e dependências
FROM debian:bullseye-slim AS builder
LABEL maintainer="Thiago <thiagodifaria@gmail.com>"

# Instalação de todas as dependências de compilação (C++, Boost, OpenSSL e para compilar COBOL)
RUN apt-get update && \
    apt-get install -y g++ cmake make git libboost-system-dev libssl-dev \
                       build-essential wget libdb-dev libgmp-dev libncurses-dev && \
    rm -rf /var/lib/apt/lists/*

# Baixar, compilar e instalar o GnuCOBOL do código-fonte para garantir a versão correta
RUN cd /tmp && \
    wget https://ftp.gnu.org/gnu/gnucobol/gnucobol-3.1.2.tar.xz && \
    tar -xf gnucobol-3.1.2.tar.xz && \
    cd gnucobol-3.1.2 && \
    ./configure --prefix=/usr/local && \
    make && \
    make install && \
    ldconfig

# Clonar e instalar a biblioteca Crow
RUN git clone https://github.com/CrowCpp/Crow.git /app/crow && \
    cd /app/crow && \
    git checkout v1.0

# Copiar todos os fontes necessários (C++, COBOL, CMake) para o ambiente de build
WORKDIR /app
COPY src/domains/middleware/reconciliation.cpp ./
COPY src/domains/middleware/crypto.cpp ./
COPY src/domains/middleware/CMakeLists.txt ./
COPY src/domains/transactions/engine/reconcile.cbl ./
COPY src/domains/transactions/copybooks/*.cpy ./

# Compilar o programa COBOL usando o compilador instalado a partir do fonte
# CORREÇÃO: Adicionada a flag -free para aceitar formato livre do COBOL
RUN LD_LIBRARY_PATH=/usr/local/lib cobc -x -free -o reconcile reconcile.cbl

# Criar um único diretório de build e compilar ambos os serviços C++
RUN mkdir -p build && \
    cd build && \
    cmake -DCMAKE_BUILD_TYPE=Release -DCMAKE_PREFIX_PATH=/app/crow .. && \
    make

# Estágio de execução final para o serviço de reconciliação
FROM debian:bullseye-slim AS reconciliation_runtime
LABEL maintainer="Thiago <email@example.com>"

# Instalação de dependências de execução (runtime) mínimas para C++ e COBOL
RUN apt-get update && \
    apt-get install -y libboost-system1.74.0 libssl1.1 libncurses6 && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copiar os executáveis compilados do estágio 'builder'
COPY --from=builder /app/build/reconciliation /app/reconciliation
COPY --from=builder /app/reconcile /app/reconcile

# Copiar as bibliotecas de runtime do COBOL compilado
COPY --from=builder /usr/local/lib/libcob.so* /usr/local/lib/
# CORREÇÃO: Copiar a biblioteca libncursesw.so.6 necessária para o COBOL
COPY --from=builder /lib/x86_64-linux-gnu/libncursesw.so.6 /usr/local/lib/
# Configurar o linker para encontrar as bibliotecas COBOL
RUN ldconfig

# Garantir permissões de execução
RUN chmod +x /app/reconciliation /app/reconcile

# Definir o comando de execução para o serviço C++
CMD ["/app/reconciliation"]

# Estágio de execução final para o serviço de criptografia
FROM debian:bullseye-slim AS crypto_runtime
LABEL maintainer="Thiago <email@example.com>"

# Instalação de dependências de execução para C++
RUN apt-get update && \
    apt-get install -y libboost-system1.74.0 libssl1.1 && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copiar o executável compilado do estágio 'builder'
COPY --from=builder /app/build/crypto /app/crypto

# Garantir permissões de execução
RUN chmod +x /app/crypto

# Definir o comando de execução
CMD ["/app/crypto"]