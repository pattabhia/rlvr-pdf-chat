#!/bin/bash

# Comprehensive worker diagnostics

LOG_DIR="${LOG_DIR:-/workspace/logs}"

echo "════════════════════════════════════════════════════════════════════════════"
echo "  WORKER DIAGNOSTICS"
echo "════════════════════════════════════════════════════════════════════════════"
echo ""

echo "1. Check which workers are running:"
echo "────────────────────────────────────────────────────────────────────────────"
verification_pid=$(ps aux | grep "verification-worker" | grep -v grep | awk '{print $2}')
dataset_pid=$(ps aux | grep "dataset-generation-worker" | grep -v grep | awk '{print $2}')

if [ -z "$verification_pid" ]; then
    echo "❌ Verification worker: NOT RUNNING"
else
    echo "✅ Verification worker: PID $verification_pid"
fi

if [ -z "$dataset_pid" ]; then
    echo "❌ Dataset worker: NOT RUNNING"
else
    echo "✅ Dataset worker: PID $dataset_pid"
fi
echo ""

echo "2. Check RabbitMQ connection status:"
echo "────────────────────────────────────────────────────────────────────────────"
if [ ! -z "$verification_pid" ]; then
    echo "Verification worker:"
    strings "$LOG_DIR/verification-worker.log" 2>/dev/null | grep -i "consumer\|connected\|rabbitmq" | tail -3
    echo ""
fi

if [ ! -z "$dataset_pid" ]; then
    echo "Dataset worker:"
    strings "$LOG_DIR/dataset-worker.log" 2>/dev/null | grep -i "consumer\|connected\|rabbitmq" | tail -3
    echo ""
fi

echo "3. Check for recent errors:"
echo "────────────────────────────────────────────────────────────────────────────"
echo "Verification worker errors:"
strings "$LOG_DIR/verification-worker.log" 2>/dev/null | grep -i "error\|exception\|failed" | tail -5
echo ""

echo "Dataset worker errors:"
strings "$LOG_DIR/dataset-worker.log" 2>/dev/null | grep -i "error\|exception\|failed" | tail -5
echo ""

echo "4. Check event flow:"
echo "────────────────────────────────────────────────────────────────────────────"
echo "Verification events published (last 5):"
strings "$LOG_DIR/verification-worker.log" 2>/dev/null | grep "Published verification.completed" | tail -5
echo ""

echo "Answer events received by dataset worker (last 5):"
strings "$LOG_DIR/dataset-worker.log" 2>/dev/null | grep "Received answer.generated" | tail -5
echo ""

echo "Verification events received by dataset worker (last 5):"
strings "$LOG_DIR/dataset-worker.log" 2>/dev/null | grep "Received verification.completed" | tail -5
echo ""

echo "Complete entries created (last 5):"
strings "$LOG_DIR/dataset-worker.log" 2>/dev/null | grep "Complete entry" | tail -5
echo ""

echo "5. Check batch tracking (new code):"
echo "────────────────────────────────────────────────────────────────────────────"
batch_events=$(strings "$LOG_DIR/dataset-worker.log" 2>/dev/null | grep "batch" | tail -5)
if [ -z "$batch_events" ]; then
    echo "❌ NO BATCH TRACKING - Workers running OLD code!"
    echo ""
    echo "   Git version in code:"
    cd /workspace/rlvr-automation
    git log --oneline -1
    echo ""
else
    echo "✅ Batch tracking active:"
    echo "$batch_events"
    echo ""
fi

echo "6. Check DPO configuration:"
echo "────────────────────────────────────────────────────────────────────────────"
strings "$LOG_DIR/dataset-worker.log" 2>/dev/null | grep "DPO Dataset Writer initialized" | tail -1
echo ""

echo "════════════════════════════════════════════════════════════════════════════"
echo "  DIAGNOSIS"
echo "════════════════════════════════════════════════════════════════════════════"
echo ""

if [ -z "$verification_pid" ] || [ -z "$dataset_pid" ]; then
    echo "❌ WORKERS NOT RUNNING"
    echo ""
    echo "   ACTION: Start workers"
    echo "   ./runpod-start-relaxed-thresholds.sh"
    echo ""
elif [ -z "$batch_events" ]; then
    echo "❌ WORKERS RUNNING OLD CODE"
    echo ""
    echo "   ACTION: Pull latest code and restart"
    echo "   git pull origin main"
    echo "   ./runpod-start-relaxed-thresholds.sh"
    echo ""
else
    verification_published=$(strings "$LOG_DIR/verification-worker.log" 2>/dev/null | grep "Published verification.completed" | wc -l)
    verification_received=$(strings "$LOG_DIR/dataset-worker.log" 2>/dev/null | grep "Received verification.completed" | wc -l)
    
    echo "Event Flow Analysis:"
    echo "  • Verification events published: $verification_published"
    echo "  • Verification events received by dataset worker: $verification_received"
    echo ""
    
    if [ $verification_published -eq 0 ]; then
        echo "❌ VERIFICATION WORKER NOT PUBLISHING EVENTS"
        echo ""
        echo "   Check verification worker log:"
        echo "   tail -50 /workspace/logs/verification-worker.log"
        echo ""
    elif [ $verification_received -eq 0 ]; then
        echo "❌ DATASET WORKER NOT RECEIVING EVENTS"
        echo ""
        echo "   Possible causes:"
        echo "   • RabbitMQ connection issue"
        echo "   • Wrong routing key"
        echo "   • Event consumer not started"
        echo ""
        echo "   Check dataset worker log:"
        echo "   tail -50 /workspace/logs/dataset-worker.log"
        echo ""
    else
        echo "✅ EVENT FLOW WORKING"
        echo ""
        echo "   If DPO files still not created, check thresholds:"
        echo "   ./diagnose-dpo-issues.sh"
        echo ""
    fi
fi

