# Document Ingestion Service Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for PDF processing
RUN apt-get update && apt-get install -y \
    libpoppler-cpp-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY services/document-ingestion/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy service code
COPY services/document-ingestion/src/ ./src/

# Copy shared libraries
COPY shared /app/shared

# Set Python path
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8002

# Run service
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8002"]

