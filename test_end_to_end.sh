#!/bin/bash

echo "=========================================="
echo "🧪 RLVR Automation - End-to-End Test"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
PASSED=0
FAILED=0

# Helper function
test_endpoint() {
    local name=$1
    local url=$2
    local expected=$3
    
    echo -n "Testing $name... "
    response=$(curl -s "$url" 2>&1)
    
    if echo "$response" | grep -q "$expected"; then
        echo -e "${GREEN}✅ PASS${NC}"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}❌ FAIL${NC}"
        echo "  Expected: $expected"
        echo "  Got: $response"
        ((FAILED++))
        return 1
    fi
}

echo "📋 Test Suite: Core Services"
echo "=========================================="

# Test 1: API Gateway Health
test_endpoint "API Gateway Health" "http://localhost:8000/health" "healthy"

# Test 2: QA Orchestrator Health
test_endpoint "QA Orchestrator Health" "http://localhost:8001/health" "healthy"

# Test 3: Document Ingestion Health
test_endpoint "Document Ingestion Health" "http://localhost:8002/health" "healthy"

# Test 4: Training Data Service Health
test_endpoint "Training Data Service Health" "http://localhost:8005/health" "healthy"

# Test 5: Ground Truth Service Health
test_endpoint "Ground Truth Service Health" "http://localhost:8007/health" "healthy"

# Test 6: Streamlit UI
echo -n "Testing Streamlit UI... "
if curl -sf http://localhost:8501 > /dev/null 2>&1; then
    echo -e "${GREEN}✅ PASS${NC}"
    ((PASSED++))
else
    echo -e "${RED}❌ FAIL${NC}"
    ((FAILED++))
fi

# Test 7: Qdrant Vector DB
test_endpoint "Qdrant Vector DB" "http://localhost:6333/dashboard" "Qdrant"

# Test 8: RabbitMQ
echo -n "Testing RabbitMQ... "
if curl -sf http://localhost:15672 > /dev/null 2>&1; then
    echo -e "${GREEN}✅ PASS${NC}"
    ((PASSED++))
else
    echo -e "${RED}❌ FAIL${NC}"
    ((FAILED++))
fi

echo ""
echo "📋 Test Suite: Vector Database"
echo "=========================================="

# Test 9: Collection Info
echo -n "Testing Collection Info... "
collection_info=$(curl -s http://localhost:8002/collection/info 2>&1)
if echo "$collection_info" | grep -q "collection_name"; then
    echo -e "${GREEN}✅ PASS${NC}"
    dimension=$(echo "$collection_info" | python3 -c "import sys, json; print(json.load(sys.stdin)['vector_dimension'])" 2>/dev/null)
    points=$(echo "$collection_info" | python3 -c "import sys, json; print(json.load(sys.stdin)['points_count'])" 2>/dev/null)
    echo "  Dimension: $dimension"
    echo "  Documents: $points"
    ((PASSED++))
else
    echo -e "${RED}❌ FAIL${NC}"
    ((FAILED++))
fi

echo ""
echo "📋 Test Suite: Question Answering"
echo "=========================================="

# Test 10: Ask a question
echo "Testing Question Answering..."
echo "  Question: 'What is AWS Support?'"
echo -n "  Sending request... "

start_time=$(date +%s)
answer_response=$(curl -s -X POST http://localhost:8001/ask \
    -H "Content-Type: application/json" \
    -d '{"question": "What is AWS Support?"}' 2>&1)
end_time=$(date +%s)
duration=$((end_time - start_time))

if echo "$answer_response" | grep -q "answer"; then
    echo -e "${GREEN}✅ PASS${NC}"
    echo "  Response time: ${duration}s"
    
    # Extract answer
    answer=$(echo "$answer_response" | python3 -c "import sys, json; print(json.load(sys.stdin)['answer'][:100])" 2>/dev/null)
    echo "  Answer preview: $answer..."
    
    # Extract scores
    scores=$(echo "$answer_response" | python3 -c "import sys, json; d=json.load(sys.stdin); print([s['score'] for s in d.get('sources', [])])" 2>/dev/null)
    echo "  Retrieval scores: $scores"
    
    ((PASSED++))
else
    echo -e "${RED}❌ FAIL${NC}"
    echo "  Response: $answer_response"
    ((FAILED++))
fi

echo ""
echo "📋 Test Suite: Training Data"
echo "=========================================="

# Test 11: Check training data
echo -n "Testing Training Data Collection... "
sleep 3  # Wait for async processing

training_data=$(curl -s http://localhost:8005/entries?limit=1 2>&1)
if echo "$training_data" | grep -q "question"; then
    echo -e "${GREEN}✅ PASS${NC}"
    count=$(echo "$training_data" | python3 -c "import sys, json; print(len(json.load(sys.stdin)))" 2>/dev/null)
    echo "  Total entries: $count"
    ((PASSED++))
else
    echo -e "${YELLOW}⚠️  SKIP${NC} (No training data yet)"
fi

# Test 12: Check JSONL file
echo -n "Testing JSONL File... "
if [ -f "data/training_data/training_data_$(date +%Y%m).jsonl" ]; then
    echo -e "${GREEN}✅ PASS${NC}"
    lines=$(wc -l < "data/training_data/training_data_$(date +%Y%m).jsonl")
    echo "  Lines in file: $lines"
    ((PASSED++))
else
    echo -e "${YELLOW}⚠️  SKIP${NC} (File not created yet)"
fi

echo ""
echo "=========================================="
echo "📊 Test Results Summary"
echo "=========================================="
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed!${NC}"
    echo ""
    echo "🎯 System is ready for deployment!"
    echo ""
    echo "Next steps:"
    echo "  1. Upload your PDF via UI: http://localhost:8501"
    echo "  2. Build Docker image: docker build -f Dockerfile.runpod -t your-username/rlvr-automation ."
    echo "  3. Push to Docker Hub: docker push your-username/rlvr-automation"
    echo "  4. Deploy on RunPod: See RUNPOD_QUICK_START.md"
    exit 0
else
    echo -e "${RED}❌ Some tests failed!${NC}"
    echo ""
    echo "Please fix the issues before deploying to RunPod."
    exit 1
fi

