#!/bin/bash

# Demo Questions Script
# Sends test questions to demonstrate the RLVR pipeline

API_URL="${API_URL:-http://localhost:8001}"

echo "╔════════════════════════════════════════════════════════════════════════════╗"
echo "║                    RLVR PIPELINE DEMO - TEST QUESTIONS                     ║"
echo "╔════════════════════════════════════════════════════════════════════════════╗"
echo ""

# Array of demo questions
questions=(
    "What is AWS Lambda and how does it work?"
    "How do I troubleshoot S3 bucket access denied errors?"
    "What are the different AWS Support plan tiers and their benefits?"
    "How do I configure CloudWatch alarms for EC2 monitoring?"
    "What is the difference between Amazon ECS and Amazon EKS?"
)

echo "This script will send ${#questions[@]} questions to the RLVR pipeline."
echo "Each question will generate 3 candidate answers."
echo ""
echo "Make sure you have the monitoring scripts running in separate terminals!"
echo ""
read -p "Press Enter to start sending questions (or Ctrl+C to cancel)..."
echo ""

for i in "${!questions[@]}"; do
    num=$((i+1))
    question="${questions[$i]}"
    
    echo "════════════════════════════════════════════════════════════════════════════"
    echo "Question $num of ${#questions[@]}"
    echo "════════════════════════════════════════════════════════════════════════════"
    echo ""
    echo "Q: $question"
    echo ""
    
    # Send the question
    response=$(curl -s -X POST "$API_URL/ask/multi-candidate" \
        -H 'Content-Type: application/json' \
        -d "{\"question\": \"$question\", \"num_candidates\": 3}")
    
    # Check if successful
    if [ $? -eq 0 ]; then
        echo "✅ Question sent successfully!"
        
        # Try to extract request_id if present
        if command -v jq &> /dev/null; then
            request_id=$(echo "$response" | jq -r '.request_id // empty' 2>/dev/null)
            if [ ! -z "$request_id" ]; then
                echo "📋 Request ID: $request_id"
            fi
        fi
    else
        echo "❌ Failed to send question"
    fi
    
    echo ""
    
    # Wait between questions
    if [ $num -lt ${#questions[@]} ]; then
        echo "Waiting 25 seconds before next question..."
        echo "(This allows time for the pipeline to process)"
        echo ""
        sleep 25
    fi
done

echo "════════════════════════════════════════════════════════════════════════════"
echo "✨ All questions sent!"
echo "════════════════════════════════════════════════════════════════════════════"
echo ""
echo "Watch the monitoring terminals to see the pipeline in action!"
echo ""
echo "After all processing completes, you can view the dashboard:"
echo "  ./rlvr-dashboard.sh --auto"
echo ""

