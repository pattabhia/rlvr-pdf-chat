FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY services/api-gateway/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY services/api-gateway/src/ ./src/

# Set Python path
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8000

# Run the service
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]

