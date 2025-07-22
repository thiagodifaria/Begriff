# Stage 1: COBOL Builder
FROM dockercobol/gnucobol-alpine:latest AS cobol-builder

WORKDIR /app

# Copy the COBOL source file and its copybooks
# Note: Adjust the source path if your project structure is different
COPY ../../../domains/transactions/engine/transaction_processor.cbl .
COPY ../../../domains/transactions/copybooks/transaction_record.cpy .

# Compile the COBOL program into an executable
RUN cobc -x -o transaction_processor transaction_processor.cbl


# Stage 2: C++ Builder
FROM gcc:latest AS cpp-builder

# Install dependencies
RUN apt-get update && apt-get install -y cmake make git

# Set working directory
WORKDIR /app

# Copy C++ source code
COPY . .

# Download and build Crow dependency
RUN git clone https://github.com/CrowCpp/Crow.git && \
    cd Crow && git checkout v1.0 && cd ..

# Configure and build the project
RUN cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DCMAKE_PREFIX_PATH=/app/Crow
RUN cmake --build build -j$(nproc)


# Stage 3: Final Production Image
FROM debian:bullseye-slim

WORKDIR /app

# Copy the compiled C++ gateway from the cpp-builder stage
COPY --from=cpp-builder /app/build/performance_gateway .

# Copy the compiled COBOL executable from the cobol-builder stage
COPY --from=cobol-builder /app/transaction_processor .

# Ensure the executables have the correct permissions
RUN chmod +x ./performance_gateway ./transaction_processor

# Expose the port the service runs on
EXPOSE 8081

# Set the command to execute the gateway application
CMD ["./performance_gateway"]

