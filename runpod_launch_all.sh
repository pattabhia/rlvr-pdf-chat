#!/bin/bash

echo "🚀 Launching all RLVR services..."

# Kill any conflicting services from RunPod base image
echo "Stopping conflicting services..."
pkill nginx || true
pkill -f uvicorn || true
pkill -f streamlit || true
sleep 2

# Set environment
export PYTHONPATH=/workspace/rlvr-pdf-chat
export RABBITMQ_URL=amqp://rlvr:rlvr_password@localhost:5672/
export OLLAMA_HOST=http://localhost:11434
export QDRANT_URL=http://localhost:6333
export MIN_SCORE_DIFF=0.3
export MIN_CHOSEN_SCORE=0.7
export ENABLE_QUALITY_FILTER=true
export TIMEOUT_MINUTES=30

cd /workspace/rlvr-pdf-chat

# Start QA Orchestrator
echo "Starting QA Orchestrator..."
cd services/qa-orchestrator/src
nohup uvicorn main:app --host 0.0.0.0 --port 8001 > /tmp/qa-orchestrator.log 2>&1 &
echo "QA Orchestrator PID: $!"

# Start Verification Worker
echo "Starting Verification Worker..."
cd /workspace/rlvr-pdf-chat/workers/verification-worker/src
nohup python -m worker > /tmp/verification-worker.log 2>&1 &
echo "Verification Worker PID: $!"

# Start Dataset Generation Worker
echo "Starting Dataset Generation Worker..."
cd /workspace/rlvr-pdf-chat/workers/dataset-generation-worker/src
nohup python -m worker > /tmp/dataset-worker.log 2>&1 &
echo "Dataset Worker PID: $!"

# Start API Gateway
echo "Starting API Gateway..."
cd /workspace/rlvr-pdf-chat/services/api-gateway/src
nohup uvicorn main:app --host 0.0.0.0 --port 8000 > /tmp/api-gateway.log 2>&1 &
echo "API Gateway PID: $!"

# Start Streamlit UI
echo "Starting Streamlit UI..."
cd /workspace/rlvr-pdf-chat/ui/streamlit/src
nohup streamlit run app_simple.py --server.port=8501 --server.address=0.0.0.0 > /tmp/streamlit.log 2>&1 &
echo "Streamlit UI PID: $!"

sleep 10

echo ""
echo "=========================================="
echo "✅ All services started!"
echo "=========================================="
echo ""
echo "📊 Access URLs:"
echo "  🌐 Streamlit UI:    http://YOUR_RUNPOD_IP:8501"
echo "  📚 API Gateway:     http://YOUR_RUNPOD_IP:8000/docs"
echo "  🤖 QA Orchestrator: http://YOUR_RUNPOD_IP:8001/docs"
echo ""
echo "📋 View logs:"
echo "  tail -f /tmp/qa-orchestrator.log"
echo "  tail -f /tmp/verification-worker.log"
echo "  tail -f /tmp/dataset-worker.log"
echo "  tail -f /tmp/streamlit.log"
echo ""
echo "🎯 GPU Status:"
nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total --format=csv,noheader
echo ""
echo "🏥 Health checks:"
sleep 5
curl -sf http://localhost:8001/health && echo "✅ QA Orchestrator" || echo "❌ QA Orchestrator"
curl -sf http://localhost:8000/health && echo "✅ API Gateway" || echo "❌ API Gateway"
curl -sf http://localhost:8501 && echo "✅ Streamlit UI" || echo "❌ Streamlit UI"
curl -sf http://localhost:11434/api/tags && echo "✅ Ollama" || echo "❌ Ollama"
echo ""

