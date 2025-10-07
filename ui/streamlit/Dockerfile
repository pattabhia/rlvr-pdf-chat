FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY ui/streamlit/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY ui/streamlit/src/ ./src/

# Set Python path
ENV PYTHONPATH=/app/src

# Expose port
EXPOSE 8501

# Run Streamlit
CMD ["streamlit", "run", "src/app_simple.py", "--server.port=8501", "--server.address=0.0.0.0"]

