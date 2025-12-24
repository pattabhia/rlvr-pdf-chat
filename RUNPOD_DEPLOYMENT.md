# RunPod Deployment Guide

## ✅ Pre-Deployment Checklist

All issues have been resolved and committed to GitHub:

- ✅ **Numpy dependency conflict** - Fixed (numpy>=1.23.2,<2.0.0)
- ✅ **Directory path issues** - Fixed
- ✅ **Secrets removed** - Cleaned from git history
- ✅ **LangChain version conflicts** - Resolved (all services use 0.3.x)
- ✅ **langchain-ollama version** - Corrected (0.3.x, not 1.x)
- ✅ **uvicorn conflicts** - Unified (>=0.24.0)
- ✅ **httpx conflicts** - Unified (>=0.25.1)
- ✅ **sentence-transformers conflicts** - Unified (>=2.7.0)
- ✅ **Full observability stack** - Added (Prometheus, Grafana, Loki, Tempo)
- ✅ **Native deployment** - No Docker required

## 🚀 Deployment Steps

### 1. Launch RunPod Instance

Choose a GPU instance (recommended: RTX 4090 or A100)

### 2. Clone Repository

```bash
cd /workspace
git clone https://github.com/pattabhia/rlvr-automation.git
cd rlvr-automation
```

### 3. Run Deployment Script

```bash
bash runpod_launch_all.sh
```

**Expected time:** 15-20 minutes

## 📊 What Gets Deployed

### Core Services
- **Ollama** (LLM) - Auto-installs llama3.2:3b
- **Qdrant** (Vector DB) - Port 6333
- **RabbitMQ** (Message Queue) - Port 5672, Management: 15672
- **Document Ingestion** - Port 8002
- **QA Orchestrator** - Port 8001
- **API Gateway** - Port 8000
- **Streamlit UI** - Port 8501
- **Verification Worker**
- **Dataset Generation Worker**

### Observability Stack
- **Prometheus** (Metrics) - Port 9090
- **Grafana** (Dashboards) - Port 3000
- **Loki** (Logs) - Port 3100
- **Tempo** (Traces) - Port 3200
- **OpenTelemetry Collector** - Port 4317/4318

## 🌐 Access URLs

Replace `<runpod-id>` and `<runpod-ip>` with your instance details.

### Main Services
- Streamlit UI: `https://<runpod-id>.proxy.runpod.net`
- API Gateway: `http://<runpod-ip>:8000/docs`
- QA Orchestrator: `http://<runpod-ip>:8001/docs`
- Document Ingestion: `http://<runpod-ip>:8002/docs`
- Qdrant Dashboard: `http://<runpod-ip>:6333/dashboard`

### Observability
- Grafana: `http://<runpod-ip>:3000` (admin/admin)
- Prometheus: `http://<runpod-ip>:9090`
- Loki: `http://<runpod-ip>:3100`
- Tempo: `http://<runpod-ip>:3200`
- RabbitMQ: `http://<runpod-ip>:15672` (rlvr/rlvr_password)

## 📋 Monitoring

### View Logs
```bash
tail -f /workspace/logs/ollama.log
tail -f /workspace/logs/qdrant.log
tail -f /workspace/logs/document-ingestion.log
tail -f /workspace/logs/qa-orchestrator.log
tail -f /workspace/logs/api-gateway.log
tail -f /workspace/logs/streamlit.log
tail -f /workspace/logs/verification-worker.log
tail -f /workspace/logs/dataset-worker.log
tail -f /workspace/logs/prometheus.log
tail -f /workspace/logs/grafana.log
tail -f /workspace/logs/loki.log
tail -f /workspace/logs/tempo.log
```

### Check Running Processes
```bash
ps aux | grep -E "ollama|qdrant|uvicorn|streamlit|prometheus|grafana|loki|tempo|otelcol|rabbitmq"
```

## 🎯 Quick Start

### 1. Upload a PDF
```bash
curl -X POST http://localhost:8002/ingest -F 'file=@your-document.pdf'
```

### 2. Ask Questions
Open Streamlit UI: `https://<runpod-id>.proxy.runpod.net`

### 3. View Metrics
Open Grafana: `http://<runpod-ip>:3000`

### 4. Check Training Data
```bash
cat /workspace/rlvr-automation/data/dpo_data/dpo_data_*.jsonl | wc -l
```

## 🔧 Troubleshooting

### Service Not Starting
Check the specific service log in `/workspace/logs/`

### Dependency Issues
All dependencies have been tested and verified compatible. If you encounter issues, ensure you're using the latest code from GitHub.

### Port Conflicts
Ensure no other services are using the required ports (8000-8002, 8501, 6333, 5672, 9090, 3000, 3100, 3200, 4317, 4318, 15672)

## 📝 Notes

- All services run natively (no Docker required)
- Logs are centralized in `/workspace/logs/`
- Data is stored in `/workspace/rlvr-automation/data/`
- The deployment is optimized for RunPod's environment

