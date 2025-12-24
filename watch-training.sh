#!/bin/bash

# Watch Training Data JSONL in Real-Time
# Shows new entries as they're written with pretty formatting

DATA_DIR="${DATA_DIR:-/workspace/rlvr-automation/data}"
TRAINING_FILE="$DATA_DIR/training_data/training_data_$(date +%Y%m).jsonl"

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
echo -e "${BOLD}║                  TRAINING DATA REAL-TIME VIEWER                            ║${NC}"
echo -e "${BOLD}╔════════════════════════════════════════════════════════════════════════════╗${NC}"
echo ""
echo -e "${CYAN}Watching: $TRAINING_FILE${NC}"
echo -e "${CYAN}Press Ctrl+C to exit${NC}"
echo ""

# Create directory if it doesn't exist
mkdir -p "$(dirname "$TRAINING_FILE")"

# Wait for file to exist
if [ ! -f "$TRAINING_FILE" ]; then
    echo -e "${YELLOW}⏳ Waiting for training file to be created...${NC}"
    while [ ! -f "$TRAINING_FILE" ]; do
        sleep 1
    done
    echo -e "${GREEN}✅ Training file found!${NC}"
    echo ""
fi

# Get initial line count
last_count=$(wc -l < "$TRAINING_FILE" 2>/dev/null || echo 0)
echo -e "${MAGENTA}📊 Current entries: $last_count${NC}"
echo ""
echo -e "${BOLD}────────────────────────────────────────────────────────────────────────────${NC}"
echo -e "${YELLOW}Waiting for new entries...${NC}"
echo ""

# Function to pretty print a training entry
pretty_print_entry() {
    local json_line="$1"
    local entry_num="$2"
    
    echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BOLD}${BLUE}📝 NEW TRAINING ENTRY #$entry_num${NC} ${CYAN}[$(date '+%H:%M:%S')]${NC}"
    echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    # Check if jq is available
    if command -v jq &> /dev/null; then
        # Extract question
        question=$(echo "$json_line" | jq -r '.question // "N/A"' 2>/dev/null)
        echo -e "${BOLD}${YELLOW}Question:${NC}"
        echo -e "  $question"
        echo ""
        
        # Extract answer
        answer=$(echo "$json_line" | jq -r '.answer // "N/A"' 2>/dev/null)
        echo -e "${BOLD}${GREEN}Answer:${NC}"
        echo "$answer" | fold -w 75 -s | sed 's/^/  /'
        echo ""
        
        # Extract verification scores
        faith=$(echo "$json_line" | jq -r '.verification.faithfulness // "N/A"' 2>/dev/null)
        rel=$(echo "$json_line" | jq -r '.verification.relevancy // "N/A"' 2>/dev/null)
        overall=$(echo "$json_line" | jq -r '.verification.overall_score // "N/A"' 2>/dev/null)
        conf=$(echo "$json_line" | jq -r '.verification.confidence // "N/A"' 2>/dev/null)
        
        if [[ "$faith" != "N/A" ]] || [[ "$rel" != "N/A" ]]; then
            echo -e "${BOLD}${CYAN}📊 Verification Scores:${NC}"
            if [[ "$faith" != "N/A" ]]; then
                echo -e "  ${CYAN}Faithfulness:${NC}  $faith"
            fi
            if [[ "$rel" != "N/A" ]]; then
                echo -e "  ${CYAN}Relevancy:${NC}     $rel"
            fi
            if [[ "$overall" != "N/A" ]]; then
                echo -e "  ${CYAN}Overall:${NC}       $overall"
            fi
            if [[ "$conf" != "N/A" ]]; then
                echo -e "  ${CYAN}Confidence:${NC}    $conf"
            fi
            echo ""
        fi
        
        # Extract contexts count
        contexts_count=$(echo "$json_line" | jq -r '.contexts | length // 0' 2>/dev/null)
        if [[ "$contexts_count" != "0" ]]; then
            echo -e "${CYAN}📚 Contexts used:${NC} $contexts_count"
            echo ""
        fi
        
        # Extract timestamp
        timestamp=$(echo "$json_line" | jq -r '.timestamp // "N/A"' 2>/dev/null)
        if [[ "$timestamp" != "N/A" ]]; then
            echo -e "${CYAN}🕐 Timestamp:${NC} $timestamp"
            echo ""
        fi
        
    else
        # Fallback without jq
        echo -e "${YELLOW}⚠️  Install 'jq' for better formatting${NC}"
        echo ""
        echo "$json_line" | python3 -m json.tool 2>/dev/null || echo "$json_line"
        echo ""
    fi
    
    echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

# Tail the file and process new lines
tail -f "$TRAINING_FILE" 2>/dev/null | while read -r line; do
    if [ ! -z "$line" ]; then
        last_count=$((last_count + 1))
        pretty_print_entry "$line" "$last_count"
        echo -e "${MAGENTA}📊 Total entries: $last_count${NC}"
        echo ""
        echo -e "${YELLOW}Waiting for next entry...${NC}"
        echo ""
    fi
done

