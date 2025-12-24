#!/bin/bash

# Debug DPO logic to see what's happening

LOG_DIR="${LOG_DIR:-/workspace/logs}"

echo "════════════════════════════════════════════════════════════════════════════"
echo "  DEBUGGING DPO LOGIC"
echo "════════════════════════════════════════════════════════════════════════════"
echo ""

echo "1. Check how many answers per question:"
echo "────────────────────────────────────────────────────────────────────────────"
strings "$LOG_DIR/dataset-worker.log" 2>/dev/null | grep "DPO: Question" | tail -20
echo ""

echo "2. Check for 'Only X answer(s)' messages:"
echo "────────────────────────────────────────────────────────────────────────────"
strings "$LOG_DIR/dataset-worker.log" 2>/dev/null | grep "Only.*answer" | tail -20
echo ""

echo "3. Check for quality gate rejections:"
echo "────────────────────────────────────────────────────────────────────────────"
echo "Low score diff:"
strings "$LOG_DIR/dataset-worker.log" 2>/dev/null | grep "Score diff too small" | tail -10
echo ""
echo "Low chosen score:"
strings "$LOG_DIR/dataset-worker.log" 2>/dev/null | grep "Chosen score too low" | tail -10
echo ""
echo "Failed verbatim test:"
strings "$LOG_DIR/dataset-worker.log" 2>/dev/null | grep "failed verbatim test" | tail -10
echo ""

echo "4. Check for successful DPO pairs:"
echo "────────────────────────────────────────────────────────────────────────────"
strings "$LOG_DIR/dataset-worker.log" 2>/dev/null | grep "Created HIGH-QUALITY DPO pair" | tail -10
echo ""

echo "5. Check complete entries:"
echo "────────────────────────────────────────────────────────────────────────────"
strings "$LOG_DIR/dataset-worker.log" 2>/dev/null | grep "Complete entry" | tail -20
echo ""

echo "════════════════════════════════════════════════════════════════════════════"
echo "  ANALYSIS"
echo "════════════════════════════════════════════════════════════════════════════"
echo ""
echo "The DPO writer should:"
echo "  1. Receive 3 complete entries for the same question"
echo "  2. Group them by question"
echo "  3. Create DPO pairs if score diff ≥ 0.3 and best score ≥ 0.7"
echo ""
echo "If you see 'Only 1 answer(s)' repeatedly, it means the DPO writer"
echo "is trying to create pairs BEFORE all 3 candidates are verified."
echo ""

