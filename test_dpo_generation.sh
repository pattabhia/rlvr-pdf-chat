#!/bin/bash

# Test DPO Generation - Quick verification script
# This script tests the complete DPO data generation pipeline

set -e

echo "============================================================"
echo "🧪 DPO Generation Test"
echo "============================================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test question
QUESTION="What is AWS Lambda?"

echo "Step 1: Restarting services to ensure clean state..."
cd infrastructure
docker compose restart qa-orchestrator verification-worker dataset-generation-worker > /dev/null 2>&1
cd ..
sleep 5
echo -e "${GREEN}✅ Services restarted${NC}"
echo ""

echo "Step 2: Asking the same question 3 times to generate DPO pairs..."
for i in 1 2 3; do
    echo "  Question $i/3..."
    RESPONSE=$(curl -s -X POST http://localhost:8001/ask \
        -H "Content-Type: application/json" \
        -d "{\"question\": \"$QUESTION\"}")
    
    if [ $? -eq 0 ]; then
        echo -e "  ${GREEN}✅ Answer $i received${NC}"
    else
        echo -e "  ${RED}❌ Failed to get answer $i${NC}"
        exit 1
    fi
    
    sleep 3
done
echo ""

echo "Step 3: Waiting 30 seconds for events to process..."
sleep 30
echo -e "${GREEN}✅ Wait complete${NC}"
echo ""

echo "Step 4: Checking training data..."
if [ -f data/training_data/training_data_$(date +%Y%m).jsonl ]; then
    TRAINING_COUNT=$(wc -l < data/training_data/training_data_$(date +%Y%m).jsonl)
    echo -e "${GREEN}✅ Training data exists: $TRAINING_COUNT entries${NC}"
else
    echo -e "${YELLOW}⚠️  No training data found${NC}"
fi
echo ""

echo "Step 5: Checking DPO data..."
if [ -f data/dpo_data/dpo_data_$(date +%Y%m).jsonl ]; then
    DPO_COUNT=$(wc -l < data/dpo_data/dpo_data_$(date +%Y%m).jsonl)
    echo -e "${GREEN}✅ DPO data exists: $DPO_COUNT pairs${NC}"
    echo ""
    echo "Sample DPO pair:"
    cat data/dpo_data/dpo_data_$(date +%Y%m).jsonl | head -1 | python3 -c "
import sys, json
entry = json.load(sys.stdin)
print(f\"  Prompt: {entry['prompt'][:60]}...\")
print(f\"  Chosen score: {entry['metadata']['chosen_score']:.3f}\")
print(f\"  Rejected score: {entry['metadata']['rejected_score']:.3f}\")
print(f\"  Score difference: {entry['metadata']['score_difference']:.3f}\")
"
else
    echo -e "${YELLOW}⚠️  No DPO data found yet${NC}"
    echo ""
    echo "Checking logs for issues..."
    echo ""
    echo "Dataset Generation Worker logs:"
    docker logs dataset-generation-worker 2>&1 | grep -E "Complete entry|DPO|error" | tail -10
    echo ""
    echo "QA Orchestrator logs:"
    docker logs qa-orchestrator 2>&1 | grep -E "Published|error" | tail -10
fi
echo ""

echo "============================================================"
echo "Test Complete!"
echo "============================================================"
echo ""
echo "Next steps:"
echo "1. If DPO data was created: ✅ System is ready for RunPod!"
echo "2. If no DPO data: Check logs above for errors"
echo "3. Common fix: Restart services and try again"
echo ""

