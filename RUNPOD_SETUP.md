# RunPod Native Deployment Guide

## 🚀 Quick Start

After starting your RunPod instance, run:

```bash
cd /workspace/rlvr-pdf-chat
git pull  # Get latest fixes
chmod +x runpod_launch_all.sh
./runpod_launch_all.sh
```

This script will:
1. ✅ Install Qdrant binary (if not present)
2. ✅ Set all environment variables for native deployment
3. ✅ Start all services with correct PYTHONPATH
4. ✅ Run health checks
5. ✅ Display access URLs and logs

---

## 📋 What Gets Started

### Infrastructure Services
- **Qdrant** (port 6333) - Vector database
- **Ollama** (port 11434) - LLM inference (should already be running)
- **RabbitMQ** (port 5672) - Event bus (should already be running)

### Application Services
- **Document Ingestion** (port 8002) - PDF upload and processing
- **QA Orchestrator** (port 8001) - Question answering with multi-candidate generation
- **API Gateway** (port 8000) - Main API entry point
- **Streamlit UI** (port 8501) - Web interface

### Background Workers
- **Verification Worker** - RAGAS quality scoring
- **Dataset Worker** - DPO dataset generation

---

## 🔧 Key Fixes Applied

### 1. Qdrant API Compatibility
- Uses `search()` instead of deprecated `query_points()`
- Iterates directly over results (not `.points` attribute)

### 2. Environment Variables
All services use `localhost` instead of Docker service names:
- `QDRANT_URL=http://localhost:6333`
- `OLLAMA_URL=http://localhost:11434`
- `RABBITMQ_URL=amqp://rlvr:rlvr_password@localhost:5672/`

### 3. Worker Module Paths
Workers run as `python -m src.worker` with correct PYTHONPATH

### 4. Data Directories
- Training data: `/workspace/rlvr-pdf-chat/data/training_data/`
- DPO dataset: `/app/data/dpo_data/` (workers write here)

### 5. Prompt Engineering
- Changed from advisory/sales tone to factual documentation tone
- Removed persuasive language ("I recommend", "you should")

---

## 📊 Verify Everything is Working

```bash
# Check all services
curl http://localhost:6333/collections  # Qdrant
curl http://localhost:8002/health       # Document Ingestion
curl http://localhost:8001/health       # QA Orchestrator
curl http://localhost:8000/health       # API Gateway
curl http://localhost:8501              # Streamlit UI

# Check workers
ps aux | grep "python -m src.worker"

# View logs
tail -f /tmp/qa-orchestrator.log
tail -f /tmp/verification-worker.log
tail -f /tmp/dataset-worker.log
```

---

## 📄 Upload a PDF

```bash
curl -X POST http://localhost:8002/ingest \
  -F "file=@/workspace/rlvr-pdf-chat/aws-support-guide.pdf"
```

---

## 🎯 Ask Questions

### Via UI
Open: `https://YOUR_RUNPOD_ID.proxy.runpod.net` (port 8501)

### Via API
```bash
curl -X POST http://localhost:8001/ask/multi-candidate \
  -H "Content-Type: application/json" \
  -d '{"question": "What is AWS Support?", "num_candidates": 3, "publish_events": true}'
```

---

## 📊 Check DPO Dataset

```bash
# View DPO pairs
cat /app/data/dpo_data/dpo_data_*.jsonl

# Count pairs
wc -l /app/data/dpo_data/dpo_data_*.jsonl

# Statistics
python3 -c "
import json
with open('/app/data/dpo_data/dpo_data_202512.jsonl', 'r') as f:
    pairs = [json.loads(line) for line in f]
    print(f'Total DPO pairs: {len(pairs)}')
    print(f'Unique questions: {len(set(p[\"prompt\"] for p in pairs))}')
    scores = [p['metadata']['score_difference'] for p in pairs]
    print(f'Avg score diff: {sum(scores)/len(scores):.3f}')
"
```

---

## 🐛 Troubleshooting

### Service won't start
```bash
# Check logs
tail -50 /tmp/<service-name>.log

# Restart specific service
pkill -f "uvicorn.*8001"  # Kill QA Orchestrator
cd /workspace/rlvr-pdf-chat/services/qa-orchestrator
export QDRANT_URL=http://localhost:6333
export OLLAMA_URL=http://localhost:11434
export RABBITMQ_URL=amqp://rlvr:rlvr_password@localhost:5672/
PYTHONPATH=/workspace/rlvr-pdf-chat/services/qa-orchestrator:/workspace/rlvr-pdf-chat \
  nohup uvicorn src.main:app --host 0.0.0.0 --port 8001 > /tmp/qa-orchestrator.log 2>&1 &
```

### Workers not processing events
```bash
# Check worker logs
tail -f /tmp/verification-worker.log
tail -f /tmp/dataset-worker.log

# Restart workers
pkill -f "python -m src.worker"
cd /workspace/rlvr-pdf-chat/workers/verification-worker
PYTHONPATH=/workspace/rlvr-pdf-chat/workers/verification-worker:/workspace/rlvr-pdf-chat \
  nohup python -m src.worker > /tmp/verification-worker.log 2>&1 &
```

### No DPO data generated
- Need at least 3 questions with 3 candidates each
- Check verification worker is running
- Check dataset worker logs for errors
- Verify score differences are > 0.3 (quality threshold)

---

## 💾 Persistence Note

**⚠️ RunPod `/workspace` is persistent, but `/tmp` and `/app` are not!**

Before stopping your pod:
```bash
# Copy DPO data to workspace
cp /app/data/dpo_data/*.jsonl /workspace/rlvr-pdf-chat/data/dpo_data/
```

---

## 🎓 Next Steps

1. Ask 10-20 questions to build a good DPO dataset
2. Review DPO pairs for quality
3. Use the dataset to fine-tune your LLM
4. Deploy the fine-tuned model back to Ollama
5. Repeat the cycle!

