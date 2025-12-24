#!/bin/bash

# Colors and formatting
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m'
BOLD='\033[1m'
DIM='\033[2m'

# Configuration
LOG_DIR="/workspace/logs"
DATA_DIR="/workspace/rlvr-automation/data"

# Function to draw a box
draw_box() {
    local width=$1
    local title=$2
    local color=$3
    
    echo -e "${color}╔$(printf '═%.0s' $(seq 1 $((width-2))))╗${NC}"
    if [ ! -z "$title" ]; then
        local padding=$(( (width - ${#title} - 2) / 2 ))
        printf "${color}║${NC}${BOLD}${WHITE}%*s%s%*s${NC}${color}║${NC}\n" $padding "" "$title" $padding ""
        echo -e "${color}╠$(printf '═%.0s' $(seq 1 $((width-2))))╣${NC}"
    fi
}

draw_box_bottom() {
    local width=$1
    local color=$2
    echo -e "${color}╚$(printf '═%.0s' $(seq 1 $((width-2))))╝${NC}"
}

# Function to parse logs and extract pipeline data
parse_pipeline_data() {
    # Extract questions from QA Orchestrator
    if [ -f "$LOG_DIR/qa-orchestrator.log" ]; then
        tail -500 "$LOG_DIR/qa-orchestrator.log" 2>/dev/null | grep -a "Generating.*candidate answers for question" 2>/dev/null | tail -5 | while read line; do
            timestamp=$(echo "$line" | cut -d',' -f1 | sed 's/.*\([0-9]\{4\}-[0-9]\{2\}-[0-9]\{2\} [0-9]\{2\}:[0-9]\{2\}:[0-9]\{2\}\).*/\1/')
            question=$(echo "$line" | sed 's/.*question: //' | sed 's/"//g')
            echo "QUESTION|$timestamp|$question"
        done

        # Extract published events (answer.generated) to show worker activity
        tail -500 "$LOG_DIR/qa-orchestrator.log" 2>/dev/null | grep -a "Published event: answer.generated" 2>/dev/null | tail -10 | while read line; do
            timestamp=$(echo "$line" | cut -d',' -f1 | sed 's/.*\([0-9]\{4\}-[0-9]\{2\}-[0-9]\{2\} [0-9]\{2\}:[0-9]\{2\}:[0-9]\{2\}\).*/\1/')
            if [[ $line =~ id=([a-f0-9-]+) ]]; then
                event_id="${BASH_REMATCH[1]}"
                echo "WORKER|$timestamp|Candidate-${event_id:0:8}|Answer generated and sent to verification"
            fi
        done
    fi

    # Extract verification results from verification worker
    if [ -f "$LOG_DIR/verification-worker.log" ]; then
        tail -500 "$LOG_DIR/verification-worker.log" 2>/dev/null | grep -a "Verification complete" 2>/dev/null | tail -10 | while read line; do
            timestamp=$(echo "$line" | cut -d',' -f1 | sed 's/.*\([0-9]\{4\}-[0-9]\{2\}-[0-9]\{2\} [0-9]\{2\}:[0-9]\{2\}:[0-9]\{2\}\).*/\1/')

            # Extract faithfulness score
            if [[ $line =~ faithfulness=([0-9.]+) ]]; then
                faith="${BASH_REMATCH[1]}"
                echo "RAGAS|$timestamp|Candidate|Faithfulness|$faith"
            fi

            # Extract relevancy score
            if [[ $line =~ relevancy=([0-9.]+) ]]; then
                rel="${BASH_REMATCH[1]}"
                echo "RAGAS|$timestamp|Candidate|Relevance|$rel"
            fi

            # Extract confidence level
            if [[ $line =~ confidence=([a-z]+) ]]; then
                conf="${BASH_REMATCH[1]}"
                echo "RAGAS|$timestamp|Candidate|Confidence|$conf"
            fi
        done

        # Extract verification.completed events
        tail -500 "$LOG_DIR/verification-worker.log" 2>/dev/null | grep -a "Published event: verification.completed" 2>/dev/null | tail -5 | while read line; do
            timestamp=$(echo "$line" | cut -d',' -f1 | sed 's/.*\([0-9]\{4\}-[0-9]\{2\}-[0-9]\{2\} [0-9]\{2\}:[0-9]\{2\}:[0-9]\{2\}\).*/\1/')
            if [[ $line =~ id=([a-f0-9-]+) ]]; then
                event_id="${BASH_REMATCH[1]}"
                echo "REWARD|$timestamp|Verified-${event_id:0:8}|Verification|Completed"
            fi
        done
    fi

    # Extract DPO pair generation from dataset worker
    if [ -f "$LOG_DIR/dataset-worker.log" ]; then
        # Look for DPO pair creation
        tail -500 "$LOG_DIR/dataset-worker.log" 2>/dev/null | grep -a -iE "dpo|preference|chosen|rejected|pair" 2>/dev/null | tail -15 | while read line; do
            timestamp=$(echo "$line" | cut -d',' -f1 | sed 's/.*\([0-9]\{4\}-[0-9]\{2\}-[0-9]\{2\} [0-9]\{2\}:[0-9]\{2\}:[0-9]\{2\}\).*/\1/')

            if [[ $line =~ chosen ]] || [[ $line =~ best ]]; then
                echo "DPO_CHOSEN|$timestamp|Best Response|$(echo $line | cut -c1-80)"
            elif [[ $line =~ rejected ]] || [[ $line =~ worst ]]; then
                echo "DPO_REJECTED|$timestamp|Worst Response|$(echo $line | cut -c1-80)"
            elif [[ $line =~ pair.*created ]] || [[ $line =~ saved.*dpo ]]; then
                echo "DPO_PAIR|$timestamp|Pair Created|$(echo $line | cut -c1-80)"
            fi
        done

        # Look for file saves
        tail -500 "$LOG_DIR/dataset-worker.log" 2>/dev/null | grep -a -iE "saved|written|created.*file" 2>/dev/null | tail -5 | while read line; do
            timestamp=$(echo "$line" | cut -d',' -f1 | sed 's/.*\([0-9]\{4\}-[0-9]\{2\}-[0-9]\{2\} [0-9]\{2\}:[0-9]\{2\}:[0-9]\{2\}\).*/\1/')
            echo "DPO_PAIR|$timestamp|File Saved|$(echo $line | cut -c1-80)"
        done
    fi
}

# Function to display the dashboard
display_dashboard() {
    clear
    
    local width=120
    
    # Header
    echo ""
    draw_box $width "RLVR PIPELINE LIFECYCLE DASHBOARD" "$CYAN"
    printf "${CYAN}║${NC} ${DIM}Last Updated: $(date '+%Y-%m-%d %H:%M:%S')%*s${CYAN}║${NC}\n" $((width - 45)) ""
    draw_box_bottom $width "$CYAN"
    echo ""

    # System Status
    draw_box $width "SYSTEM STATUS" "$BLUE"
    printf "${BLUE}║${NC} %-116s ${BLUE}║${NC}\n" "Service Health:"

    local services=("API Gateway:8000" "QA Orchestrator:8001" "Document Ingestion:8002" "Streamlit:8501")
    for svc in "${services[@]}"; do
        IFS=':' read -r name port <<< "$svc"
        if curl -s http://localhost:$port/health > /dev/null 2>&1 || curl -s http://localhost:$port > /dev/null 2>&1; then
            printf "${BLUE}║${NC}   ${GREEN}●${NC} %-112s ${BLUE}║${NC}\n" "$name (Port $port) - Running"
        else
            printf "${BLUE}║${NC}   ${RED}●${NC} %-112s ${BLUE}║${NC}\n" "$name (Port $port) - Down"
        fi
    done
    draw_box_bottom $width "$BLUE"
    echo ""

    # Request Flow
    draw_box $width "1. INCOMING REQUESTS" "$MAGENTA"
    printf "${MAGENTA}║${NC} %-20s │ %-93s ${MAGENTA}║${NC}\n" "Timestamp" "Question"
    printf "${MAGENTA}║${NC}$(printf '─%.0s' $(seq 1 118))${MAGENTA}║${NC}\n"

    local question_count=0
    parse_pipeline_data | grep "^QUESTION" | tail -3 | while IFS='|' read -r type timestamp question; do
        printf "${MAGENTA}║${NC} ${CYAN}%-20s${NC} │ %-93s ${MAGENTA}║${NC}\n" "$timestamp" "${question:0:93}"
        ((question_count++))
    done

    if [ $question_count -eq 0 ]; then
        printf "${MAGENTA}║${NC} ${DIM}%-116s${NC} ${MAGENTA}║${NC}\n" "No recent questions found - Send a query to see the pipeline in action"
    fi
    draw_box_bottom $width "$MAGENTA"
    echo ""

    # Worker Responses (Multi-Candidate Generation)
    draw_box $width "2. MULTI-CANDIDATE GENERATION (Workers)" "$YELLOW"
    printf "${YELLOW}║${NC} %-20s │ %-15s │ %-78s ${YELLOW}║${NC}\n" "Timestamp" "Worker ID" "Response Preview"
    printf "${YELLOW}║${NC}$(printf '─%.0s' $(seq 1 118))${YELLOW}║${NC}\n"

    local worker_count=0
    parse_pipeline_data | grep "^WORKER" | tail -5 | while IFS='|' read -r type timestamp worker response; do
        printf "${YELLOW}║${NC} ${CYAN}%-20s${NC} │ ${GREEN}%-15s${NC} │ %-78s ${YELLOW}║${NC}\n" "$timestamp" "$worker" "${response:0:78}"
        ((worker_count++))
    done

    if [ $worker_count -eq 0 ]; then
        printf "${YELLOW}║${NC} ${DIM}%-116s${NC} ${YELLOW}║${NC}\n" "No worker responses found - Workers will generate multiple candidate answers"
    fi
    draw_box_bottom $width "$YELLOW"
    echo ""

    # RAGAS Evaluation & Reward Calculation
    draw_box $width "3. RAGAS EVALUATION & REWARD CALCULATION" "$GREEN"
    printf "${GREEN}║${NC} %-20s │ %-15s │ %-20s │ %-10s │ %-45s ${GREEN}║${NC}\n" "Timestamp" "Worker ID" "Metric" "Score" "Status"
    printf "${GREEN}║${NC}$(printf '─%.0s' $(seq 1 118))${GREEN}║${NC}\n"

    # Store scores by worker for reward calculation display
    declare -A worker_scores
    local ragas_count=0

    while IFS='|' read -r type timestamp worker metric score; do
        local status
        local score_color

        # Determine quality based on score
        if (( $(echo "$score > 0.7" | bc -l 2>/dev/null || echo 0) )); then
            status="✓ High Quality"
            score_color="${GREEN}"
        elif (( $(echo "$score > 0.5" | bc -l 2>/dev/null || echo 0) )); then
            status="~ Medium Quality"
            score_color="${YELLOW}"
        else
            status="✗ Low Quality"
            score_color="${RED}"
        fi

        printf "${GREEN}║${NC} ${CYAN}%-20s${NC} │ ${BLUE}%-15s${NC} │ %-20s │ ${score_color}%-10s${NC} │ %-45s ${GREEN}║${NC}\n" \
            "$timestamp" "$worker" "$metric" "$score" "$status"

        # Track scores for reward calculation
        worker_scores["$worker,$metric"]="$score"
        ((ragas_count++))
    done < <(parse_pipeline_data | grep "^RAGAS" | tail -15)

    # Display total rewards
    if [ $ragas_count -gt 0 ]; then
        printf "${GREEN}║${NC}$(printf '─%.0s' $(seq 1 118))${GREEN}║${NC}\n"

        while IFS='|' read -r type timestamp worker metric reward; do
            printf "${GREEN}║${NC} ${CYAN}%-20s${NC} │ ${BOLD}${BLUE}%-15s${NC} │ ${BOLD}%-20s${NC} │ ${BOLD}${MAGENTA}%-10s${NC} │ %-45s ${GREEN}║${NC}\n" \
                "$timestamp" "$worker" "$metric" "$reward" "⭐ Final Reward Score"
        done < <(parse_pipeline_data | grep "^REWARD" | tail -5)
    fi

    if [ $ragas_count -eq 0 ]; then
        printf "${GREEN}║${NC} ${DIM}%-116s${NC} ${GREEN}║${NC}\n" "No RAGAS scores found - Evaluation metrics will appear here"
    fi

    printf "${GREEN}║${NC}$(printf '─%.0s' $(seq 1 118))${GREEN}║${NC}\n"
    printf "${GREEN}║${NC} ${BOLD}Reward Formula:${NC} R = w₁·Faithfulness + w₂·Relevance + w₃·Correctness%-50s ${GREEN}║${NC}\n" ""
    draw_box_bottom $width "$GREEN"
    echo ""

    # DPO Pair Generation - DETAILED VIEW
    draw_box $width "4. DPO PREFERENCE PAIR GENERATION" "$CYAN"
    printf "${CYAN}║${NC} ${BOLD}%-116s${NC} ${CYAN}║${NC}\n" "Best vs Worst Response Selection for Training"
    printf "${CYAN}║${NC}$(printf '─%.0s' $(seq 1 118))${CYAN}║${NC}\n"

    # Show chosen response
    local chosen_count=0
    while IFS='|' read -r type timestamp worker response; do
        if [ $chosen_count -eq 0 ]; then
            printf "${CYAN}║${NC} ${BOLD}${GREEN}CHOSEN RESPONSE (Highest Reward):${NC}%-82s ${CYAN}║${NC}\n" ""
            printf "${CYAN}║${NC}$(printf '─%.0s' $(seq 1 118))${CYAN}║${NC}\n"
        fi
        printf "${CYAN}║${NC} ${CYAN}%-20s${NC} │ ${GREEN}%-15s${NC} │ %-78s ${CYAN}║${NC}\n" "$timestamp" "$worker" "${response:0:78}"
        ((chosen_count++))
    done < <(parse_pipeline_data | grep "^DPO_CHOSEN" | tail -3)

    if [ $chosen_count -eq 0 ]; then
        printf "${CYAN}║${NC} ${BOLD}${GREEN}CHOSEN RESPONSE:${NC}%-99s ${CYAN}║${NC}\n" ""
        printf "${CYAN}║${NC}   ${DIM}No chosen response yet${NC}%-88s ${CYAN}║${NC}\n" ""
    fi

    printf "${CYAN}║${NC}$(printf '─%.0s' $(seq 1 118))${CYAN}║${NC}\n"

    # Show rejected response
    local rejected_count=0
    while IFS='|' read -r type timestamp worker response; do
        if [ $rejected_count -eq 0 ]; then
            printf "${CYAN}║${NC} ${BOLD}${RED}REJECTED RESPONSE (Lowest Reward):${NC}%-81s ${CYAN}║${NC}\n" ""
            printf "${CYAN}║${NC}$(printf '─%.0s' $(seq 1 118))${CYAN}║${NC}\n"
        fi
        printf "${CYAN}║${NC} ${CYAN}%-20s${NC} │ ${RED}%-15s${NC} │ %-78s ${CYAN}║${NC}\n" "$timestamp" "$worker" "${response:0:78}"
        ((rejected_count++))
    done < <(parse_pipeline_data | grep "^DPO_REJECTED" | tail -3)

    if [ $rejected_count -eq 0 ]; then
        printf "${CYAN}║${NC} ${BOLD}${RED}REJECTED RESPONSE:${NC}%-97s ${CYAN}║${NC}\n" ""
        printf "${CYAN}║${NC}   ${DIM}No rejected response yet${NC}%-86s ${CYAN}║${NC}\n" ""
    fi

    printf "${CYAN}║${NC}$(printf '─%.0s' $(seq 1 118))${CYAN}║${NC}\n"

    # Show pair creation status
    local pair_count=0
    while IFS='|' read -r type timestamp status details; do
        printf "${CYAN}║${NC} ${BOLD}${MAGENTA}DPO PAIR STATUS:${NC} %-98s ${CYAN}║${NC}\n" "$status"
        printf "${CYAN}║${NC}   ${CYAN}Time:${NC} %-109s ${CYAN}║${NC}\n" "$timestamp"
        ((pair_count++))
    done < <(parse_pipeline_data | grep "^DPO_PAIR" | tail -1)

    if [ $pair_count -eq 0 ]; then
        printf "${CYAN}║${NC} ${BOLD}${MAGENTA}DPO PAIR STATUS:${NC} %-98s ${CYAN}║${NC}\n" "Waiting for pair creation..."
    fi

    printf "${CYAN}║${NC}$(printf '─%.0s' $(seq 1 118))${CYAN}║${NC}\n"
    printf "${CYAN}║${NC} ${BOLD}DPO Training Logic:${NC}%-96s ${CYAN}║${NC}\n" ""
    printf "${CYAN}║${NC}   • ${GREEN}Chosen:${NC}   Response with highest reward (best quality)%-58s ${CYAN}║${NC}\n" ""
    printf "${CYAN}║${NC}   • ${RED}Rejected:${NC} Response with lowest reward (worst quality)%-57s ${CYAN}║${NC}\n" ""
    printf "${CYAN}║${NC}   • ${YELLOW}Objective:${NC} Train model to prefer chosen over rejected%-55s ${CYAN}║${NC}\n" ""
    draw_box_bottom $width "$CYAN"
    echo ""

    # DPO Data Storage
    draw_box $width "5. DPO DATA STORAGE & FILES" "$WHITE"

    local dpo_files=$(find "$DATA_DIR" -type f \( -name "*dpo*.json" -o -name "*dpo*.jsonl" -o -name "*preference*.json" \) 2>/dev/null | wc -l)
    local training_files=$(find "$DATA_DIR" -type f -path "*/training/*" \( -name "*.json" -o -name "*.jsonl" \) 2>/dev/null | wc -l)

    printf "${WHITE}║${NC} ${BOLD}Storage Location:${NC} %-99s ${WHITE}║${NC}\n" "$DATA_DIR/dpo/"
    printf "${WHITE}║${NC} ${BOLD}DPO Files:${NC} %-15s ${BOLD}Training Files:${NC} %-79s ${WHITE}║${NC}\n" "$dpo_files" "$training_files"

    if [ $dpo_files -gt 0 ]; then
        printf "${WHITE}║${NC}$(printf '─%.0s' $(seq 1 118))${WHITE}║${NC}\n"
        printf "${WHITE}║${NC} ${BOLD}Recent DPO Files:${NC}%-99s ${WHITE}║${NC}\n" ""

        find "$DATA_DIR" -type f \( -name "*dpo*.json" -o -name "*dpo*.jsonl" \) 2>/dev/null | \
            head -5 | while read file; do
                local size=$(du -h "$file" 2>/dev/null | cut -f1)
                local name=$(basename "$file")
                local modified=$(stat -f "%Sm" -t "%Y-%m-%d %H:%M" "$file" 2>/dev/null || stat -c "%y" "$file" 2>/dev/null | cut -d'.' -f1)
                printf "${WHITE}║${NC}   ${GREEN}●${NC} %-80s ${CYAN}%s${NC} ${DIM}%s${NC}%*s ${WHITE}║${NC}\n" \
                    "${name:0:80}" "$size" "${modified:0:16}" $((15 - ${#size})) ""
            done
    else
        printf "${WHITE}║${NC}$(printf '─%.0s' $(seq 1 118))${WHITE}║${NC}\n"
        printf "${WHITE}║${NC} ${DIM}%-116s${NC} ${WHITE}║${NC}\n" "No DPO files found yet - Files will be saved after pair generation"
    fi

    draw_box_bottom $width "$WHITE"
    echo ""

    # Pipeline Flow Diagram
    draw_box $width "COMPLETE PIPELINE FLOW" "$BLUE"
    printf "${BLUE}║${NC}%-118s${BLUE}║${NC}\n" ""
    printf "${BLUE}║${NC}  ${MAGENTA}[1. Question]${NC} → ${YELLOW}[2. Workers]${NC} → ${GREEN}[3. RAGAS]${NC} → ${CYAN}[4. DPO Pair]${NC} → ${WHITE}[5. Storage]${NC}%*s${BLUE}║${NC}\n" 30 ""
    printf "${BLUE}║${NC}%-118s${BLUE}║${NC}\n" ""
    printf "${BLUE}║${NC}       ↓               ↓              ↓               ↓                ↓%*s${BLUE}║${NC}\n" 34 ""
    printf "${BLUE}║${NC}   Received        Generate       Calculate       Select Best      Save to%*s${BLUE}║${NC}\n" 32 ""
    printf "${BLUE}║${NC}   via API        Multiple       Rewards         & Worst         Training%*s${BLUE}║${NC}\n" 31 ""
    printf "${BLUE}║${NC}                  Candidates     (RAGAS)         Responses        Dataset%*s${BLUE}║${NC}\n" 32 ""
    printf "${BLUE}║${NC}%-118s${BLUE}║${NC}\n" ""
    draw_box_bottom $width "$BLUE"
    echo ""

    # Footer with instructions
    if [ "$AUTO_REFRESH" == "--auto" ] || [ "$AUTO_REFRESH" == "-a" ]; then
        printf "${BOLD}${GREEN}⟳ Auto-refreshing every 5 seconds | Press Ctrl+C to exit${NC}\n"
    else
        printf "${BOLD}${YELLOW}Press ENTER to refresh | Ctrl+C to exit | Run with --auto for auto-refresh${NC}\n"
    fi
    echo ""
}

# Main function
main() {
    echo "Starting RLVR Pipeline Dashboard..."
    echo "Initializing..."
    sleep 1

    # Check if auto-refresh is requested
    AUTO_REFRESH=${1:-""}

    if [ "$AUTO_REFRESH" == "--auto" ] || [ "$AUTO_REFRESH" == "-a" ]; then
        echo "Auto-refresh mode enabled (5 second intervals)"
        echo "Press Ctrl+C to exit"
        sleep 2

        while true; do
            display_dashboard
            sleep 5
        done
    else
        echo "Manual refresh mode (press ENTER to refresh)"
        sleep 1

        while true; do
            display_dashboard
            read -r
        done
    fi
}

# Run the dashboard
main "$@"

