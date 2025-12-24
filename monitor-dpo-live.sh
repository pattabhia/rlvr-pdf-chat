#!/bin/bash

# Real-time DPO monitoring - shows latest activity

DPO_FILE="/app/data/dpo_data/dpo_data_202512.jsonl"
DATASET_LOG="/workspace/logs/dataset-worker.log"
VERIFY_LOG="/workspace/logs/verification-worker.log"

clear
echo "════════════════════════════════════════════════════════════════════════════"
echo "  🔴 LIVE DPO MONITORING (refreshes every 5 seconds)"
echo "  $(date '+%Y-%m-%d %H:%M:%S')"
echo "════════════════════════════════════════════════════════════════════════════"
echo ""

# Total DPO pairs
if [ -f "$DPO_FILE" ]; then
    total_pairs=$(wc -l < "$DPO_FILE")
    file_size=$(du -h "$DPO_FILE" | cut -f1)
    echo "📊 Total DPO Pairs: $total_pairs (File size: $file_size)"
else
    total_pairs=0
    echo "📊 Total DPO Pairs: 0 (File not created yet)"
fi
echo ""

# Latest DPO pair created
echo "🆕 Latest DPO Pair Created:"
echo "────────────────────────────────────────────────────────────────────────────"
if [ -f "$DPO_FILE" ] && [ $total_pairs -gt 0 ]; then
    tail -1 "$DPO_FILE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    prompt = data.get('prompt', 'N/A')[:70]
    chosen_score = data.get('chosen_score', 0)
    rejected_score = data.get('rejected_score', 0)
    score_diff = data.get('score_diff', 0)
    created_at = data.get('metadata', {}).get('created_at', 'N/A')
    print(f'Question: {prompt}...')
    print(f'Chosen Score: {chosen_score:.3f} | Rejected Score: {rejected_score:.3f} | Diff: {score_diff:.3f}')
    print(f'Created: {created_at}')
except Exception as e:
    print(f'(Unable to parse: {e})')
" 2>&1
else
    echo "  (No DPO pairs created yet)"
fi
echo ""

# Recent questions being processed (last 5 minutes)
echo "🔄 Recent Questions Being Processed (last 5 min):"
echo "────────────────────────────────────────────────────────────────────────────"
recent_questions=$(strings "$DATASET_LOG" 2>/dev/null | grep "Complete entry:" | tail -10 | awk -F': ' '{print $NF}' | sed 's/\.\.\.//' | tail -5)
if [ -z "$recent_questions" ]; then
    echo "  (No recent activity)"
else
    echo "$recent_questions" | nl
fi
echo ""

# Latest DPO analysis (last 5)
echo "📈 Latest DPO Analysis (last 5):"
echo "────────────────────────────────────────────────────────────────────────────"
latest_analysis=$(strings "$DATASET_LOG" 2>/dev/null | grep "DPO: Question" | tail -5)
if [ -z "$latest_analysis" ]; then
    echo "  (No DPO analysis yet)"
else
    echo "$latest_analysis" | while read line; do
        # Extract score diff and check if it passed (using awk instead of bc)
        score_diff=$(echo "$line" | grep -oP 'score diff: \K[0-9.]+')
        best_score=$(echo "$line" | grep -oP 'best=\K[0-9.]+')

        # Use awk for floating point comparison (bc not available)
        passed=$(awk -v diff="$score_diff" -v best="$best_score" 'BEGIN {print (diff >= 0.05 && best >= 0.6) ? "yes" : "no"}')

        if [ "$passed" = "yes" ]; then
            echo "  ✅ $line"
        else
            echo "  ❌ $line"
        fi
    done
fi
echo ""

# Latest verifications (last 5)
echo "🔍 Latest Verifications (last 5):"
echo "────────────────────────────────────────────────────────────────────────────"
latest_verifications=$(strings "$VERIFY_LOG" 2>/dev/null | grep "Verification complete:" | tail -5)
if [ -z "$latest_verifications" ]; then
    echo "  (No verifications yet)"
else
    echo "$latest_verifications"
fi
echo ""

# Worker status
echo "🔧 Worker Status:"
echo "────────────────────────────────────────────────────────────────────────────"
verify_pid=$(ps aux | grep "verification-worker" | grep -v grep | awk '{print $2}')
dataset_pid=$(ps aux | grep "dataset-generation-worker" | grep -v grep | awk '{print $2}')

if [ -z "$verify_pid" ]; then
    echo "  ❌ Verification worker: NOT RUNNING"
else
    echo "  ✅ Verification worker: Running (PID: $verify_pid)"
fi

if [ -z "$dataset_pid" ]; then
    echo "  ❌ Dataset worker: NOT RUNNING"
else
    echo "  ✅ Dataset worker: Running (PID: $dataset_pid)"
fi
echo ""

# Event counts (last 1 minute)
echo "📊 Event Activity (last 1 min):"
echo "────────────────────────────────────────────────────────────────────────────"
one_min_ago=$(date -d '1 minute ago' '+%Y-%m-%d %H:%M' 2>/dev/null || date -v-1M '+%Y-%m-%d %H:%M')
answer_events=$(strings "$DATASET_LOG" 2>/dev/null | grep "Received event: answer.generated" | grep "$one_min_ago" | wc -l)
verify_events=$(strings "$DATASET_LOG" 2>/dev/null | grep "Received event: verification.completed" | grep "$one_min_ago" | wc -l)
complete_entries=$(strings "$DATASET_LOG" 2>/dev/null | grep "Complete entry written" | grep "$one_min_ago" | wc -l)

echo "  • Answer events: $answer_events"
echo "  • Verification events: $verify_events"
echo "  • Complete entries: $complete_entries"
echo ""

# Rejection stats (last 10)
echo "❌ Recent Rejections (last 10):"
echo "────────────────────────────────────────────────────────────────────────────"
rejections=$(strings "$DATASET_LOG" 2>/dev/null | grep -E "Score diff too small|Chosen score too low" | tail -10)
if [ -z "$rejections" ]; then
    echo "  (No rejections - all passing!)"
else
    echo "$rejections" | sed 's/^/  /'
fi
echo ""

# Current thresholds
echo "⚙️  Current Thresholds:"
echo "────────────────────────────────────────────────────────────────────────────"
thresholds=$(strings "$DATASET_LOG" 2>/dev/null | grep "DPO Dataset Writer initialized" | tail -1)
if [ -z "$thresholds" ]; then
    echo "  (Unable to read thresholds)"
else
    echo "  $thresholds"
fi
echo ""

echo "════════════════════════════════════════════════════════════════════════════"
echo "  Press Ctrl+C to stop monitoring"
echo "  Tip: Run 'watch -n 5 ./monitor-dpo-live.sh' for auto-refresh"
echo "════════════════════════════════════════════════════════════════════════════"

