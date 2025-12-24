# 🚀 RUNPOD - Quick Command Reference

## Step 1: Pull Latest Code

```bash
cd /workspace/rlvr-automation
git pull origin main
```

## Step 2: Start Workers

```bash
./runpod-start.sh
```

**Expected Output:**
```
✅ Verification worker connected (PID: XXXXX)
✅ Dataset worker running (PID: XXXXX)
```

## Step 3: Send Test Query

```bash
curl -X POST http://localhost:8001/ask/multi-candidate \
  -H 'Content-Type: application/json' \
  -d '{"question": "What is Docker?", "num_candidates": 3}'
```

## Step 4: View Real-Time Dashboard

```bash
./rlvr-dashboard.sh --auto
```

**Press Ctrl+C to exit**

---

## 🔍 Troubleshooting Commands

### Check Worker Status
```bash
ps aux | grep -E "verification-worker|dataset-worker" | grep -v grep
```

### View Logs
```bash
# Verification worker
tail -f /workspace/logs/verification-worker.log

# Dataset worker
tail -f /workspace/logs/dataset-worker.log

# QA Orchestrator
tail -f /workspace/logs/qa-orchestrator.log
```

### Test Dashboard Parsing
```bash
./test-dashboard.sh
```

### Restart Workers
```bash
./runpod-start.sh
```

### Check DPO Files
```bash
find /workspace/rlvr-automation/data -name "*.json" -type f
ls -lh /workspace/rlvr-automation/data/dpo/
```

---

## 📊 Dashboard Modes

| Command | Description |
|---------|-------------|
| `./rlvr-dashboard.sh` | Manual refresh (press ENTER) |
| `./rlvr-dashboard.sh --auto` | Auto-refresh every 5 seconds |

---

## 🎯 Complete Test Flow

```bash
# 1. Pull code
cd /workspace/rlvr-automation && git pull

# 2. Start workers
./runpod-start.sh

# 3. Send query (in another terminal)
curl -X POST http://localhost:8001/ask/multi-candidate \
  -H 'Content-Type: application/json' \
  -d '{"question": "What is Kubernetes?", "num_candidates": 3}'

# 4. Watch dashboard (auto-refresh)
./rlvr-dashboard.sh --auto
```

---

## 🐛 Common Issues & Fixes

### Issue: Workers won't connect to RabbitMQ
**Fix:**
```bash
export RABBITMQ_URL="amqp://guest:guest@localhost:5672/"
./runpod-start.sh
```

### Issue: Dashboard shows no data
**Fix:**
```bash
# 1. Send a query first
curl -X POST http://localhost:8001/ask/multi-candidate \
  -H 'Content-Type: application/json' \
  -d '{"question": "Test", "num_candidates": 3}'

# 2. Wait 15 seconds
sleep 15

# 3. Test parsing
./test-dashboard.sh

# 4. View dashboard
./rlvr-dashboard.sh --auto
```

### Issue: RAGAS temperature error
**Impact:** Worker uses fallback heuristic (still works!)
**No action needed** - verification will continue with fallback scores

---

## 📁 Important Paths

| Path | Description |
|------|-------------|
| `/workspace/logs/` | All log files |
| `/workspace/rlvr-automation/data/dpo/` | DPO training data |
| `/workspace/rlvr-automation/workers/` | Worker source code |

---

## 💡 Pro Tips

1. **Use auto-refresh** during testing: `./rlvr-dashboard.sh --auto`
2. **Send multiple queries** to see the full pipeline
3. **Check logs** if something seems wrong
4. **Test parsing first** with `./test-dashboard.sh`

---

## 📞 Quick Health Check

```bash
# One-liner to check everything
echo "Workers:" && ps aux | grep -E "verification-worker|dataset-worker" | grep -v grep && \
echo -e "\nLogs:" && ls -lh /workspace/logs/*.log && \
echo -e "\nDPO Files:" && find /workspace/rlvr-automation/data -name "*.json" | wc -l
```

