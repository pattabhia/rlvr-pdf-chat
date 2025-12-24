#!/bin/bash

# RAGAS Evaluation Monitor
# Shows real-time RAGAS verification with scores

LOG_DIR="${LOG_DIR:-/workspace/logs}"
VERIFY_LOG="$LOG_DIR/verification-worker.log"

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
echo -e "${BOLD}║                      RAGAS EVALUATION & SCORING MONITOR                    ║${NC}"
echo -e "${BOLD}╔════════════════════════════════════════════════════════════════════════════╗${NC}"
echo ""

# Function to format timestamp
format_time() {
    echo "$1" | sed 's/.*\([0-9]\{2\}:[0-9]\{2\}:[0-9]\{2\}\).*/\1/'
}

# Function to draw score bar
draw_score_bar() {
    local score=$1
    local width=30
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

# Function to get confidence emoji
get_confidence_emoji() {
    case "$1" in
        high) echo "🟢" ;;
        medium) echo "🟡" ;;
        low) echo "🔴" ;;
        *) echo "⚪" ;;
    esac
}

echo -e "${CYAN}Monitoring: $VERIFY_LOG${NC}"
echo -e "${CYAN}Press Ctrl+C to exit${NC}"
echo ""
echo -e "${BOLD}────────────────────────────────────────────────────────────────────────────${NC}"
echo ""

if [ ! -f "$VERIFY_LOG" ]; then
    echo -e "${YELLOW}⚠ Log file not found: $VERIFY_LOG${NC}"
    echo "Waiting for log file to be created..."
    while [ ! -f "$VERIFY_LOG" ]; do
        sleep 1
    done
fi

# Follow the log file
tail -f "$VERIFY_LOG" 2>/dev/null | while read -r line; do
    timestamp=$(format_time "$line")
    
    # Event received
    if [[ $line =~ "Received event: answer.generated" ]]; then
        if [[ $line =~ id=([a-f0-9-]+) ]]; then
            event_id="${BASH_REMATCH[1]}"
            short_id="${event_id:0:8}"
        fi
        echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${BOLD}${BLUE}📨 ANSWER RECEIVED FOR VERIFICATION${NC} ${CYAN}[$timestamp]${NC}"
        echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${CYAN}Event ID:${NC} $short_id"
        echo ""
    fi
    
    # Processing event
    if [[ $line =~ "Processing answer.generated event:" ]]; then
        echo -e "${MAGENTA}  ⚙️  Starting RAGAS verification...${NC}"
    fi
    
    # Running RAGAS
    if [[ $line =~ "Running RAGAS verification" ]]; then
        if [[ $line =~ "with Ollama" ]]; then
            echo -e "${BLUE}  🤖 Mode: Ollama LLM-based evaluation${NC}"
        else
            echo -e "${BLUE}  📊 Mode: Heuristic evaluation${NC}"
        fi
    fi
    
    # Heuristic details
    if [[ $line =~ "Heuristic scores:" ]]; then
        # Extract details from debug line
        if [[ $line =~ faithfulness=([0-9.]+) ]]; then
            faith="${BASH_REMATCH[1]}"
        fi
        if [[ $line =~ relevancy=([0-9.]+) ]]; then
            rel="${BASH_REMATCH[1]}"
        fi
        if [[ $line =~ overlap=([0-9.]+) ]]; then
            overlap="${BASH_REMATCH[1]}"
        fi
        if [[ $line =~ len=([0-9]+) ]]; then
            length="${BASH_REMATCH[1]}"
        fi
        if [[ $line =~ quality=([0-9.]+) ]]; then
            quality="${BASH_REMATCH[1]}"
        fi
        
        echo -e "${CYAN}  📈 Analysis:${NC} overlap=${overlap:-N/A}, length=${length:-N/A}, quality=${quality:-N/A}"
    fi
    
    # Verification complete
    if [[ $line =~ "Verification complete:" ]]; then
        faith=""
        rel=""
        conf=""
        
        # Extract scores
        if [[ $line =~ faithfulness=([0-9.]+) ]]; then
            faith="${BASH_REMATCH[1]}"
        fi
        if [[ $line =~ relevancy=([0-9.]+) ]]; then
            rel="${BASH_REMATCH[1]}"
        fi
        if [[ $line =~ confidence=([a-z]+) ]]; then
            conf="${BASH_REMATCH[1]}"
        fi
        
        # Calculate overall score
        overall=$(echo "scale=3; ($faith + $rel) / 2" | bc 2>/dev/null || echo "0.000")
        
        echo ""
        echo -e "${BOLD}${GREEN}  ✅ VERIFICATION COMPLETE${NC}"
        echo -e "${BOLD}  ═══════════════════════════════════════════════════════════════════${NC}"
        echo ""
        echo -e "  ${BOLD}Faithfulness:${NC}  $(draw_score_bar $faith)"
        echo -e "  ${BOLD}Relevancy:${NC}     $(draw_score_bar $rel)"
        echo -e "  ${BOLD}Overall Score:${NC} $(draw_score_bar $overall)"
        echo ""
        echo -e "  ${BOLD}Confidence:${NC}    $(get_confidence_emoji $conf) ${conf^^}"
        echo -e "${BOLD}  ═══════════════════════════════════════════════════════════════════${NC}"
        echo ""
    fi
    
    # Event published
    if [[ $line =~ "Published event: verification.completed" ]]; then
        if [[ $line =~ id=([a-f0-9-]+) ]]; then
            event_id="${BASH_REMATCH[1]}"
            short_id="${event_id:0:8}"
        fi
        echo -e "${GREEN}  📤 Published verification.completed event${NC} ${CYAN}($short_id)${NC}"
        echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo ""
    fi
    
    # Warnings
    if [[ $line =~ "WARNING" ]] && [[ $line =~ "RAGAS" ]]; then
        warning=$(echo "$line" | sed 's/.*WARNING - //')
        echo -e "${YELLOW}  ⚠️  $warning${NC}"
    fi
    
    # Errors
    if [[ $line =~ "ERROR" ]]; then
        error=$(echo "$line" | sed 's/.*ERROR - //')
        echo -e "${RED}  ❌ ERROR: $error${NC}"
    fi
done

