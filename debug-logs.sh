#!/bin/bash

echo "=========================================="
echo "  DEBUG LOG PARSING"
echo "=========================================="
echo ""

LOG_DIR="/workspace/logs"

echo "1. Checking verification-worker.log for RAGAS scores:"
echo "   Looking for 'Verification complete' lines..."
echo ""
tail -100 "$LOG_DIR/verification-worker.log" 2>/dev/null | grep -a "Verification complete" 2>/dev/null | tail -5
echo ""

echo "2. Checking dataset-worker.log for DPO activity:"
echo "   Looking for DPO-related lines..."
echo ""
tail -100 "$LOG_DIR/dataset-worker.log" 2>/dev/null | grep -a -iE "dpo|preference|chosen|rejected|pair|saved" 2>/dev/null | tail -10
echo ""

echo "3. Checking for verification.completed events:"
echo ""
tail -100 "$LOG_DIR/verification-worker.log" 2>/dev/null | grep -a "verification.completed" 2>/dev/null | tail -5
echo ""

echo "4. Checking dataset worker for received events:"
echo ""
tail -100 "$LOG_DIR/dataset-worker.log" 2>/dev/null | grep -a "Received event" 2>/dev/null | tail -10
echo ""

echo "5. Full last 20 lines of verification-worker.log:"
echo ""
tail -20 "$LOG_DIR/verification-worker.log" 2>/dev/null
echo ""

echo "6. Full last 20 lines of dataset-worker.log:"
echo ""
tail -20 "$LOG_DIR/dataset-worker.log" 2>/dev/null
echo ""

echo "=========================================="
echo "  CHECKING DATA FILES"
echo "=========================================="
echo ""

echo "7. Looking for DPO JSON files:"
find /workspace/rlvr-automation/data -name "*.json" -type f 2>/dev/null | head -10
echo ""

echo "8. Checking data directory structure:"
ls -lR /workspace/rlvr-automation/data 2>/dev/null | head -30
echo ""

echo "=========================================="

