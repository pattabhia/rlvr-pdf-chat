#!/bin/bash

# Test Multi-Candidate Answer Generation for DPO Training
# This script demonstrates how to generate multiple candidate answers
# for the same question, which will be scored by RAGAS and used to
# create DPO training pairs.

set -e

echo "🧪 Testing Multi-Candidate Answer Generation for DPO"
echo "=================================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test questions
QUESTIONS=(
    "What is AWS Lambda?"
    "How does Amazon S3 work?"
    "What is EC2?"
)

echo -e "${BLUE}📝 Test Plan:${NC}"
echo "1. Generate 3 candidate answers for each question"
echo "2. Each candidate will be verified by RAGAS worker"
echo "3. Dataset worker will create DPO pairs from candidates with different scores"
echo ""

# Function to generate multi-candidate answers
generate_candidates() {
    local question="$1"
    local num_candidates="${2:-3}"
    
    echo -e "${YELLOW}❓ Question:${NC} $question"
    echo -e "${BLUE}🔄 Generating $num_candidates candidate answers...${NC}"
    
    response=$(curl -s -X POST http://localhost:8001/ask/multi-candidate \
        -H "Content-Type: application/json" \
        -d "{
            \"question\": \"$question\",
            \"num_candidates\": $num_candidates,
            \"publish_events\": true
        }")
    
    # Extract event IDs
    event_ids=$(echo "$response" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    candidates = data.get('candidates', [])
    for i, c in enumerate(candidates):
        event_id = c.get('metadata', {}).get('event_id', 'N/A')
        answer = c.get('answer', '')[:80]
        print(f'  Candidate {i+1}: Event ID = {event_id}')
        print(f'    Answer: {answer}...')
except Exception as e:
    print(f'Error: {e}')
" 2>&1)
    
    echo "$event_ids"
    echo ""
}

# Test 1: Generate candidates for first question
echo -e "${GREEN}=== Test 1: Generate 3 candidates for AWS Lambda ===${NC}"
generate_candidates "${QUESTIONS[0]}" 3
sleep 5

# Test 2: Generate candidates for second question
echo -e "${GREEN}=== Test 2: Generate 3 candidates for Amazon S3 ===${NC}"
generate_candidates "${QUESTIONS[1]}" 3
sleep 5

# Test 3: Generate candidates for third question
echo -e "${GREEN}=== Test 3: Generate 3 candidates for EC2 ===${NC}"
generate_candidates "${QUESTIONS[2]}" 3
sleep 5

echo ""
echo -e "${GREEN}✅ Multi-candidate generation complete!${NC}"
echo ""
echo -e "${BLUE}📊 Next Steps:${NC}"
echo "1. Wait 10-15 seconds for RAGAS verification to complete"
echo "2. Check verification logs:"
echo "   docker logs verification-worker 2>&1 | tail -30"
echo ""
echo "3. Check DPO pair creation:"
echo "   docker logs dataset-generation-worker 2>&1 | grep 'DPO:'"
echo ""
echo "4. View DPO data files:"
echo "   ls -la data/dpo_data/"
echo "   cat data/dpo_data/dpo_data_*.jsonl | jq ."
echo ""
echo -e "${YELLOW}💡 Expected Outcome:${NC}"
echo "- Each question has 3 candidate answers"
echo "- RAGAS will score each candidate differently (due to LLM sampling variation)"
echo "- Dataset worker will create DPO pairs: best answer (chosen) vs worst answer (rejected)"
echo "- DPO files will appear in data/dpo_data/ directory"
echo ""
echo "Wait 15 seconds and then check the results..."
sleep 15

echo ""
echo -e "${BLUE}📈 Checking Results...${NC}"
echo ""

# Check verification logs
echo -e "${GREEN}=== Verification Worker Logs ===${NC}"
docker logs verification-worker 2>&1 | grep -E "Received|overall_score|Verification completed" | tail -20

echo ""
echo -e "${GREEN}=== Dataset Worker DPO Logs ===${NC}"
docker logs dataset-generation-worker 2>&1 | grep "DPO:" | tail -20

echo ""
echo -e "${GREEN}=== DPO Data Files ===${NC}"
ls -lah data/dpo_data/ 2>/dev/null || echo "No DPO files yet - may need more time or score differences"

echo ""
echo -e "${GREEN}✅ Test Complete!${NC}"

