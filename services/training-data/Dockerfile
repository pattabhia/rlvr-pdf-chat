# Training Data Service Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install Python dependencies
COPY services/training-data/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy service code
COPY services/training-data/src/ ./src/

# Set Python path
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8005

# Run service
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8005"]

