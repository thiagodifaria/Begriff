# Stage 1: Base Image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Set the python path to include the app directory
ENV PYTHONPATH "${PYTHONPATH}:/app"

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY ./src /app/src

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application with Uvicorn
# The command from docker-compose.yml will override this, but this is a good default.
CMD ["uvicorn", "src.app.main:app", "--host", "0.0.0.0", "--port", "8000"]