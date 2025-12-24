#!/bin/bash

echo "=========================================="
echo "  RLVR AUTOMATION - RUNPOD STARTUP"
echo "=========================================="
echo ""

# Set RabbitMQ URL for localhost (using rlvr credentials)
export RABBITMQ_URL="amqp://rlvr:rlvr_password@localhost:5672/"

# Create log directory
mkdir -p /workspace/logs

# Stop any existing workers
echo "1. Stopping existing workers..."
pkill -f "verification-worker" 2>/dev/null
pkill -f "dataset-generation-worker" 2>/dev/null
sleep 2

# Start Verification Worker
echo ""
echo "2. Starting Verification Worker..."
cd /workspace/rlvr-automation/workers/verification-worker
RABBITMQ_URL="amqp://rlvr:rlvr_password@localhost:5672/" \
nohup python -m src.worker > /workspace/logs/verification-worker.log 2>&1 &
VERIFY_PID=$!
sleep 3

# Check verification worker
if grep -q "Consumer started" /workspace/logs/verification-worker.log 2>/dev/null; then
    echo "   ✅ Verification worker connected (PID: $VERIFY_PID)"
else
    echo "   ⚠️  Verification worker may have issues"
    echo "   Last 5 lines of log:"
    tail -5 /workspace/logs/verification-worker.log
fi

# Start Dataset Worker
echo ""
echo "3. Starting Dataset Worker..."
cd /workspace/rlvr-automation/workers/dataset-generation-worker
RABBITMQ_URL="amqp://rlvr:rlvr_password@localhost:5672/" \
nohup python -m src.worker > /workspace/logs/dataset-worker.log 2>&1 &
DATASET_PID=$!
sleep 3

# Check dataset worker
if ps -p $DATASET_PID > /dev/null 2>&1; then
    echo "   ✅ Dataset worker running (PID: $DATASET_PID)"
else
    echo "   ⚠️  Dataset worker failed"
    echo "   Last 5 lines of log:"
    tail -5 /workspace/logs/dataset-worker.log
fi

echo ""
echo "=========================================="
echo "  ✅ WORKERS STARTED!"
echo "=========================================="
echo ""
echo "Worker Status:"
echo "  • Verification Worker: PID $VERIFY_PID"
echo "  • Dataset Worker:      PID $DATASET_PID"
echo ""
echo "Next Steps:"
echo "  1. Send a test query:"
echo "     curl -X POST http://localhost:8001/ask/multi-candidate \\"
echo "       -H 'Content-Type: application/json' \\"
echo "       -d '{\"question\": \"What is Docker?\", \"num_candidates\": 3}'"
echo ""
echo "  2. View the dashboard:"
echo "     cd /workspace/rlvr-automation"
echo "     ./rlvr-dashboard.sh --auto"
echo ""
echo "  3. Monitor logs:"
echo "     tail -f /workspace/logs/verification-worker.log"
echo "     tail -f /workspace/logs/dataset-worker.log"
echo ""

