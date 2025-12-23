#!/bin/bash

echo "🚀 Launching all RLVR services for native RunPod deployment..."
echo ""

# Kill any conflicting services from RunPod base image
echo "🛑 Stopping conflicting services..."
pkill nginx || true
pkill -f uvicorn || true
pkill -f streamlit || true
pkill -f "python -m src.worker" || true
pkill -f qdrant || true
sleep 2

# Set environment variables for native deployment (localhost instead of Docker service names)
echo "⚙️  Setting environment variables..."
export PYTHONPATH=/workspace/rlvr-pdf-chat
export RABBITMQ_URL=amqp://rlvr:rlvr_password@localhost:5672/
export OLLAMA_HOST=http://localhost:11434
export OLLAMA_URL=http://localhost:11434
export OLLAMA_MODEL=llama3.2:3b
export QDRANT_URL=http://localhost:6333
export QDRANT_HOST=localhost
export QDRANT_PORT=6333
export MIN_SCORE_DIFF=0.3
export MIN_CHOSEN_SCORE=0.7
export ENABLE_QUALITY_FILTER=true
export TIMEOUT_MINUTES=30
export TRAINING_DATA_DIR=/workspace/rlvr-pdf-chat/data/training_data
export DPO_DATA_DIR=/workspace/rlvr-pdf-chat/data/dpo_data

# API Gateway service URLs (localhost for native deployment)
export QA_ORCHESTRATOR_URL=http://localhost:8001
export DOC_INGESTION_SERVICE_URL=http://localhost:8002
export TRAINING_DATA_SERVICE_URL=http://localhost:8005
export GROUND_TRUTH_SERVICE_URL=http://localhost:8007

cd /workspace/rlvr-pdf-chat

# Install Qdrant if not present
if ! command -v qdrant &> /dev/null; then
    echo "📦 Installing Qdrant binary..."
    cd /tmp
    wget -q https://github.com/qdrant/qdrant/releases/download/v1.7.4/qdrant-x86_64-unknown-linux-gnu.tar.gz
    tar -xzf qdrant-x86_64-unknown-linux-gnu.tar.gz
    mv qdrant /usr/local/bin/
    chmod +x /usr/local/bin/qdrant
    rm qdrant-x86_64-unknown-linux-gnu.tar.gz
    cd /workspace/rlvr-pdf-chat
    echo "✅ Qdrant installed"
else
    echo "✅ Qdrant already installed"
fi

# Start Qdrant (vector database)
echo "🗄️  Starting Qdrant..."
mkdir -p /workspace/qdrant_storage
cd /workspace/qdrant_storage
nohup /usr/local/bin/qdrant > /tmp/qdrant.log 2>&1 &
echo "   Qdrant PID: $!"
cd /workspace/rlvr-pdf-chat
sleep 5

# Install/upgrade all service dependencies to override RunPod base image packages
echo "📦 Installing service dependencies..."
pip install --upgrade -q -r services/qa-orchestrator/requirements.txt
pip install --upgrade -q -r services/api-gateway/requirements.txt
pip install --upgrade -q -r services/document-ingestion/requirements.txt
pip install --upgrade -q -r ui/streamlit/requirements.txt
pip install --upgrade -q -r workers/verification-worker/requirements.txt
pip install --upgrade -q -r workers/dataset-generation-worker/requirements.txt
echo "✅ Dependencies installed"
echo ""

# Start Document Ingestion Service
echo "📄 Starting Document Ingestion Service..."
cd /workspace/rlvr-pdf-chat/services/document-ingestion
PYTHONPATH=/workspace/rlvr-pdf-chat/services/document-ingestion:/workspace/rlvr-pdf-chat nohup uvicorn src.main:app --host 0.0.0.0 --port 8002 > /tmp/document-ingestion.log 2>&1 &
echo "   Document Ingestion PID: $!"
sleep 3

# Start QA Orchestrator (with correct environment variables for native deployment)
echo "🤖 Starting QA Orchestrator..."
cd /workspace/rlvr-pdf-chat/services/qa-orchestrator
PYTHONPATH=/workspace/rlvr-pdf-chat/services/qa-orchestrator:/workspace/rlvr-pdf-chat nohup uvicorn src.main:app --host 0.0.0.0 --port 8001 > /tmp/qa-orchestrator.log 2>&1 &
echo "   QA Orchestrator PID: $!"
sleep 3

# Start Verification Worker (with correct module path)
echo "✅ Starting Verification Worker..."
cd /workspace/rlvr-pdf-chat/workers/verification-worker
PYTHONPATH=/workspace/rlvr-pdf-chat/workers/verification-worker:/workspace/rlvr-pdf-chat nohup python -m src.worker > /tmp/verification-worker.log 2>&1 &
echo "   Verification Worker PID: $!"
sleep 2

# Start Dataset Generation Worker (with correct module path and data directories)
echo "📊 Starting Dataset Generation Worker..."
cd /workspace/rlvr-pdf-chat/workers/dataset-generation-worker
PYTHONPATH=/workspace/rlvr-pdf-chat/workers/dataset-generation-worker:/workspace/rlvr-pdf-chat nohup python -m src.worker > /tmp/dataset-worker.log 2>&1 &
echo "   Dataset Worker PID: $!"
sleep 2

# Start API Gateway
echo "🌐 Starting API Gateway..."
cd /workspace/rlvr-pdf-chat/services/api-gateway
PYTHONPATH=/workspace/rlvr-pdf-chat/services/api-gateway:/workspace/rlvr-pdf-chat nohup uvicorn src.main:app --host 0.0.0.0 --port 8000 > /tmp/api-gateway.log 2>&1 &
echo "   API Gateway PID: $!"
sleep 3

# Start Streamlit UI
echo "🎨 Starting Streamlit UI..."
cd /workspace/rlvr-pdf-chat/ui/streamlit
PYTHONPATH=/workspace/rlvr-pdf-chat/ui/streamlit:/workspace/rlvr-pdf-chat nohup streamlit run src/app_simple.py > /tmp/streamlit.log 2>&1 &
echo "   Streamlit UI PID: $!"

echo ""
echo "⏳ Waiting for services to initialize..."
sleep 10

echo ""
echo "=========================================="
echo "✅ All services started!"
echo "=========================================="
echo ""
echo "🏥 Running health checks..."
sleep 5

# Health checks with better error handling
echo ""
echo "Service Status:"
curl -sf http://localhost:6333/collections > /dev/null 2>&1 && echo "  ✅ Qdrant (Vector DB)" || echo "  ❌ Qdrant - Check /tmp/qdrant.log"
curl -sf http://localhost:11434/api/tags > /dev/null 2>&1 && echo "  ✅ Ollama (LLM)" || echo "  ❌ Ollama - Check if Ollama is running"
curl -sf http://localhost:8002/health > /dev/null 2>&1 && echo "  ✅ Document Ingestion" || echo "  ❌ Document Ingestion - Check /tmp/document-ingestion.log"
curl -sf http://localhost:8001/health > /dev/null 2>&1 && echo "  ✅ QA Orchestrator" || echo "  ❌ QA Orchestrator - Check /tmp/qa-orchestrator.log"
curl -sf http://localhost:8000/health > /dev/null 2>&1 && echo "  ✅ API Gateway" || echo "  ❌ API Gateway - Check /tmp/api-gateway.log"
curl -sf http://localhost:8501 > /dev/null 2>&1 && echo "  ✅ Streamlit UI" || echo "  ❌ Streamlit UI - Check /tmp/streamlit.log"

# Check workers
ps aux | grep -q "python -m src.worker" && echo "  ✅ Background Workers (2 running)" || echo "  ❌ Workers - Check /tmp/verification-worker.log and /tmp/dataset-worker.log"

echo ""
echo "📊 Access URLs:"
echo "  🌐 Streamlit UI:        https://YOUR_RUNPOD_ID.proxy.runpod.net (port 8501)"
echo "  📚 API Gateway:         http://localhost:8000/docs"
echo "  🤖 QA Orchestrator:     http://localhost:8001/docs"
echo "  📄 Document Ingestion:  http://localhost:8002/docs"
echo "  🗄️  Qdrant Dashboard:    http://localhost:6333/dashboard"
echo ""
echo "📋 View logs:"
echo "  tail -f /tmp/qdrant.log"
echo "  tail -f /tmp/document-ingestion.log"
echo "  tail -f /tmp/qa-orchestrator.log"
echo "  tail -f /tmp/verification-worker.log"
echo "  tail -f /tmp/dataset-worker.log"
echo "  tail -f /tmp/api-gateway.log"
echo "  tail -f /tmp/streamlit.log"
echo ""
echo "📊 Data directories:"
echo "  Training data: /workspace/rlvr-pdf-chat/data/training_data/"
echo "  DPO dataset:   /workspace/rlvr-pdf-chat/data/dpo_data/"
echo "  Note: Workers also write to /app/data/ - copy files if needed"
echo ""
echo "🎯 GPU Status:"
nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total --format=csv,noheader 2>/dev/null || echo "  No GPU detected"
echo ""
echo "🚀 Quick start:"
echo "  1. Upload PDF: curl -X POST http://localhost:8002/ingest -F 'file=@your-file.pdf'"
echo "  2. Ask question via UI: Open Streamlit URL above"
echo "  3. Check DPO data: cat /app/data/dpo_data/dpo_data_*.jsonl | wc -l"
echo ""

