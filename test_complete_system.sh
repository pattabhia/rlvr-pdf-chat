#!/bin/bash

# Complete System Test - RLVR PDF Chat
# Tests all components before RunPod deployment

set -e

echo "============================================================"
echo "🧪 RLVR PDF Chat - Complete System Test"
echo "============================================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Helper functions
pass() {
    echo -e "${GREEN}✅ PASS${NC}: $1"
    ((TESTS_PASSED++))
}

fail() {
    echo -e "${RED}❌ FAIL${NC}: $1"
    ((TESTS_FAILED++))
}

info() {
    echo -e "${YELLOW}ℹ️  INFO${NC}: $1"
}

# Test 1: Check all services are running
echo "Test 1: Checking all services..."
REQUIRED_SERVICES=(
    "rabbitmq-eventbus"
    "qdrant-vectordb"
    "postgres-groundtruth"
    "ollama-service"
    "api-gateway"
    "qa-orchestrator"
    "document-ingestion"
    "verification-worker"
    "reward-computation-worker"
    "dataset-generation-worker"
    "training-data"
    "ground-truth"
    "streamlit-ui"
)

for service in "${REQUIRED_SERVICES[@]}"; do
    if docker ps --format '{{.Names}}' | grep -q "^${service}$"; then
        pass "Service running: $service"
    else
        fail "Service NOT running: $service"
    fi
done

echo ""

# Test 2: Check API endpoints
echo "Test 2: Checking API endpoints..."

# API Gateway health
if curl -s http://localhost:8000/health | grep -q "healthy"; then
    pass "API Gateway health check"
else
    fail "API Gateway health check"
fi

# QA Orchestrator health
if curl -s http://localhost:8001/health | grep -q "healthy"; then
    pass "QA Orchestrator health check"
else
    fail "QA Orchestrator health check"
fi

# Document Ingestion health
if curl -s http://localhost:8002/health | grep -q "healthy"; then
    pass "Document Ingestion health check"
else
    fail "Document Ingestion health check"
fi

# Training Data health
if curl -s http://localhost:8005/health | grep -q "healthy"; then
    pass "Training Data health check"
else
    fail "Training Data health check"
fi

echo ""

# Test 3: Check Qdrant vector database
echo "Test 3: Checking Qdrant vector database..."
COLLECTION_INFO=$(curl -s http://localhost:6333/collections/documents)
if echo "$COLLECTION_INFO" | grep -q "points_count"; then
    POINTS=$(echo "$COLLECTION_INFO" | python3 -c "import sys, json; print(json.load(sys.stdin)['result']['points_count'])")
    pass "Qdrant collection exists with $POINTS documents"
else
    fail "Qdrant collection check"
fi

echo ""

# Test 4: Ask a question and verify response
echo "Test 4: Testing question answering..."
QUESTION="What is AWS Trusted Advisor?"
RESPONSE=$(curl -s -X POST http://localhost:8001/ask \
    -H "Content-Type: application/json" \
    -d "{\"question\": \"$QUESTION\"}")

if echo "$RESPONSE" | grep -q "answer"; then
    pass "Question answering works"
    info "Question: $QUESTION"
    ANSWER=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['answer'][:100])")
    info "Answer: $ANSWER..."
else
    fail "Question answering"
fi

echo ""

# Test 5: Wait for events to process
echo "Test 5: Waiting for event processing (5 seconds)..."
sleep 5
pass "Event processing wait complete"

echo ""

# Test 6: Check training data was created
echo "Test 6: Checking training data generation..."
if [ -f "data/training_data/training_data_$(date +%Y%m).jsonl" ]; then
    ENTRIES=$(wc -l < "data/training_data/training_data_$(date +%Y%m).jsonl")
    pass "Training data file exists with $ENTRIES entries"
else
    fail "Training data file not found"
fi

echo ""

# Test 7: Check DPO data generation
echo "Test 7: Checking DPO data generation..."
if [ -d "data/dpo_data" ]; then
    pass "DPO data directory exists"
    if [ -f "data/dpo_data/dpo_data_$(date +%Y%m).jsonl" ]; then
        DPO_ENTRIES=$(wc -l < "data/dpo_data/dpo_data_$(date +%Y%m).jsonl")
        pass "DPO data file exists with $DPO_ENTRIES pairs"
    else
        info "DPO data file not yet created (need multiple answers per question)"
    fi
else
    fail "DPO data directory not found"
fi

echo ""

# Summary
echo "============================================================"
echo "📊 Test Summary"
echo "============================================================"
echo -e "${GREEN}Passed: $TESTS_PASSED${NC}"
echo -e "${RED}Failed: $TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 All tests passed! System is ready for RunPod deployment.${NC}"
    exit 0
else
    echo -e "${RED}⚠️  Some tests failed. Please fix issues before deploying.${NC}"
    exit 1
fi

