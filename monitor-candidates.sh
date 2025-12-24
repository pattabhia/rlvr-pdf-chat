#!/bin/bash

# Multi-Candidate Generation Monitor
# Shows real-time candidate generation with nice formatting

LOG_DIR="${LOG_DIR:-/workspace/logs}"
QA_LOG="$LOG_DIR/qa-orchestrator.log"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Clear screen
clear

echo -e "${BOLD}╔════════════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}║                    MULTI-CANDIDATE GENERATION MONITOR                      ║${NC}"
echo -e "${BOLD}╔════════════════════════════════════════════════════════════════════════════╗${NC}"
echo ""

# Track last processed line
LAST_LINE=0

# Function to format timestamp
format_time() {
    echo "$1" | sed 's/.*\([0-9]\{2\}:[0-9]\{2\}:[0-9]\{2\}\).*/\1/'
}

# Function to truncate text
truncate_text() {
    local text="$1"
    local max_len="${2:-70}"
    if [ ${#text} -gt $max_len ]; then
        echo "${text:0:$max_len}..."
    else
        echo "$text"
    fi
}

# Main monitoring loop
echo -e "${CYAN}Monitoring: $QA_LOG${NC}"
echo -e "${CYAN}Press Ctrl+C to exit${NC}"
echo ""
echo -e "${BOLD}────────────────────────────────────────────────────────────────────────────${NC}"
echo ""

if [ ! -f "$QA_LOG" ]; then
    echo -e "${YELLOW}⚠ Log file not found: $QA_LOG${NC}"
    echo "Waiting for log file to be created..."
    while [ ! -f "$QA_LOG" ]; do
        sleep 1
    done
fi

# Follow the log file
tail -f "$QA_LOG" 2>/dev/null | while read -r line; do
    timestamp=$(format_time "$line")
    
    # Question received
    if [[ $line =~ "Received question:" ]]; then
        question=$(echo "$line" | sed 's/.*Received question: //' | sed 's/,.*//')
        echo -e "${BOLD}${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${BOLD}${GREEN}📥 NEW QUESTION${NC} ${CYAN}[$timestamp]${NC}"
        echo -e "${BOLD}${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${YELLOW}Q:${NC} $(truncate_text "$question" 70)"
        echo ""
    fi
    
    # Number of candidates
    if [[ $line =~ "num_candidates="([0-9]+) ]]; then
        num="${BASH_REMATCH[1]}"
        echo -e "${BLUE}🎯 Generating ${BOLD}$num${NC}${BLUE} candidate answers...${NC}"
        echo ""
    fi
    
    # Candidate generation started
    if [[ $line =~ "Generating candidate".*"of" ]]; then
        candidate_info=$(echo "$line" | sed 's/.*Generating candidate //')
        echo -e "${MAGENTA}  ⚙️  $candidate_info${NC}"
    fi
    
    # Candidate generated
    if [[ $line =~ "Generated candidate".*"answer_id=" ]]; then
        if [[ $line =~ answer_id=([a-f0-9-]+) ]]; then
            answer_id="${BASH_REMATCH[1]}"
            short_id="${answer_id:0:8}"
        fi
        
        if [[ $line =~ "candidate ([0-9]+)" ]]; then
            num="${BASH_REMATCH[1]}"
        fi
        
        echo -e "${GREEN}  ✅ Candidate #$num generated${NC} ${CYAN}(ID: $short_id)${NC}"
    fi
    
    # Answer content preview
    if [[ $line =~ "Answer preview:" ]]; then
        preview=$(echo "$line" | sed 's/.*Answer preview: //')
        echo -e "${CYAN}     Preview:${NC} $(truncate_text "$preview" 65)"
    fi
    
    # Event published
    if [[ $line =~ "Published event: answer.generated" ]]; then
        if [[ $line =~ id=([a-f0-9-]+) ]]; then
            event_id="${BASH_REMATCH[1]}"
            short_id="${event_id:0:8}"
        fi
        echo -e "${BLUE}  📤 Event published:${NC} answer.generated ${CYAN}($short_id)${NC}"
    fi
    
    # All candidates complete
    if [[ $line =~ "All candidates generated" ]] || [[ $line =~ "Multi-candidate generation complete" ]]; then
        echo ""
        echo -e "${GREEN}  ✨ All candidates generated successfully!${NC}"
        echo -e "${BOLD}${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo ""
    fi
    
    # Errors
    if [[ $line =~ "ERROR" ]] || [[ $line =~ "Error" ]]; then
        error_msg=$(echo "$line" | sed 's/.*ERROR - //' | sed 's/.*Error: //')
        echo -e "${BOLD}${YELLOW}  ⚠️  ERROR:${NC} $(truncate_text "$error_msg" 65)"
    fi
done

