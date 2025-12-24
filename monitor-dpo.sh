#!/bin/bash

# DPO Preference Pair Monitor
# Shows DPO pair creation with chosen/rejected answers

LOG_DIR="${LOG_DIR:-/workspace/logs}"
DATASET_LOG="$LOG_DIR/dataset-worker.log"
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

# Clear screen
clear

echo -e "${BOLD}╔════════════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}║                     DPO PREFERENCE PAIR MONITOR                            ║${NC}"
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

# Function to draw score comparison
draw_comparison() {
    local chosen=$1
    local rejected=$2
    local diff=$3
    
    echo -e "  ${BOLD}${GREEN}Chosen:${NC}   $(printf '█%.0s' $(seq 1 $(echo "$chosen * 30" | bc | cut -d. -f1))) ${GREEN}$chosen${NC}"
    echo -e "  ${BOLD}${RED}Rejected:${NC} $(printf '█%.0s' $(seq 1 $(echo "$rejected * 30" | bc | cut -d. -f1))) ${RED}$rejected${NC}"
    echo -e "  ${BOLD}${CYAN}Margin:${NC}   $(printf '█%.0s' $(seq 1 $(echo "$diff * 30" | bc | cut -d. -f1))) ${CYAN}+$diff${NC}"
}

echo -e "${CYAN}Monitoring: $DATASET_LOG${NC}"
echo -e "${CYAN}Data directory: $DATA_DIR${NC}"
echo -e "${CYAN}Press Ctrl+C to exit${NC}"
echo ""
echo -e "${BOLD}────────────────────────────────────────────────────────────────────────────${NC}"
echo ""

# Show existing DPO files
if [ -d "$DATA_DIR/dpo" ]; then
    dpo_count=$(find "$DATA_DIR/dpo" -name "*.json" -type f 2>/dev/null | wc -l)
    echo -e "${MAGENTA}📁 Existing DPO pairs: $dpo_count${NC}"
    echo ""
fi

if [ ! -f "$DATASET_LOG" ]; then
    echo -e "${YELLOW}⚠ Log file not found: $DATASET_LOG${NC}"
    echo "Waiting for log file to be created..."
    while [ ! -f "$DATASET_LOG" ]; do
        sleep 1
    done
fi

# Track state
current_question=""
best_score=""
worst_score=""
score_diff=""

# Follow the log file
tail -f "$DATASET_LOG" 2>/dev/null | while read -r line; do
    timestamp=$(format_time "$line")
    
    # DPO analysis line
    if [[ $line =~ "DPO: Question" ]]; then
        question=$(echo "$line" | sed "s/.*Question '//" | sed "s/'.*//")
        current_question="$question"
        
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
        
        # Check if DPO pair will be created
        will_create_dpo=false
        if (( $(echo "$score_diff >= 0.3" | bc -l) )) && (( $(echo "$best_score >= 0.7" | bc -l) )); then
            will_create_dpo=true
        fi
        
        if [ "$will_create_dpo" = true ]; then
            echo -e "${BOLD}${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
            echo -e "${BOLD}${GREEN}✨ DPO PAIR CREATED${NC} ${CYAN}[$timestamp]${NC}"
            echo -e "${BOLD}${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
            echo ""
            echo -e "${BOLD}Question:${NC}"
            echo -e "  $(truncate_text "$question" 70)"
            echo ""
            echo -e "${BOLD}Score Comparison:${NC}"
            draw_comparison "$best_score" "$worst_score" "$score_diff"
            echo ""
            echo -e "${BOLD}Quality Metrics:${NC}"
            echo -e "  ${GREEN}✅ Score difference: $score_diff (≥ 0.3 required)${NC}"
            echo -e "  ${GREEN}✅ Best score: $best_score (≥ 0.7 required)${NC}"
            echo -e "  ${CYAN}📊 Answers analyzed: $num_answers${NC}"
            echo ""
        else
            echo -e "${BOLD}${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
            echo -e "${BOLD}${YELLOW}⚠️  DPO PAIR SKIPPED${NC} ${CYAN}[$timestamp]${NC}"
            echo -e "${BOLD}${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
            echo ""
            echo -e "${BOLD}Question:${NC}"
            echo -e "  $(truncate_text "$question" 70)"
            echo ""
            echo -e "${BOLD}Score Analysis:${NC}"
            echo -e "  ${CYAN}Best score:${NC}  $best_score"
            echo -e "  ${CYAN}Worst score:${NC} $worst_score"
            echo -e "  ${RED}Difference:${NC}  $score_diff"
            echo ""
            echo -e "${BOLD}Reasons for skipping:${NC}"
            
            if (( $(echo "$score_diff < 0.3" | bc -l) )); then
                echo -e "  ${RED}❌ Score difference too small: $score_diff < 0.3${NC}"
                echo -e "     ${CYAN}Need more variation between answers${NC}"
            fi
            
            if (( $(echo "$best_score < 0.7" | bc -l) )); then
                echo -e "  ${RED}❌ Best score too low: $best_score < 0.7${NC}"
                echo -e "     ${CYAN}Best answer quality not high enough${NC}"
            fi
            
            echo -e "  ${CYAN}📊 Answers analyzed: $num_answers${NC}"
            echo ""
        fi
    fi
    
    # DPO file saved
    if [[ $line =~ "Saved DPO pair to" ]] || [[ $line =~ "Created DPO pair" ]]; then
        filepath=$(echo "$line" | sed 's/.*to //' | sed 's/ .*//')
        filename=$(basename "$filepath" 2>/dev/null || echo "unknown")
        
        echo -e "${GREEN}  💾 DPO pair saved:${NC} $filename"
        echo ""
        
        # Try to show pair details if file exists
        if [ -f "$filepath" ]; then
            echo -e "${BOLD}  📄 Pair Details:${NC}"
            
            # Extract chosen and rejected previews using grep/sed
            chosen_preview=$(grep -o '"chosen"[^}]*"text":"[^"]*"' "$filepath" 2>/dev/null | sed 's/.*"text":"//' | sed 's/".*//' | head -c 100)
            rejected_preview=$(grep -o '"rejected"[^}]*"text":"[^"]*"' "$filepath" 2>/dev/null | sed 's/.*"text":"//' | sed 's/".*//' | head -c 100)
            
            if [ ! -z "$chosen_preview" ]; then
                echo -e "  ${GREEN}✅ Chosen:${NC}   $(truncate_text "$chosen_preview" 60)"
            fi
            if [ ! -z "$rejected_preview" ]; then
                echo -e "  ${RED}❌ Rejected:${NC} $(truncate_text "$rejected_preview" 60)"
            fi
            echo ""
        fi
        
        # Update count
        if [ -d "$DATA_DIR/dpo" ]; then
            dpo_count=$(find "$DATA_DIR/dpo" -name "*.json" -type f 2>/dev/null | wc -l)
            echo -e "${MAGENTA}  📊 Total DPO pairs: $dpo_count${NC}"
        fi
        
        echo -e "${BOLD}${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo ""
    fi
    
    # Training data written (but not DPO)
    if [[ $line =~ "Wrote entry to training_data" ]] && [ ! -z "$current_question" ]; then
        if [ "$will_create_dpo" != true ]; then
            echo -e "${CYAN}  📝 Added to training data (no DPO pair)${NC}"
            echo -e "${BOLD}${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
            echo ""
        fi
    fi
done

