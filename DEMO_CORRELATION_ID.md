# Demo: Correlation ID Tracing

## 🎯 What You'll Demo

Show how to trace a request from UI → DPO file using correlation IDs!

## 📋 Setup (on Runpod)

```bash
cd /workspace/rlvr-automation
git pull origin main

# Restart services to pick up changes
./runpod-start-relaxed-thresholds.sh
```

## 🚀 Demo Script

### Step 1: Send a Question

```bash
# Send a question and capture the response
curl -X POST http://localhost:8001/ask/multi-candidate \
  -H 'Content-Type: application/json' \
  -d '{"question": "What is AWS Lambda?", "num_candidates": 3}' \
  | jq .
```

**Expected Output:**
```json
{
  "question": "What is AWS Lambda?",
  "candidates": [...],
  "num_candidates": 3,
  "events_published": 3,
  "batch_id": "abc-123-def-456",
  "correlation_id": "xyz-789-ghi-012"  ← COPY THIS!
}
```

### Step 2: Copy the correlation_id

From the response above, copy the `correlation_id` value.

Example: `xyz-789-ghi-012`

### Step 3: Trace the Request

```bash
# Replace with your actual correlation_id
./trace-request.sh xyz-789-ghi-012
```

**Expected Output:**
```
════════════════════════════════════════════════════════════════════════════
  🔍 REQUEST TRACE: xyz-789-ghi-012
  2025-12-24 13:45:30
════════════════════════════════════════════════════════════════════════════

📄 api-gateway.log (2 matches)
────────────────────────────────────────────────────────────────────────────
  [correlation_id=xyz-789] Multi-candidate request: What is AWS Lambda?...
  [correlation_id=xyz-789] Multi-candidate response sent (batch_id=abc-123)

📄 qa-orchestrator.log (5 matches)
────────────────────────────────────────────────────────────────────────────
  [correlation_id=xyz-789] Received multi-candidate request: What is AWS Lambda?
  [correlation_id=xyz-789] [batch_id=abc-123] Publishing 3 answer.generated events
  [correlation_id=xyz-789] [batch_id=abc-123] Published answer.generated event for candidate 1/3
  [correlation_id=xyz-789] [batch_id=abc-123] Published answer.generated event for candidate 2/3
  [correlation_id=xyz-789] [batch_id=abc-123] Published answer.generated event for candidate 3/3

📄 verification-worker.log (6 matches)
────────────────────────────────────────────────────────────────────────────
  [correlation_id=xyz-789] [batch_id=abc-123] Processing answer.generated event
  [correlation_id=xyz-789] [batch_id=abc-123] Verification complete: faithfulness=0.850
  [correlation_id=xyz-789] [batch_id=abc-123] Published verification.completed event
  ...

📄 dataset-worker.log (8 matches)
────────────────────────────────────────────────────────────────────────────
  [correlation_id=xyz-789] [batch_id=abc-123] Received answer.generated
  [correlation_id=xyz-789] Received verification.completed
  [correlation_id=xyz-789] [batch_id=abc-123] DPO pair created: score_diff=0.120
  ...

════════════════════════════════════════════════════════════════════════════
  ✅ Found 21 log entries for: xyz-789-ghi-012
════════════════════════════════════════════════════════════════════════════

📊 Summary:
────────────────────────────────────────────────────────────────────────────
  Question: What is AWS Lambda?
  Answer events: 3
  Verification events: 3
  DPO pair created: ✅ YES
```

### Step 4: Show Real-Time Monitoring

```bash
# In one terminal, start monitoring
tail -f /workspace/logs/*.log | grep "correlation_id=xyz-789"

# In another terminal, send the same question again
curl -X POST http://localhost:8001/ask/multi-candidate \
  -H 'Content-Type: application/json' \
  -d '{"question": "What is AWS Lambda?", "num_candidates": 3}'
```

You'll see logs streaming in real-time with the correlation_id!

## 🎬 Demo Talking Points

### 1. The Problem
"Before, when you sent a question from the UI, you couldn't track what happened to it. Did it create a DPO pair? Why not? Where did it fail?"

### 2. The Solution
"Now, every request gets a unique correlation_id that follows it through the entire system."

### 3. The Flow
"Watch this: I send a question, get back a correlation_id, and now I can trace it through:
- API Gateway (receives request)
- QA Orchestrator (generates 3 candidates)
- Verification Worker (scores each candidate)
- Dataset Worker (creates DPO pair if thresholds met)"

### 4. The Benefits
"This is perfect for:
- Debugging: Why didn't my question create a DPO pair?
- Monitoring: How long did each step take?
- Verification: Did all 3 candidates get verified?
- Production: Track every request in production"

## 🔍 Advanced Demo

### Show Why a DPO Pair Wasn't Created

```bash
# Send a question that might not create DPO
curl -X POST http://localhost:8001/ask/multi-candidate \
  -H 'Content-Type: application/json' \
  -d '{"question": "Hello", "num_candidates": 3}' \
  | jq .

# Copy correlation_id, then trace it
./trace-request.sh <correlation_id>

# Look for rejection reason in the summary:
# "DPO pair created: ❌ NO"
# "Rejection reason: Score diff too small (0.02 < 0.05)"
```

### Show Processing Time

```bash
# Trace a request and look at timestamps
./trace-request.sh <correlation_id> | grep -E "timestamp|Duration"
```

### Show All Recent Requests

```bash
# Show last 10 correlation IDs
tail -100 /workspace/logs/api-gateway.log | grep -oP 'correlation_id=\K[a-f0-9-]+' | tail -10

# Trace each one to see which created DPO pairs
for id in $(tail -100 /workspace/logs/api-gateway.log | grep -oP 'correlation_id=\K[a-f0-9-]+' | tail -5); do
    echo "Tracing: $id"
    ./trace-request.sh $id | grep "DPO pair created"
done
```

## 📊 Key Metrics to Show

1. **Request Coverage**: Every request is tracked
2. **Event Completeness**: All 3 candidates → 3 verifications
3. **DPO Success Rate**: How many requests create DPO pairs
4. **Processing Time**: From request to DPO file

## 🎯 Demo Checklist

- [ ] Pull latest code
- [ ] Restart services
- [ ] Send test question
- [ ] Copy correlation_id from response
- [ ] Run trace script
- [ ] Show complete lifecycle
- [ ] Explain each step
- [ ] Show rejection reason (if applicable)
- [ ] Show real-time monitoring

## 💡 Tips

1. **Use jq**: Makes JSON responses readable
2. **Keep correlation_id handy**: Copy it immediately
3. **Show both success and failure**: Demonstrates debugging power
4. **Explain the architecture**: How correlation_id flows through system
5. **Highlight the value**: Production debugging, monitoring, verification

## 🚀 One-Liner Demo

```bash
# Send question, extract correlation_id, and trace it automatically
CORR_ID=$(curl -s -X POST http://localhost:8001/ask/multi-candidate \
  -H 'Content-Type: application/json' \
  -d '{"question": "What is AWS Lambda?", "num_candidates": 3}' \
  | jq -r '.correlation_id') && \
echo "Correlation ID: $CORR_ID" && \
sleep 5 && \
./trace-request.sh $CORR_ID
```

This sends the question, waits 5 seconds for processing, then automatically traces it! 🎉

