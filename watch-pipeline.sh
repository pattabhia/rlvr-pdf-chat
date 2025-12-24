#!/bin/bash

# Watch Complete Pipeline in Real-Time
# Shows questions, answers, scores, and DPO pairs as they happen

LOG_DIR="${LOG_DIR:-/workspace/logs}"
DATA_DIR="${DATA_DIR:-/workspace/rlvr-automation/data}"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
RED='\033[0;31m'
NC='\033[0m' # No Color
BOLD='\033[1m'

clear

echo -e "${BOLD}╔════════════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}║                    RLVR PIPELINE LIVE VIEWER                               ║${NC}"
echo -e "${BOLD}║                  Watch Your Query Flow Through!                            ║${NC}"
echo -e "${BOLD}╔════════════════════════════════════════════════════════════════════════════╗${NC}"
echo ""
echo -e "${CYAN}📊 Monitoring all pipeline stages...${NC}"
echo -e "${CYAN}Press Ctrl+C to exit${NC}"
echo ""
echo -e "${BOLD}────────────────────────────────────────────────────────────────────────────${NC}"
echo ""

# Function to format timestamp
format_time() {
    echo "$1" | sed 's/.*\([0-9]\{2\}:[0-9]\{2\}:[0-9]\{2\}\).*/\1/'
}

# Function to draw score bar
draw_score_bar() {
    local score=$1
    local width=20
    local filled=$(echo "$score * $width" | bc 2>/dev/null | cut -d. -f1)
    local empty=$((width - filled))
    
    local color=$RED
    if (( $(echo "$score >= 0.8" | bc -l 2>/dev/null || echo 0) )); then
        color=$GREEN
    elif (( $(echo "$score >= 0.6" | bc -l 2>/dev/null || echo 0) )); then
        color=$YELLOW
    fi
    
    echo -ne "${color}"
    printf '█%.0s' $(seq 1 $filled 2>/dev/null)
    echo -ne "${NC}"
    printf '░%.0s' $(seq 1 $empty 2>/dev/null)
    printf " %.3f" "$score"
}

# Track state
current_question=""
candidate_count=0
verification_count=0

# Tail all relevant logs
tail -f "$LOG_DIR/qa-orchestrator.log" "$LOG_DIR/verification-worker.log" "$LOG_DIR/dataset-worker.log" 2>/dev/null | while read -r line; do
    timestamp=$(format_time "$line")
    
    # ========== QUESTION RECEIVED ==========
    if [[ $line =~ "Received question:" ]]; then
        question=$(echo "$line" | sed 's/.*Received question: //' | sed 's/,.*//')
        current_question="$question"
        candidate_count=0
        verification_count=0
        
        echo -e "${BOLD}${GREEN}╔════════════════════════════════════════════════════════════════════════════╗${NC}"
        echo -e "${BOLD}${GREEN}║  📥 NEW QUESTION RECEIVED${NC} ${CYAN}[$timestamp]${NC}"
        echo -e "${BOLD}${GREEN}╚════════════════════════════════════════════════════════════════════════════╝${NC}"
        echo -e "${YELLOW}$question${NC}"
        echo ""
    fi
    
    # ========== CANDIDATE GENERATED ==========
    if [[ $line =~ "Generated candidate" ]] && [[ $line =~ "answer_id=" ]]; then
        candidate_count=$((candidate_count + 1))
        
        if [[ $line =~ answer_id=([a-f0-9-]+) ]]; then
            answer_id="${BASH_REMATCH[1]:0:8}"
        fi
        
        echo -e "${BLUE}  ✅ Candidate #$candidate_count generated${NC} ${CYAN}(ID: $answer_id)${NC}"
        
        # Check if this is the last candidate
        if [[ $line =~ "candidate ([0-9]+)" ]]; then
            num="${BASH_REMATCH[1]}"
            if [[ $candidate_count -eq $num ]]; then
                echo -e "${GREEN}  🎯 All $num candidates generated!${NC}"
                echo ""
            fi
        fi
    fi
    
    # ========== VERIFICATION COMPLETE ==========
    if [[ $line =~ "Verification complete:" ]]; then
        verification_count=$((verification_count + 1))
        
        faith=""
        rel=""
        conf=""
        
        if [[ $line =~ faithfulness=([0-9.]+) ]]; then
            faith="${BASH_REMATCH[1]}"
        fi
        if [[ $line =~ relevancy=([0-9.]+) ]]; then
            rel="${BASH_REMATCH[1]}"
        fi
        if [[ $line =~ confidence=([a-z]+) ]]; then
            conf="${BASH_REMATCH[1]}"
        fi
        
        overall=$(echo "scale=3; ($faith + $rel) / 2" | bc 2>/dev/null || echo "0.000")
        
        echo -e "${MAGENTA}  📊 Verification #$verification_count:${NC}"
        echo -e "     Faithfulness: $(draw_score_bar $faith)"
        echo -e "     Relevancy:    $(draw_score_bar $rel)"
        echo -e "     Overall:      $(draw_score_bar $overall) ${CYAN}[$conf]${NC}"
        echo ""
    fi
    
    # ========== DPO ANALYSIS ==========
    if [[ $line =~ "DPO: Question" ]]; then
        score_diff=""
        best_score=""
        worst_score=""
        
        if [[ $line =~ "score diff: ([0-9.]+)" ]]; then
            score_diff="${BASH_REMATCH[1]}"
        fi
        if [[ $line =~ "best=([0-9.]+)" ]]; then
            best_score="${BASH_REMATCH[1]}"
        fi
        if [[ $line =~ "worst=([0-9.]+)" ]]; then
            worst_score="${BASH_REMATCH[1]}"
        fi
        
        echo -e "${BOLD}${CYAN}  ═══════════════════════════════════════════════════════════════════${NC}"
        echo -e "${BOLD}${CYAN}  📈 DPO SCORE ANALYSIS${NC}"
        echo -e "${BOLD}${CYAN}  ═══════════════════════════════════════════════════════════════════${NC}"
        echo -e "     Best:       $(draw_score_bar $best_score)"
        echo -e "     Worst:      $(draw_score_bar $worst_score)"
        
        # Check if DPO pair will be created
        if (( $(echo "$score_diff >= 0.3" | bc -l 2>/dev/null || echo 0) )) && (( $(echo "$best_score >= 0.7" | bc -l 2>/dev/null || echo 0) )); then
            echo -e "     ${GREEN}Difference: $score_diff ✅ DPO PAIR CREATED!${NC}"
        else
            echo -e "     ${RED}Difference: $score_diff ❌ Skipped (need ≥0.3)${NC}"
        fi
        echo -e "${BOLD}${CYAN}  ═══════════════════════════════════════════════════════════════════${NC}"
        echo ""
    fi
    
    # ========== TRAINING DATA WRITTEN ==========
    if [[ $line =~ "Wrote entry to training_data" ]]; then
        echo -e "${GREEN}  💾 Training data saved${NC}"
    fi
    
    # ========== COMPLETE ENTRY ==========
    if [[ $line =~ "Complete entry written! Total:" ]]; then
        total=""
        if [[ $line =~ "Total: ([0-9]+)" ]]; then
            total="${BASH_REMATCH[1]}"
        fi
        
        echo -e "${BOLD}${GREEN}  ✨ Entry complete! Total entries: $total${NC}"
        echo ""
        echo -e "${BOLD}${GREEN}╚════════════════════════════════════════════════════════════════════════════╝${NC}"
        echo ""
        echo -e "${YELLOW}Waiting for next question...${NC}"
        echo ""
    fi
done

