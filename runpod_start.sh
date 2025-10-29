#!/bin/bash
set -e

echo "=========================================="
echo "🚀 RLVR Automation Demo - RunPod Startup"
echo "=========================================="

# Check GPU availability
echo ""
echo "🔍 Checking GPU availability..."
nvidia-smi || echo "⚠️  No GPU detected"

# Start Docker daemon
echo ""
echo "🐳 Starting Docker daemon..."
dockerd &
sleep 5

# Start Ollama with GPU support
echo ""
echo "📦 Starting Ollama with GPU acceleration..."
export OLLAMA_HOST=0.0.0.0:11434
export OLLAMA_GPU_LAYERS=999
ollama serve &
OLLAMA_PID=$!
sleep 10

# Pull Llama model
echo ""
echo "📥 Pulling Llama 3.2:3b model (this may take a few minutes)..."
ollama pull llama3.2:3b

# Verify Ollama is using GPU
echo ""
echo "✅ Verifying Ollama GPU usage..."
ollama list

# Navigate to infrastructure directory
cd /workspace/infrastructure

# Start all services with docker-compose
echo ""
echo "🚀 Starting all microservices..."
docker-compose up -d

# Wait for services to initialize
echo ""
echo "⏳ Waiting for services to start (30 seconds)..."
sleep 30

# Health checks
echo ""
echo "🏥 Running health checks..."
echo ""

check_service() {
    local name=$1
    local url=$2
    if curl -sf "$url" > /dev/null 2>&1; then
        echo "✅ $name is healthy"
    else
        echo "❌ $name is not responding"
    fi
}

check_service "API Gateway" "http://localhost:8000/health"
check_service "QA Orchestrator" "http://localhost:8001/health"
check_service "Document Ingestion" "http://localhost:8002/health"
check_service "Training Data Service" "http://localhost:8005/health"
check_service "Ground Truth Service" "http://localhost:8007/health"
check_service "Streamlit UI" "http://localhost:8501"
check_service "Qdrant Vector DB" "http://localhost:6333/dashboard"
check_service "RabbitMQ" "http://localhost:15672"
check_service "Ollama" "http://localhost:11434/api/tags"

# Display access information
echo ""
echo "=========================================="
echo "✅ RLVR Automation Demo is READY!"
echo "=========================================="
echo ""
echo "📊 Access Points:"
echo "  🌐 Streamlit UI:    http://YOUR_RUNPOD_IP:8501"
echo "  📚 API Gateway:     http://YOUR_RUNPOD_IP:8000/docs"
echo "  🤖 QA Orchestrator: http://YOUR_RUNPOD_IP:8001/docs"
echo "  📄 Doc Ingestion:   http://YOUR_RUNPOD_IP:8002/docs"
echo "  🎓 Training Data:   http://YOUR_RUNPOD_IP:8005/docs"
echo "  ✅ Ground Truth:    http://YOUR_RUNPOD_IP:8007/docs"
echo "  🐰 RabbitMQ:        http://YOUR_RUNPOD_IP:15672 (guest/guest)"
echo "  🔍 Qdrant:          http://YOUR_RUNPOD_IP:6333/dashboard"
echo ""
echo "🎯 GPU Performance:"
nvidia-smi --query-gpu=name,memory.total,memory.used --format=csv,noheader
echo ""
echo "📝 Next Steps:"
echo "  1. Access Streamlit UI and upload your PDF"
echo "  2. Ask questions and see <5s response times!"
echo "  3. Monitor GPU usage with: nvidia-smi"
echo ""
echo "=========================================="

# Show logs
echo ""
echo "📋 Tailing service logs (Ctrl+C to stop)..."
echo ""
docker-compose logs -f

