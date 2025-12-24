#!/bin/bash

# RLVR Pipeline Demo Setup
# Prepares all monitoring scripts for multi-terminal demo

echo "╔════════════════════════════════════════════════════════════════════════════╗"
echo "║                    RLVR PIPELINE DEMO SETUP                                ║"
echo "╔════════════════════════════════════════════════════════════════════════════╗"
echo ""

# Make all monitoring scripts executable
echo "Making monitoring scripts executable..."
chmod +x monitor-candidates.sh
chmod +x monitor-ragas.sh
chmod +x monitor-rewards.sh
chmod +x monitor-dpo.sh
chmod +x rlvr-dashboard.sh
chmod +x debug-logs.sh

echo "✅ All scripts are now executable"
echo ""

echo "════════════════════════════════════════════════════════════════════════════"
echo "  DEMO INSTRUCTIONS"
echo "════════════════════════════════════════════════════════════════════════════"
echo ""
echo "Open 4 separate terminals and run these commands:"
echo ""
echo "📺 TERMINAL 1 - Multi-Candidate Generation:"
echo "   ./monitor-candidates.sh"
echo ""
echo "📺 TERMINAL 2 - RAGAS Evaluation & Scoring:"
echo "   ./monitor-ragas.sh"
echo ""
echo "📺 TERMINAL 3 - Reward Calculation:"
echo "   ./monitor-rewards.sh"
echo ""
echo "📺 TERMINAL 4 - DPO Pair Generation:"
echo "   ./monitor-dpo.sh"
echo ""
echo "════════════════════════════════════════════════════════════════════════════"
echo ""
echo "Then send a test question:"
echo ""
echo "curl -X POST http://localhost:8001/ask/multi-candidate \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"question\": \"What is AWS Lambda and how does it work?\", \"num_candidates\": 3}'"
echo ""
echo "════════════════════════════════════════════════════════════════════════════"
echo ""
echo "Watch the pipeline flow through all 4 terminals! 🚀"
echo ""

