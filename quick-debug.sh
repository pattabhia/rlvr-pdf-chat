#!/bin/bash

# Quick Debug - Find out what's wrong

echo "╔════════════════════════════════════════════════════════════════════════════╗"
echo "║                    QUICK DEBUG - WHAT'S WRONG?                             ║"
echo "╔════════════════════════════════════════════════════════════════════════════╗"
echo ""

LOG_DIR="${LOG_DIR:-/workspace/logs}"
DATA_DIR="${DATA_DIR:-/workspace/rlvr-automation/data}"

# 1. Check if workers are running
echo "1. Checking if workers are running..."
echo "────────────────────────────────────────────────────────────────────────────"
ps aux | grep -E "qa-orchestrator|verification-worker|dataset.*worker" | grep -v grep
if [ $? -eq 0 ]; then
    echo "✅ Workers are running"
else
    echo "❌ NO WORKERS RUNNING!"
    echo ""
    echo "FIX: Run this command:"
    echo "  ./runpod-start.sh"
    echo ""
fi
echo ""

# 2. Check if log files exist
echo "2. Checking if log files exist..."
echo "────────────────────────────────────────────────────────────────────────────"
if [ -f "$LOG_DIR/qa-orchestrator.log" ]; then
    echo "✅ qa-orchestrator.log exists"
    lines=$(wc -l < "$LOG_DIR/qa-orchestrator.log")
    echo "   Lines: $lines"
else
    echo "❌ qa-orchestrator.log NOT FOUND"
fi

if [ -f "$LOG_DIR/verification-worker.log" ]; then
    echo "✅ verification-worker.log exists"
    lines=$(wc -l < "$LOG_DIR/verification-worker.log")
    echo "   Lines: $lines"
else
    echo "❌ verification-worker.log NOT FOUND"
fi

if [ -f "$LOG_DIR/dataset-worker.log" ]; then
    echo "✅ dataset-worker.log exists"
    lines=$(wc -l < "$LOG_DIR/dataset-worker.log")
    echo "   Lines: $lines"
else
    echo "❌ dataset-worker.log NOT FOUND"
fi
echo ""

# 3. Check recent activity
echo "3. Checking recent activity (last 2 minutes)..."
echo "────────────────────────────────────────────────────────────────────────────"
if [ -f "$LOG_DIR/qa-orchestrator.log" ]; then
    recent=$(find "$LOG_DIR/qa-orchestrator.log" -mmin -2 2>/dev/null)
    if [ ! -z "$recent" ]; then
        echo "✅ QA Orchestrator has recent activity"
        echo "   Last 5 lines:"
        tail -5 "$LOG_DIR/qa-orchestrator.log" | sed 's/^/   /'
    else
        echo "⚠️  QA Orchestrator - no activity in last 2 minutes"
    fi
else
    echo "❌ No QA Orchestrator log"
fi
echo ""

# 4. Check if UI is accessible
echo "4. Checking if services are accessible..."
echo "────────────────────────────────────────────────────────────────────────────"
if command -v curl &> /dev/null; then
    # Check QA service
    response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/health 2>/dev/null || echo "000")
    if [ "$response" = "200" ]; then
        echo "✅ QA Service (port 8001) is UP"
    else
        echo "❌ QA Service (port 8001) is DOWN (HTTP $response)"
    fi
    
    # Check UI
    response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 2>/dev/null || echo "000")
    if [ "$response" = "200" ]; then
        echo "✅ UI (port 3000) is UP"
    else
        echo "⚠️  UI (port 3000) - HTTP $response"
    fi
else
    echo "⚠️  curl not available, skipping service checks"
fi
echo ""

# 5. Check RabbitMQ
echo "5. Checking RabbitMQ..."
echo "────────────────────────────────────────────────────────────────────────────"
if command -v rabbitmqctl &> /dev/null; then
    rabbitmqctl list_queues 2>/dev/null | head -10
    if [ $? -eq 0 ]; then
        echo "✅ RabbitMQ is running"
    else
        echo "❌ RabbitMQ is NOT running"
    fi
else
    echo "⚠️  rabbitmqctl not available"
fi
echo ""

# 6. Check data directory
echo "6. Checking data directory..."
echo "────────────────────────────────────────────────────────────────────────────"
if [ -d "$DATA_DIR" ]; then
    echo "✅ Data directory exists: $DATA_DIR"
    
    # Check training data
    if [ -d "$DATA_DIR/training_data" ]; then
        count=$(find "$DATA_DIR/training_data" -name "*.jsonl" -type f 2>/dev/null | wc -l)
        echo "   Training files: $count"
    fi
    
    # Check DPO data
    if [ -d "$DATA_DIR/dpo" ]; then
        count=$(find "$DATA_DIR/dpo" -name "*.json" -type f 2>/dev/null | wc -l)
        echo "   DPO files: $count"
    fi
else
    echo "❌ Data directory NOT FOUND: $DATA_DIR"
fi
echo ""

# 7. Show what to do next
echo "════════════════════════════════════════════════════════════════════════════"
echo "  WHAT TO DO NEXT"
echo "════════════════════════════════════════════════════════════════════════════"
echo ""

# Determine the issue
workers_running=$(ps aux | grep -E "qa-orchestrator|verification-worker|dataset.*worker" | grep -v grep | wc -l)

if [ $workers_running -eq 0 ]; then
    echo "❌ PROBLEM: Workers are not running!"
    echo ""
    echo "FIX:"
    echo "  1. Start the workers:"
    echo "     ./runpod-start.sh"
    echo ""
    echo "  2. Wait 10 seconds for them to start"
    echo ""
    echo "  3. Try your query again in the UI"
    echo ""
    echo "  4. Run the watcher:"
    echo "     ./watch-pipeline.sh"
    echo ""
else
    echo "✅ Workers are running"
    echo ""
    echo "Try this:"
    echo "  1. Run the watcher in one terminal:"
    echo "     ./watch-pipeline.sh"
    echo ""
    echo "  2. In another terminal, send a test query:"
    echo "     curl -X POST http://localhost:8001/ask/multi-candidate \\"
    echo "       -H 'Content-Type: application/json' \\"
    echo "       -d '{\"question\": \"What is AWS Lambda?\", \"num_candidates\": 3}'"
    echo ""
    echo "  3. Watch the first terminal for output"
    echo ""
    echo "If still nothing shows up, check the logs manually:"
    echo "  tail -f $LOG_DIR/qa-orchestrator.log"
    echo ""
fi

