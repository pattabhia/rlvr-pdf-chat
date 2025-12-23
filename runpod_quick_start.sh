#!/bin/bash
set -e

echo "=========================================="
echo "🚀 RLVR Quick Start for RunPod"
echo "=========================================="

# Check GPU
echo ""
echo "🔍 GPU Info:"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader

# Install Docker
echo ""
echo "📦 Installing Docker..."
apt-get update -qq
apt-get install -y -qq curl ca-certificates gnupg lsb-release postgresql-client
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
rm get-docker.sh

# Install Docker Compose
echo ""
echo "📦 Installing Docker Compose..."
curl -L "https://github.com/docker/compose/releases/download/v2.23.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Start Docker daemon
echo ""
echo "🐳 Starting Docker daemon..."
dockerd > /tmp/dockerd.log 2>&1 &
sleep 10

# Verify Docker
docker --version
docker-compose --version

# Install Ollama
echo ""
echo "📦 Installing Ollama..."
curl -fsSL https://ollama.com/install.sh | sh

# Start Ollama with GPU
echo ""
echo "🚀 Starting Ollama with GPU..."
export OLLAMA_HOST=0.0.0.0:11434
export OLLAMA_GPU_LAYERS=999
ollama serve > /tmp/ollama.log 2>&1 &
sleep 10

# Pull model
echo ""
echo "📥 Pulling Llama 3.2:3b model..."
ollama pull llama3.2:3b

# Start services
echo ""
echo "🚀 Starting microservices..."
cd /workspace/rlvr-pdf-chat/infrastructure
docker-compose up -d

# Wait for services
echo ""
echo "⏳ Waiting for services to initialize..."
sleep 30

# Health checks
echo ""
echo "🏥 Health Checks:"
curl -sf http://localhost:8000/health && echo "✅ API Gateway" || echo "❌ API Gateway"
curl -sf http://localhost:8001/health && echo "✅ QA Orchestrator" || echo "❌ QA Orchestrator"
curl -sf http://localhost:8501 && echo "✅ Streamlit UI" || echo "❌ Streamlit UI"
curl -sf http://localhost:11434/api/tags && echo "✅ Ollama" || echo "❌ Ollama"

echo ""
echo "=========================================="
echo "✅ RLVR is READY!"
echo "=========================================="
echo ""
echo "📊 Access URLs (replace with your RunPod IP):"
echo "  🌐 Streamlit UI:    http://YOUR_RUNPOD_IP:8501"
echo "  📚 API Gateway:     http://YOUR_RUNPOD_IP:8000/docs"
echo "  🤖 QA Orchestrator: http://YOUR_RUNPOD_IP:8001/docs"
echo ""
echo "🎯 GPU Status:"
nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total --format=csv,noheader
echo ""
echo "📋 View logs:"
echo "  docker-compose logs -f"
echo ""

# Keep container running
tail -f /tmp/ollama.log
