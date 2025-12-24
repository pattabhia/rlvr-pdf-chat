#!/bin/bash

# Force restart verification worker - PROPERLY

echo "════════════════════════════════════════════════════════════════════════════"
echo "  FORCE RESTARTING VERIFICATION WORKER"
echo "════════════════════════════════════════════════════════════════════════════"
echo ""

# 1. Find ALL verification workers
echo "1. Finding all verification workers..."
pids=$(ps aux | grep -E "python.*verification-worker|verification.*worker" | grep -v grep | awk '{print $2}')

if [ -z "$pids" ]; then
    echo "   No verification workers running"
else
    echo "   Found PIDs: $pids"
    echo ""
    echo "2. Killing all verification workers..."
    for pid in $pids; do
        echo "   Killing PID $pid"
        kill -9 $pid 2>/dev/null
    done
    sleep 2
fi
echo ""

# 3. Verify they're dead
echo "3. Verifying workers are stopped..."
remaining=$(ps aux | grep -E "python.*verification-worker|verification.*worker" | grep -v grep | wc -l)
if [ $remaining -gt 0 ]; then
    echo "   ❌ Some workers still running!"
    ps aux | grep verification-worker | grep -v grep
    exit 1
else
    echo "   ✅ All workers stopped"
fi
echo ""

# 4. Check RabbitMQ connection info
echo "4. Checking RabbitMQ configuration..."
if [ -f "/workspace/rlvr-automation/workers/verification-worker/.env" ]; then
    echo "   .env file found:"
    grep RABBITMQ /workspace/rlvr-automation/workers/verification-worker/.env
elif [ -f "/workspace/rlvr-automation/.env" ]; then
    echo "   Root .env file found:"
    grep RABBITMQ /workspace/rlvr-automation/.env
else
    echo "   No .env file found, using defaults"
    echo "   RABBITMQ_HOST=${RABBITMQ_HOST:-localhost}"
fi
echo ""

# 5. Check if RabbitMQ is running
echo "5. Checking if RabbitMQ is running..."
if pgrep -f rabbitmq > /dev/null; then
    echo "   ✅ RabbitMQ is running"
else
    echo "   ❌ RabbitMQ is NOT running!"
    echo ""
    echo "   You need to start RabbitMQ first:"
    echo "   sudo service rabbitmq-server start"
    echo ""
    echo "   Or if using Docker:"
    echo "   docker ps | grep rabbitmq"
    exit 1
fi
echo ""

# 6. Clear the old log
echo "6. Clearing old verification log..."
> /workspace/logs/verification-worker.log
echo "   ✅ Log cleared"
echo ""

# 7. Start new verification worker
echo "7. Starting new verification worker..."
cd /workspace/rlvr-automation/workers/verification-worker

# Set RabbitMQ URL (using rlvr credentials)
export RABBITMQ_URL="amqp://rlvr:rlvr_password@localhost:5672/"

# Start in background with RabbitMQ URL
RABBITMQ_URL="amqp://rlvr:rlvr_password@localhost:5672/" \
nohup python -m src.worker >> /workspace/logs/verification-worker.log 2>&1 &
NEW_PID=$!

echo "   Started with PID: $NEW_PID"
echo ""

# 8. Wait and check if it's running
echo "8. Waiting for worker to start..."
sleep 5

if ps -p $NEW_PID > /dev/null; then
    echo "   ✅ Worker is running (PID: $NEW_PID)"
else
    echo "   ❌ Worker failed to start!"
    echo ""
    echo "   Check the log:"
    tail -30 /workspace/logs/verification-worker.log
    exit 1
fi
echo ""

# 9. Check for errors in log
echo "9. Checking for startup errors..."
errors=$(grep -i "error\|failed\|exception" /workspace/logs/verification-worker.log | head -5)
if [ ! -z "$errors" ]; then
    echo "   ⚠️  Found errors:"
    echo "$errors"
    echo ""
else
    echo "   ✅ No errors found"
fi
echo ""

# 10. Show recent log
echo "10. Recent log output:"
echo "────────────────────────────────────────────────────────────────────────────"
tail -15 /workspace/logs/verification-worker.log
echo ""

echo "════════════════════════════════════════════════════════════════════════════"
echo "  ✅ VERIFICATION WORKER RESTARTED"
echo "════════════════════════════════════════════════════════════════════════════"
echo ""
echo "Worker PID: $NEW_PID"
echo ""
echo "Now send a test query:"
echo "  curl -X POST http://localhost:8001/ask/multi-candidate \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"question\": \"What is AWS Lambda?\", \"num_candidates\": 3}'"
echo ""
echo "Then check scores (should be DIFFERENT now, not all 0.675):"
echo "  grep 'Verification complete' /workspace/logs/verification-worker.log | tail -5"
echo ""

