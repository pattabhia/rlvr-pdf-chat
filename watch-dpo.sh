#!/bin/bash

# Watch DPO JSON Files in Real-Time
# Shows newly created DPO pairs with pretty formatting

DATA_DIR="${DATA_DIR:-/workspace/rlvr-automation/data}"
DPO_DIR="$DATA_DIR/dpo"

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
echo -e "${BOLD}║                    DPO PAIR REAL-TIME VIEWER                               ║${NC}"
echo -e "${BOLD}╔════════════════════════════════════════════════════════════════════════════╗${NC}"
echo ""
echo -e "${CYAN}Watching: $DPO_DIR${NC}"
echo -e "${CYAN}Press Ctrl+C to exit${NC}"
echo ""

# Create DPO directory if it doesn't exist
mkdir -p "$DPO_DIR"

# Get initial file count
last_count=$(find "$DPO_DIR" -name "*.json" -type f 2>/dev/null | wc -l | tr -d ' ')

echo -e "${MAGENTA}📁 Current DPO pairs: $last_count${NC}"
echo ""
echo -e "${BOLD}────────────────────────────────────────────────────────────────────────────${NC}"
echo -e "${YELLOW}Waiting for new DPO pairs...${NC}"
echo ""

# Function to pretty print a DPO pair
pretty_print_dpo() {
    local file="$1"
    local filename=$(basename "$file")
    
    echo -e "${BOLD}${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BOLD}${GREEN}✨ NEW DPO PAIR CREATED${NC} ${CYAN}[$(date '+%H:%M:%S')]${NC}"
    echo -e "${BOLD}${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}File:${NC} $filename"
    echo ""
    
    # Check if jq is available
    if command -v jq &> /dev/null; then
        # Use jq for pretty printing
        
        # Extract question
        question=$(jq -r '.prompt // .question // "N/A"' "$file" 2>/dev/null)
        echo -e "${BOLD}${YELLOW}Question:${NC}"
        echo -e "  $question"
        echo ""
        
        # Extract chosen answer
        chosen_text=$(jq -r '.chosen.text // .chosen // "N/A"' "$file" 2>/dev/null)
        chosen_score=$(jq -r '.chosen.score // "N/A"' "$file" 2>/dev/null)
        
        echo -e "${BOLD}${GREEN}✅ CHOSEN Answer (Score: $chosen_score):${NC}"
        echo "$chosen_text" | fold -w 75 -s | sed 's/^/  /'
        echo ""
        
        # Extract rejected answer
        rejected_text=$(jq -r '.rejected.text // .rejected // "N/A"' "$file" 2>/dev/null)
        rejected_score=$(jq -r '.rejected.score // "N/A"' "$file" 2>/dev/null)
        
        echo -e "${BOLD}${RED}❌ REJECTED Answer (Score: $rejected_score):${NC}"
        echo "$rejected_text" | fold -w 75 -s | sed 's/^/  /'
        echo ""
        
        # Calculate margin
        if [[ "$chosen_score" != "N/A" ]] && [[ "$rejected_score" != "N/A" ]]; then
            margin=$(echo "$chosen_score - $rejected_score" | bc 2>/dev/null)
            echo -e "${BOLD}${CYAN}📊 Score Margin:${NC} +$margin"
            echo ""
        fi
        
        # Show metadata
        timestamp=$(jq -r '.timestamp // .created_at // "N/A"' "$file" 2>/dev/null)
        if [[ "$timestamp" != "N/A" ]]; then
            echo -e "${CYAN}🕐 Created:${NC} $timestamp"
        fi
        
    else
        # Fallback without jq - just show raw JSON with basic formatting
        echo -e "${YELLOW}⚠️  Install 'jq' for better formatting${NC}"
        echo ""
        cat "$file" | python3 -m json.tool 2>/dev/null || cat "$file"
    fi
    
    echo -e "${BOLD}${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

# Watch for new files
while true; do
    current_count=$(find "$DPO_DIR" -name "*.json" -type f 2>/dev/null | wc -l | tr -d ' ')
    
    if [ "$current_count" -gt "$last_count" ]; then
        # New file(s) detected
        new_files=$(find "$DPO_DIR" -name "*.json" -type f -mmin -1 2>/dev/null | sort)
        
        for file in $new_files; do
            # Check if we've already processed this file
            if [ -f "$file" ]; then
                pretty_print_dpo "$file"
            fi
        done
        
        last_count=$current_count
        echo -e "${MAGENTA}📊 Total DPO pairs: $current_count${NC}"
        echo ""
        echo -e "${YELLOW}Waiting for next DPO pair...${NC}"
        echo ""
    fi
    
    sleep 2
done

