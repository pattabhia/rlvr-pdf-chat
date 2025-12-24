#!/bin/bash

# Generate DPO samples by asking diverse questions

QA_URL="${QA_URL:-http://localhost:8001}"
LOG_DIR="${LOG_DIR:-/workspace/logs}"

echo "════════════════════════════════════════════════════════════════════════════"
echo "  GENERATING DPO SAMPLES"
echo "════════════════════════════════════════════════════════════════════════════"
echo ""
echo "This will send 10 diverse questions to generate DPO training pairs."
echo "Each question will generate 3 candidate answers with different temperatures."
echo ""
echo "DPO Requirements:"
echo "  • Score difference ≥ 0.3 between best and worst"
echo "  • Best score ≥ 0.7"
echo ""

# Array of diverse questions that should produce good answers
questions=(
    "What is AWS Lambda and how does it differ from EC2?"
    "Explain the CAP theorem in distributed systems."
    "What are the main differences between SQL and NoSQL databases?"
    "How does Docker containerization work?"
    "What is the difference between authentication and authorization?"
    "Explain how HTTPS encryption works."
    "What is the purpose of a load balancer in web architecture?"
    "How does Git branching and merging work?"
    "What is the difference between REST and GraphQL APIs?"
    "Explain the concept of microservices architecture."
)

total=${#questions[@]}
success=0
failed=0

for i in "${!questions[@]}"; do
    num=$((i + 1))
    question="${questions[$i]}"
    
    echo "────────────────────────────────────────────────────────────────────────────"
    echo "[$num/$total] Asking: $question"
    echo "────────────────────────────────────────────────────────────────────────────"
    
    # Send the question
    response=$(curl -s -X POST "$QA_URL/ask/multi-candidate" \
        -H 'Content-Type: application/json' \
        -d "{\"question\": \"$question\", \"num_candidates\": 3}" \
        2>&1)
    
    if [ $? -eq 0 ]; then
        echo "✅ Question sent successfully"
        ((success++))
    else
        echo "❌ Failed to send question"
        echo "   Error: $response"
        ((failed++))
    fi
    
    # Wait a bit between questions to avoid overwhelming the system
    if [ $num -lt $total ]; then
        echo "   Waiting 5 seconds before next question..."
        sleep 5
    fi
    echo ""
done

echo "════════════════════════════════════════════════════════════════════════════"
echo "  QUESTIONS SENT"
echo "════════════════════════════════════════════════════════════════════════════"
echo ""
echo "Summary:"
echo "  • Total questions: $total"
echo "  • Successful: $success"
echo "  • Failed: $failed"
echo ""
echo "Now waiting 60 seconds for RAGAS verification to complete..."
echo "(RAGAS needs time to verify all 30 candidate answers)"
echo ""

# Show a progress bar
for i in {1..60}; do
    printf "\rProgress: [%-60s] %d/60s" $(printf '#%.0s' $(seq 1 $i)) $i
    sleep 1
done
echo ""
echo ""

echo "════════════════════════════════════════════════════════════════════════════"
echo "  CHECKING RESULTS"
echo "════════════════════════════════════════════════════════════════════════════"
echo ""

# Check verification scores
echo "1. Recent Verification Scores:"
echo "────────────────────────────────────────────────────────────────────────────"
strings "$LOG_DIR/verification-worker.log" 2>/dev/null | grep "Verification complete" | tail -15
echo ""

# Check DPO analysis
echo "2. DPO Score Analysis:"
echo "────────────────────────────────────────────────────────────────────────────"
strings "$LOG_DIR/dataset-worker.log" 2>/dev/null | grep "DPO:" | tail -10
echo ""

# Check DPO files
echo "3. DPO Files Created:"
echo "────────────────────────────────────────────────────────────────────────────"
dpo_dir="/workspace/rlvr-automation/data/dpo"
dpo_count=$(find "$dpo_dir" -name "*.jsonl" -type f 2>/dev/null | wc -l)

if [ $dpo_count -gt 0 ]; then
    echo "✅ Found $dpo_count DPO file(s)!"
    echo ""
    
    for file in $(find "$dpo_dir" -name "*.jsonl" -type f 2>/dev/null | sort); do
        lines=$(wc -l < "$file" 2>/dev/null)
        size=$(ls -lh "$file" | awk '{print $5}')
        echo "   📄 $(basename $file)"
        echo "      • DPO pairs: $lines"
        echo "      • Size: $size"
        echo ""
    done
    
    # Show a sample DPO pair
    latest=$(find "$dpo_dir" -name "*.jsonl" -type f 2>/dev/null | sort | tail -1)
    echo "   Sample DPO pair from latest file:"
    echo "   ────────────────────────────────────────────────────────────────────"
    tail -1 "$latest" | python3 -m json.tool 2>/dev/null | head -30
    echo ""
else
    echo "❌ No DPO files created yet"
    echo ""
    echo "Possible reasons:"
    echo "  • Score differences < 0.3 (need more variance)"
    echo "  • Best scores < 0.7 (answers not good enough)"
    echo "  • Still processing (check logs in a minute)"
    echo ""
    echo "Check the DPO analysis above to see why pairs were rejected."
    echo ""
fi

echo "════════════════════════════════════════════════════════════════════════════"
echo "  DONE"
echo "════════════════════════════════════════════════════════════════════════════"
echo ""
echo "To check status again:"
echo "  ./check-if-fixed.sh"
echo ""
echo "To view full logs:"
echo "  tail -f $LOG_DIR/verification-worker.log"
echo "  tail -f $LOG_DIR/dataset-worker.log"
echo ""

