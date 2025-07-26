# Stage 1: COBOL Builder - Compiling GnuCOBOL from source for maximum compatibility
FROM debian:bullseye-slim AS cobol-builder

# Install build dependencies required to compile GnuCOBOL
RUN apt-get update && \
    apt-get install -y \
    build-essential \
    wget \
    libdb-dev \
    libgmp-dev \
    libncurses-dev && \
    rm -rf /var/lib/apt/lists/*

# Download, configure, and compile GnuCOBOL
WORKDIR /tmp
RUN wget https://ftp.gnu.org/gnu/gnucobol/gnucobol-3.1.2.tar.xz && \
    tar -xf gnucobol-3.1.2.tar.xz

WORKDIR /tmp/gnucobol-3.1.2
RUN ./configure --prefix=/usr/local && \
    make && \
    make install

# Configure the library path and update the dynamic linker cache
RUN echo "/usr/local/lib" > /etc/ld.so.conf.d/gnucobol.conf && \
    ldconfig

# Set environment variables for GnuCOBOL
ENV LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH
ENV COB_CONFIG_DIR=/usr/local/share/gnucobol/config
ENV COB_COPY_DIR=/usr/local/share/gnucobol/copy

# Now, compile our application's COBOL code
WORKDIR /app
COPY src/domains/transactions/engine/ .
COPY src/domains/transactions/copybooks/ .

# Compile COBOL with the proper library path
RUN LD_LIBRARY_PATH=/usr/local/lib cobc -x -o transaction_processor transaction_processor.cbl


# Stage 2: C++ Builder
FROM debian:bullseye-slim AS cpp-builder

# Install dependencies, including Boost and build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    g++ \
    cmake \
    make \
    git \
    libboost-system-dev \
    libboost-thread-dev \
    libboost-filesystem-dev \
    libboost-date-time-dev \
    libboost-atomic-dev && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy C++ source code
COPY src/infra/gateways/performance_gateway/ .

# Download and build Crow dependency
RUN git config --global http.sslVerify false && git clone https://github.com/CrowCpp/Crow.git && \
    cd Crow && git checkout v1.0 && cd ..

# Configure and build the project
RUN cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DCMAKE_PREFIX_PATH=/app/Crow
RUN cmake --build build -j$(nproc)


# Stage 3: Final Production Image
FROM debian:bullseye-slim

RUN apt-get update && apt-get install -y libboost-system1.74.0 libboost-thread1.74.0 libboost-filesystem1.74.0 libboost-date-time1.74.0 libboost-atomic1.74.0 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install runtime dependencies for GnuCOBOL
RUN apt-get update && \
    apt-get install -y \
    libdb5.3 \
    libgmp10 \
    libncurses6 && \
    rm -rf /var/lib/apt/lists/*

# Copy the compiled C++ gateway from the cpp-builder stage
COPY --from=cpp-builder /app/build/performance_gateway .

# Copy the compiled COBOL executable from the cobol-builder stage
COPY --from=cobol-builder /app/transaction_processor .

# Copy GnuCOBOL runtime libraries from the builder stage
COPY --from=cobol-builder /usr/local/lib/libcob.so* /usr/local/lib/
COPY --from=cobol-builder /usr/local/share/gnucobol /usr/local/share/gnucobol

# Configure library path for runtime
RUN echo "/usr/local/lib" > /etc/ld.so.conf.d/gnucobol.conf && \
    ldconfig

# Set environment variables for GnuCOBOL runtime
ENV LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH
ENV COB_CONFIG_DIR=/usr/local/share/gnucobol/config
ENV COB_COPY_DIR=/usr/local/share/gnucobol/copy

# Ensure the executables have the correct permissions
RUN chmod +x ./performance_gateway ./transaction_processor

# Expose the port the service runs on
EXPOSE 8081

# Set the command to execute the gateway application
CMD ["./performance_gateway"]