#!/bin/bash

# Test script for DPO quality improvements
# Tests 3 questions and monitors DPO file generation

echo "=========================================="
echo "DPO QUALITY IMPROVEMENT TEST"
echo "=========================================="
echo ""

# Question 1
echo "📝 Testing Question 1: AWS Lambda cold starts"
curl -s -X POST "http://localhost:8001/ask/multi-candidate" \
  -H "Content-Type: application/json" \
  -d '{"question": "How do I optimize AWS Lambda cold starts?", "publish_events": true}' \
  > /tmp/test_q1.json

echo "✅ Question 1 completed"
echo ""

# Question 2
echo "📝 Testing Question 2: S3 bucket security"
curl -s -X POST "http://localhost:8001/ask/multi-candidate" \
  -H "Content-Type: application/json" \
  -d '{"question": "What are best practices for S3 bucket security?", "publish_events": true}' \
  > /tmp/test_q2.json

echo "✅ Question 2 completed"
echo ""

# Question 3
echo "📝 Testing Question 3: EC2 cost reduction"
curl -s -X POST "http://localhost:8001/ask/multi-candidate" \
  -H "Content-Type: application/json" \
  -d '{"question": "How do I reduce EC2 costs?", "publish_events": true}' \
  > /tmp/test_q3.json

echo "✅ Question 3 completed"
echo ""

echo "=========================================="
echo "SUMMARY"
echo "=========================================="
echo ""

# Show summary of all 3 questions
for i in 1 2 3; do
  echo "Question $i:"
  cat /tmp/test_q$i.json | jq -r '.question'
  echo "  Candidates: $(cat /tmp/test_q$i.json | jq -r '.num_candidates')"
  echo "  Events published: $(cat /tmp/test_q$i.json | jq -r '.events_published')"
  echo "  Temperatures: $(cat /tmp/test_q$i.json | jq -r '[.candidates[].metadata.temperature] | join(", ")')"
  echo ""
done

echo "=========================================="
echo "WAITING FOR RAGAS VERIFICATION"
echo "=========================================="
echo ""
echo "⏳ Waiting 10 minutes for RAGAS verification to complete..."
echo "   (9 candidates × ~2-3 min each = ~18-27 minutes total)"
echo ""
echo "   You can monitor progress with:"
echo "   docker logs -f dataset-generation-worker"
echo ""
echo "   After verification completes, check DPO files with:"
echo "   cat data/dpo_data/dpo_data_202512.jsonl | jq -c '{question: .prompt[:60], chosen_score: .metadata.chosen_score, rejected_score: .metadata.rejected_score, score_diff: .metadata.score_difference}'"
echo ""

