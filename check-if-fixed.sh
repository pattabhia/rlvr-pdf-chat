#!/bin/bash

# Check if the verification fix is working

LOG_DIR="${LOG_DIR:-/workspace/logs}"
DATA_DIR="${DATA_DIR:-/workspace/rlvr-automation/data}"

echo "════════════════════════════════════════════════════════════════════════════"
echo "  CHECKING IF VERIFICATION FIX IS WORKING"
echo "════════════════════════════════════════════════════════════════════════════"
echo ""

echo "1. Recent Verification Scores (last 10):"
echo "────────────────────────────────────────────────────────────────────────────"
# Use -a to force text mode, or strings to handle binary
strings "$LOG_DIR/verification-worker.log" 2>/dev/null | grep "Verification complete" | tail -10 || \
grep -a "Verification complete" "$LOG_DIR/verification-worker.log" 2>/dev/null | tail -10 || \
echo "Could not read verification log"
echo ""

echo "2. DPO Score Analysis (last 10):"
echo "────────────────────────────────────────────────────────────────────────────"
strings "$LOG_DIR/dataset-worker.log" 2>/dev/null | grep "DPO:" | tail -10 || \
grep -a "DPO:" "$LOG_DIR/dataset-worker.log" 2>/dev/null | tail -10 || \
echo "Could not read dataset log"
echo ""

echo "3. Checking for the 0.675 fallback score pattern:"
echo "────────────────────────────────────────────────────────────────────────────"
fallback_count=$(strings "$LOG_DIR/dataset-worker.log" 2>/dev/null | grep "score diff: 0.000 (best=0.675, worst=0.675)" | wc -l)
echo "   Found $fallback_count instances of fallback score (0.675)"

if [ $fallback_count -gt 0 ]; then
    echo "   ⚠️  Still seeing fallback scores!"
    echo ""
    echo "   Last fallback occurrence:"
    strings "$LOG_DIR/dataset-worker.log" 2>/dev/null | grep "score diff: 0.000 (best=0.675, worst=0.675)" | tail -1
    echo ""
fi
echo ""

echo "4. Checking for VARIED scores (non-zero diff):"
echo "────────────────────────────────────────────────────────────────────────────"
varied_scores=$(strings "$LOG_DIR/dataset-worker.log" 2>/dev/null | grep "score diff:" | grep -v "score diff: 0.000" | tail -5)

if [ -z "$varied_scores" ]; then
    echo "   ❌ NO VARIED SCORES FOUND!"
    echo "   All scores are still identical (0.675)"
    echo ""
    echo "   This means the verification worker is still using the old code."
    echo "   Did you restart it with: ./force-restart-verification.sh ?"
    echo ""
else
    echo "   ✅ FOUND VARIED SCORES!"
    echo ""
    echo "$varied_scores"
    echo ""
fi
echo ""

echo "5. DPO Files Created:"
echo "────────────────────────────────────────────────────────────────────────────"
dpo_count=$(find "$DATA_DIR/dpo" -name "*.jsonl" -type f 2>/dev/null | wc -l)
echo "   Total DPO files: $dpo_count"

if [ $dpo_count -gt 0 ]; then
    echo ""
    echo "   ✅ DPO FILES EXIST!"
    echo ""
    latest=$(find "$DATA_DIR/dpo" -name "*.jsonl" -type f 2>/dev/null | sort | tail -1)
    echo "   Latest file: $latest"
    lines=$(wc -l < "$latest" 2>/dev/null)
    echo "   Number of DPO pairs: $lines"
    echo ""
    echo "   Last DPO pair:"
    tail -1 "$latest" | python3 -m json.tool 2>/dev/null | head -20
else
    echo ""
    echo "   ❌ NO DPO FILES YET"
    echo ""
fi
echo ""

echo "════════════════════════════════════════════════════════════════════════════"
echo "  DIAGNOSIS"
echo "════════════════════════════════════════════════════════════════════════════"
echo ""

# Check if we have varied scores
if [ ! -z "$varied_scores" ]; then
    echo "✅ FIX IS WORKING!"
    echo "   - Scores are varying (not all 0.675)"
    echo "   - RAGAS verification is working properly"
    echo ""
    
    if [ $dpo_count -eq 0 ]; then
        echo "   But no DPO files yet because:"
        echo "   - Score differences might be < 0.3"
        echo "   - Or best score might be < 0.7"
        echo ""
        echo "   Try asking more diverse questions!"
        echo ""
    else
        echo "   ✅ AND DPO FILES ARE BEING CREATED!"
        echo ""
        echo "   🎉 EVERYTHING IS WORKING!"
        echo ""
    fi
else
    echo "❌ FIX NOT WORKING YET"
    echo "   - All scores are still 0.675 (fallback)"
    echo "   - RAGAS verification is still failing"
    echo ""
    echo "   Actions:"
    echo "   1. Restart verification worker:"
    echo "      ./force-restart-verification.sh"
    echo ""
    echo "   2. Send a NEW query (not an old one):"
    echo "      curl -X POST http://localhost:8001/ask/multi-candidate \\"
    echo "        -H 'Content-Type: application/json' \\"
    echo "        -d '{\"question\": \"What is AWS Lambda?\", \"num_candidates\": 3}'"
    echo ""
    echo "   3. Wait 20 seconds and run this script again:"
    echo "      ./check-if-fixed.sh"
    echo ""
fi

