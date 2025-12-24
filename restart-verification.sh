#!/bin/bash

# Restart Verification Worker with Fix

echo "╔════════════════════════════════════════════════════════════════════════════╗"
echo "║              RESTARTING VERIFICATION WORKER WITH FIX                       ║"
echo "╔════════════════════════════════════════════════════════════════════════════╗"
echo ""

# 1. Pull latest code
echo "1. Pulling latest code..."
git pull origin main
echo ""

# 2. Find and kill verification workers
echo "2. Stopping old verification workers..."
pkill -f "verification-worker" || echo "No verification workers running"
sleep 2
echo ""

# 3. Restart verification worker
echo "3. Starting verification worker..."
cd /workspace/rlvr-automation/workers/verification-worker
nohup python -m src.worker > /workspace/logs/verification-worker.log 2>&1 &
WORKER_PID=$!
echo "Started verification worker (PID: $WORKER_PID)"
echo ""

# 4. Wait a bit and check if it's running
sleep 3
if ps -p $WORKER_PID > /dev/null; then
    echo "✅ Verification worker is running!"
else
    echo "❌ Verification worker failed to start"
    echo "Check logs: tail -f /workspace/logs/verification-worker.log"
    exit 1
fi
echo ""

# 5. Show recent log
echo "5. Recent log output:"
echo "────────────────────────────────────────────────────────────────────────────"
tail -20 /workspace/logs/verification-worker.log
echo ""

echo "════════════════════════════════════════════════════════════════════════════"
echo "  ✅ DONE! Verification worker restarted with fix"
echo "════════════════════════════════════════════════════════════════════════════"
echo ""
echo "Now try entering a query in the UI and watch:"
echo "  ./watch-pipeline.sh"
echo ""
echo "You should see DIFFERENT scores for each candidate now!"
echo ""

