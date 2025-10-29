FROM python:3.11-slim

WORKDIR /app

# Copy requirements
COPY workers/reward-computation-worker/requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared libraries
COPY shared /app/shared

# Copy worker code
COPY workers/reward-computation-worker/src /app/src

# Run worker
CMD ["python", "-m", "src.worker"]

