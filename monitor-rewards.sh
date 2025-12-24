#!/bin/bash

# Reward Calculation Monitor
# Shows reward model scoring (when implemented)

LOG_DIR="${LOG_DIR:-/workspace/logs}"
DATASET_LOG="$LOG_DIR/dataset-worker.log"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
RED='\033[0;31m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Clear screen
clear

echo -e "${BOLD}╔════════════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}║                        REWARD CALCULATION MONITOR                          ║${NC}"
echo -e "${BOLD}╔════════════════════════════════════════════════════════════════════════════╗${NC}"
echo ""

# Function to format timestamp
format_time() {
    echo "$1" | sed 's/.*\([0-9]\{2\}:[0-9]\{2\}:[0-9]\{2\}\).*/\1/'
}

# Function to truncate text
truncate_text() {
    local text="$1"
    local max_len="${2:-60}"
    if [ ${#text} -gt $max_len ]; then
        echo "${text:0:$max_len}..."
    else
        echo "$text"
    fi
}

# Function to draw score bar
draw_score_bar() {
    local score=$1
    local width=25
    local filled=$(echo "$score * $width" | bc | cut -d. -f1)
    local empty=$((width - filled))
    
    # Color based on score
    local color=$RED
    if (( $(echo "$score >= 0.8" | bc -l) )); then
        color=$GREEN
    elif (( $(echo "$score >= 0.6" | bc -l) )); then
        color=$YELLOW
    fi
    
    echo -ne "${color}"
    printf '█%.0s' $(seq 1 $filled)
    echo -ne "${NC}"
    printf '░%.0s' $(seq 1 $empty)
    printf " %.3f" "$score"
}

echo -e "${CYAN}Monitoring: $DATASET_LOG${NC}"
echo -e "${CYAN}Press Ctrl+C to exit${NC}"
echo ""
echo -e "${BOLD}────────────────────────────────────────────────────────────────────────────${NC}"
echo ""

if [ ! -f "$DATASET_LOG" ]; then
    echo -e "${YELLOW}⚠ Log file not found: $DATASET_LOG${NC}"
    echo "Waiting for log file to be created..."
    while [ ! -f "$DATASET_LOG" ]; do
        sleep 1
    done
fi

# Track current question
current_question=""

# Follow the log file
tail -f "$DATASET_LOG" 2>/dev/null | while read -r line; do
    timestamp=$(format_time "$line")
    
    # Verification event received
    if [[ $line =~ "Received event: verification.completed" ]]; then
        if [[ $line =~ id=([a-f0-9-]+) ]]; then
            event_id="${BASH_REMATCH[1]}"
            short_id="${event_id:0:8}"
        fi
        echo -e "${BLUE}  📨 Verification received${NC} ${CYAN}($short_id)${NC} ${CYAN}[$timestamp]${NC}"
    fi
    
    # Complete entry detected
    if [[ $line =~ "Complete entry:" ]]; then
        question=$(echo "$line" | sed 's/.*Complete entry: //' | sed 's/\.\.\..*//')
        current_question="$question"
        
        has_reward="false"
        if [[ $line =~ "has_reward=True" ]]; then
            has_reward="true"
        fi
        
        echo ""
        echo -e "${BOLD}${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${BOLD}${GREEN}🎯 COMPLETE ENTRY - CALCULATING REWARDS${NC} ${CYAN}[$timestamp]${NC}"
        echo -e "${BOLD}${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${YELLOW}Question:${NC} $(truncate_text "$question" 65)"
        echo ""
        
        if [ "$has_reward" = "true" ]; then
            echo -e "${GREEN}  ✅ Reward model scores available${NC}"
        else
            echo -e "${CYAN}  📊 Using RAGAS scores (reward model not yet implemented)${NC}"
        fi
        echo ""
    fi
    
    # DPO analysis
    if [[ $line =~ "DPO: Question" ]]; then
        question=$(echo "$line" | sed "s/.*Question '//" | sed "s/'.*//")
        
        num_answers=""
        score_diff=""
        best_score=""
        worst_score=""
        
        if [[ $line =~ "has ([0-9]+) answers" ]]; then
            num_answers="${BASH_REMATCH[1]}"
        fi
        if [[ $line =~ "score diff: ([0-9.]+)" ]]; then
            score_diff="${BASH_REMATCH[1]}"
        fi
        if [[ $line =~ "best=([0-9.]+)" ]]; then
            best_score="${BASH_REMATCH[1]}"
        fi
        if [[ $line =~ "worst=([0-9.]+)" ]]; then
            worst_score="${BASH_REMATCH[1]}"
        fi
        
        echo -e "${BOLD}  📊 SCORE ANALYSIS${NC}"
        echo -e "  ─────────────────────────────────────────────────────────────────"
        echo -e "  ${CYAN}Answers collected:${NC} $num_answers"
        echo ""
        echo -e "  ${BOLD}Best Answer:${NC}   $(draw_score_bar $best_score)"
        echo -e "  ${BOLD}Worst Answer:${NC}  $(draw_score_bar $worst_score)"
        echo ""
        
        # Color code the difference
        diff_color=$RED
        if (( $(echo "$score_diff >= 0.3" | bc -l) )); then
            diff_color=$GREEN
        elif (( $(echo "$score_diff >= 0.2" | bc -l) )); then
            diff_color=$YELLOW
        fi
        
        echo -e "  ${BOLD}Score Difference:${NC} ${diff_color}${BOLD}$score_diff${NC}"
        echo -e "  ${CYAN}Required for DPO:${NC} 0.300"
        echo ""
        
        # Determine if DPO pair will be created
        if (( $(echo "$score_diff >= 0.3" | bc -l) )) && (( $(echo "$best_score >= 0.7" | bc -l) )); then
            echo -e "  ${GREEN}✅ DPO pair will be created!${NC}"
        else
            echo -e "  ${YELLOW}⚠️  DPO pair skipped:${NC}"
            if (( $(echo "$score_diff < 0.3" | bc -l) )); then
                echo -e "     ${RED}• Score difference too small ($score_diff < 0.3)${NC}"
            fi
            if (( $(echo "$best_score < 0.7" | bc -l) )); then
                echo -e "     ${RED}• Best score too low ($best_score < 0.7)${NC}"
            fi
        fi
        echo -e "  ─────────────────────────────────────────────────────────────────"
        echo ""
    fi
    
    # Entry written
    if [[ $line =~ "Wrote entry to training_data" ]]; then
        filename=$(echo "$line" | sed 's/.*to //' | sed 's/:.*//')
        echo -e "${GREEN}  💾 Training data written:${NC} $filename"
    fi
    
    # Stats
    if [[ $line =~ "Complete entry written! Total:" ]]; then
        if [[ $line =~ "Total: ([0-9]+)" ]]; then
            total="${BASH_REMATCH[1]}"
        fi
        if [[ $line =~ "answer=([0-9]+)" ]]; then
            answers="${BASH_REMATCH[1]}"
        fi
        if [[ $line =~ "verification=([0-9]+)" ]]; then
            verifications="${BASH_REMATCH[1]}"
        fi
        if [[ $line =~ "reward=([0-9]+)" ]]; then
            rewards="${BASH_REMATCH[1]}"
        fi
        
        echo -e "${BOLD}${MAGENTA}  📈 PIPELINE STATS${NC}"
        echo -e "  ${CYAN}Total entries:${NC}      $total"
        echo -e "  ${CYAN}Answers:${NC}            $answers"
        echo -e "  ${CYAN}Verifications:${NC}      $verifications"
        echo -e "  ${CYAN}Rewards:${NC}            $rewards"
        echo -e "${BOLD}${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo ""
    fi
done

