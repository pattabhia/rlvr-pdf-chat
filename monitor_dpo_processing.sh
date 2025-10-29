#!/bin/bash

# Monitor DPO processing in real-time
# Usage: ./monitor_dpo_processing.sh

echo "🔍 DPO Processing Monitor - Started at $(date '+%H:%M:%S')"
echo "=================================================="
echo ""

while true; do
    clear
    echo "🔍 DPO Processing Monitor - $(date '+%H:%M:%S')"
    echo "=================================================="
    echo ""
    
    # 1. Git Status
    echo "📦 GIT STATUS:"
    echo "  Branch: $(git branch --show-current)"
    echo "  Last commit: $(git log -1 --format='%h %ad %s' --date=format:'%Y-%m-%d %H:%M')"
    echo "  Total commits on branch: $(git log --oneline | wc -l | tr -d ' ')"
    echo ""
    
    # 2. RAGAS Verification Status
    echo "🔬 RAGAS VERIFICATION STATUS:"
    verification_count=$(docker logs verification-worker 2>&1 | grep -c "Verification complete")
    latest_verification=$(docker logs verification-worker 2>&1 | grep "RAGAS scores" | tail -1)
    echo "  Total verifications completed: $verification_count"
    echo "  Latest: $latest_verification"
    
    # Check if verification is currently running
    if docker logs verification-worker 2>&1 | tail -5 | grep -q "Evaluating:"; then
        current_eval=$(docker logs verification-worker 2>&1 | tail -5 | grep "Evaluating:" | tail -1)
        echo "  ⏳ Currently evaluating: $current_eval"
    fi
    echo ""
    
    # 3. Dataset Worker Status
    echo "📊 DATASET GENERATION WORKER STATUS:"
    dataset_stats=$(docker logs dataset-generation-worker 2>&1 | grep "Stats:" | tail -1)
    echo "  $dataset_stats"
    
    # Check for DPO pair creation
    dpo_created=$(docker logs dataset-generation-worker 2>&1 | grep -c "✅ All quality checks passed")
    dpo_rejected_diff=$(docker logs dataset-generation-worker 2>&1 | grep -c "❌ Score diff too small")
    dpo_rejected_score=$(docker logs dataset-generation-worker 2>&1 | grep -c "❌ Chosen score too low")
    dpo_rejected_quality=$(docker logs dataset-generation-worker 2>&1 | grep -c "❌ Chosen answer failed verbatim test")
    
    echo "  DPO pairs created: $dpo_created"
    echo "  Rejected (low score diff): $dpo_rejected_diff"
    echo "  Rejected (low chosen score): $dpo_rejected_score"
    echo "  Rejected (quality filter): $dpo_rejected_quality"
    echo ""
    
    # 4. DPO Files Status
    echo "📁 DPO FILES:"
    if [ -f "data/dpo_data/dpo_data_202512.jsonl" ]; then
        file_size=$(ls -lh data/dpo_data/dpo_data_202512.jsonl | awk '{print $5}')
        line_count=$(wc -l < data/dpo_data/dpo_data_202512.jsonl)
        echo "  ✅ File exists: dpo_data_202512.jsonl"
        echo "  Size: $file_size"
        echo "  DPO pairs: $line_count"
        
        if [ $line_count -gt 0 ]; then
            echo ""
            echo "  Latest DPO pair:"
            tail -1 data/dpo_data/dpo_data_202512.jsonl | jq -c '{question: .prompt[:60], chosen_score, rejected_score, score_diff}'
        fi
    else
        echo "  ⏳ No DPO file created yet"
    fi
    echo ""
    
    # 5. Event Aggregator Status
    echo "🔄 EVENT AGGREGATOR:"
    aggregator_status=$(docker logs dataset-generation-worker 2>&1 | grep "complete.*pending.*expired" | tail -1)
    echo "  $aggregator_status"
    
    # Show pending questions
    pending_questions=$(docker logs dataset-generation-worker 2>&1 | grep "Aggregating.*candidates" | tail -5)
    if [ -n "$pending_questions" ]; then
        echo ""
        echo "  Recent aggregations:"
        echo "$pending_questions" | sed 's/^/    /'
    fi
    echo ""
    
    # 6. Recent Activity
    echo "📝 RECENT ACTIVITY (last 30 seconds):"
    recent_verification=$(docker logs verification-worker 2>&1 --since 30s | grep -E "(Processing|Verification complete)" | tail -3)
    recent_dataset=$(docker logs dataset-generation-worker 2>&1 --since 30s | grep -E "(Received event|quality checks|DPO)" | tail -3)
    
    if [ -n "$recent_verification" ]; then
        echo "  Verification Worker:"
        echo "$recent_verification" | sed 's/^/    /'
    fi
    
    if [ -n "$recent_dataset" ]; then
        echo "  Dataset Worker:"
        echo "$recent_dataset" | sed 's/^/    /'
    fi
    
    if [ -z "$recent_verification" ] && [ -z "$recent_dataset" ]; then
        echo "  ⏸️  No recent activity"
    fi
    echo ""
    
    echo "=================================================="
    echo "Press Ctrl+C to stop monitoring"
    echo "Refreshing in 10 seconds..."
    
    sleep 10
done

