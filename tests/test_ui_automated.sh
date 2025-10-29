#!/bin/bash

# RLVR Automation Demo - Automated UI Tests
# This script tests the UI functionality without requiring a browser

echo "=========================================="
echo "RLVR Automation Demo - UI Automated Tests"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PASSED=0
FAILED=0

# Test 1: Check if Streamlit UI is running
echo "Test 1: Streamlit UI Accessibility"
echo "-----------------------------------"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8501)
if [ "$HTTP_CODE" == "200" ]; then
    echo -e "${GREEN}✅ PASS${NC}: Streamlit UI is accessible (HTTP $HTTP_CODE)"
    ((PASSED++))
else
    echo -e "${RED}❌ FAIL${NC}: Streamlit UI is not accessible (HTTP $HTTP_CODE)"
    ((FAILED++))
fi
echo ""

# Test 2: Check if API Gateway is running
echo "Test 2: API Gateway Health Check"
echo "---------------------------------"
HEALTH=$(curl -s http://localhost:8000/health 2>&1)
if echo "$HEALTH" | grep -q "healthy"; then
    echo -e "${GREEN}✅ PASS${NC}: API Gateway is healthy"
    ((PASSED++))
else
    echo -e "${RED}❌ FAIL${NC}: API Gateway health check failed"
    echo "Response: $HEALTH"
    ((FAILED++))
fi
echo ""

# Test 3: Check if QA Orchestrator is running
echo "Test 3: QA Orchestrator Health Check"
echo "-------------------------------------"
QA_HEALTH=$(curl -s http://localhost:8001/health 2>&1)
if echo "$QA_HEALTH" | grep -q "healthy"; then
    echo -e "${GREEN}✅ PASS${NC}: QA Orchestrator is healthy"
    ((PASSED++))
else
    echo -e "${RED}❌ FAIL${NC}: QA Orchestrator health check failed"
    echo "Response: $QA_HEALTH"
    ((FAILED++))
fi
echo ""

# Test 4: Test question submission via API
echo "Test 4: Question Submission (API)"
echo "----------------------------------"
QUESTION='{"question": "What is AWS Trusted Advisor?"}'
RESPONSE=$(curl -s -X POST http://localhost:8001/ask \
    -H "Content-Type: application/json" \
    -d "$QUESTION" 2>&1)

if echo "$RESPONSE" | grep -q "answer"; then
    echo -e "${GREEN}✅ PASS${NC}: Question was answered successfully"
    ANSWER_LENGTH=$(echo "$RESPONSE" | python3 -c "import sys, json; d=json.load(sys.stdin); print(len(d['answer']))" 2>/dev/null)
    echo "Answer length: $ANSWER_LENGTH characters"
    ((PASSED++))
else
    echo -e "${RED}❌ FAIL${NC}: Question submission failed"
    echo "Response: ${RESPONSE:0:200}..."
    ((FAILED++))
fi
echo ""

# Test 5: Test Enter key functionality (verify form exists in HTML)
echo "Test 5: Enter Key Support (Form Check)"
echo "---------------------------------------"
HTML=$(curl -s http://localhost:8501)
if echo "$HTML" | grep -q "question_form"; then
    echo -e "${GREEN}✅ PASS${NC}: Form element exists for Enter key support"
    ((PASSED++))
else
    echo -e "${YELLOW}⚠️  WARN${NC}: Form element not found (may need manual verification)"
    ((FAILED++))
fi
echo ""

# Test 6: Check if Qdrant has documents
echo "Test 6: Vector Database Status"
echo "-------------------------------"
QDRANT=$(curl -s http://localhost:6333/collections/documents 2>&1)
if echo "$QDRANT" | grep -q "points_count"; then
    POINTS=$(echo "$QDRANT" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d['result']['points_count'])" 2>/dev/null)
    echo -e "${GREEN}✅ PASS${NC}: Qdrant has $POINTS documents indexed"
    ((PASSED++))
else
    echo -e "${RED}❌ FAIL${NC}: Qdrant collection check failed"
    ((FAILED++))
fi
echo ""

# Test 7: Test multiple questions (chat history)
echo "Test 7: Multiple Questions (Chat History)"
echo "------------------------------------------"
Q1='{"question": "How do I contact AWS Support?"}'
Q2='{"question": "What are the pricing details?"}'

R1=$(curl -s -X POST http://localhost:8001/ask -H "Content-Type: application/json" -d "$Q1" 2>&1)
sleep 2
R2=$(curl -s -X POST http://localhost:8001/ask -H "Content-Type: application/json" -d "$Q2" 2>&1)

if echo "$R1" | grep -q "answer" && echo "$R2" | grep -q "answer"; then
    echo -e "${GREEN}✅ PASS${NC}: Multiple questions answered successfully"
    ((PASSED++))
else
    echo -e "${RED}❌ FAIL${NC}: Multiple question test failed"
    ((FAILED++))
fi
echo ""

# Test 8: Check RabbitMQ connectivity
echo "Test 8: RabbitMQ Event System"
echo "------------------------------"
RABBITMQ=$(curl -s http://localhost:15672/api/overview -u rlvr:rlvr_password 2>&1)
if echo "$RABBITMQ" | grep -q "rabbitmq_version"; then
    echo -e "${GREEN}✅ PASS${NC}: RabbitMQ is running and accessible"
    ((PASSED++))
else
    echo -e "${RED}❌ FAIL${NC}: RabbitMQ check failed"
    ((FAILED++))
fi
echo ""

# Test 9: Check Document Ingestion service
echo "Test 9: Document Ingestion Service"
echo "-----------------------------------"
DOC_HEALTH=$(curl -s http://localhost:8002/health 2>&1)
if echo "$DOC_HEALTH" | grep -q "healthy"; then
    echo -e "${GREEN}✅ PASS${NC}: Document Ingestion service is healthy"
    ((PASSED++))
else
    echo -e "${RED}❌ FAIL${NC}: Document Ingestion health check failed"
    ((FAILED++))
fi
echo ""

# Test 10: Check Training Data service
echo "Test 10: Training Data Service"
echo "-------------------------------"
TRAINING_HEALTH=$(curl -s http://localhost:8005/health 2>&1)
if echo "$TRAINING_HEALTH" | grep -q "healthy"; then
    echo -e "${GREEN}✅ PASS${NC}: Training Data service is healthy"
    ((PASSED++))
else
    echo -e "${RED}❌ FAIL${NC}: Training Data health check failed"
    ((FAILED++))
fi
echo ""

# Summary
echo "=========================================="
echo "Test Summary"
echo "=========================================="
echo -e "Total Tests: $((PASSED + FAILED))"
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}⚠️  Some tests failed. Please review the output above.${NC}"
    exit 1
fi

