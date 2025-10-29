FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY services/ground-truth/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared libraries
COPY shared /app/shared

# Copy application code
COPY services/ground-truth/src /app/src

# Expose port
EXPOSE 8007

# Run application
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8007"]

