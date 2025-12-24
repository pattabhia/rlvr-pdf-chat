# 🎬 Simple UI Demo - Watch Your Query Flow!

## 🚀 Super Simple Setup

### Step 1: Pull Latest Code
```bash
cd /workspace/rlvr-automation
git pull origin main
```

### Step 2: Start the Watcher
```bash
./watch-pipeline.sh
```

### Step 3: Enter Query in UI
Go to your UI and enter a question like:
- "What is AWS Lambda?"
- "How do I troubleshoot S3 access issues?"
- "What are AWS Support plans?"

### Step 4: Watch the Magic! ✨
The terminal will show in real-time:
1. ✅ Question received
2. ✅ 3 candidates generated
3. ✅ Each candidate scored (with progress bars!)
4. ✅ DPO analysis (best vs worst)
5. ✅ Training data saved

---

## 📊 What You'll See

```
╔════════════════════════════════════════════════════════════════════════════╗
║  📥 NEW QUESTION RECEIVED [11:30:15]
╚════════════════════════════════════════════════════════════════════════════╝
What is AWS Lambda and how does it work?

  ✅ Candidate #1 generated (ID: a1b2c3d4)
  ✅ Candidate #2 generated (ID: e5f6g7h8)
  ✅ Candidate #3 generated (ID: i9j0k1l2)
  🎯 All 3 candidates generated!

  📊 Verification #1:
     Faithfulness: ████████████████░░░░ 0.820
     Relevancy:    ██████████████████░░ 0.875
     Overall:      █████████████████░░░ 0.848 [high]

  📊 Verification #2:
     Faithfulness: ████████████░░░░░░░░ 0.650
     Relevancy:    ██████████████░░░░░░ 0.720
     Overall:      █████████████░░░░░░░ 0.685 [low]

  📊 Verification #3:
     Faithfulness: ██████████░░░░░░░░░░ 0.520
     Relevancy:    ████████████░░░░░░░░ 0.610
     Overall:      ███████████░░░░░░░░░ 0.565 [low]

  ═══════════════════════════════════════════════════════════════════
  📈 DPO SCORE ANALYSIS
  ═══════════════════════════════════════════════════════════════════
     Best:       █████████████████░░░ 0.848
     Worst:      ███████████░░░░░░░░░ 0.565
     Difference: 0.283 ❌ Skipped (need ≥0.3)
  ═══════════════════════════════════════════════════════════════════

  💾 Training data saved
  ✨ Entry complete! Total entries: 42

╚════════════════════════════════════════════════════════════════════════════╝

Waiting for next question...
```

---

## 🎯 Alternative Watchers

### Watch DPO Pairs Only
```bash
./watch-dpo.sh
```
Shows only when DPO pairs are created with full chosen/rejected text.

### Watch Training Data Only
```bash
./watch-training.sh
```
Shows each training entry as it's written to JSONL.

---

## 💡 Tips

1. **Best for demo:** Use `./watch-pipeline.sh` - shows everything!
2. **Color-coded scores:**
   - 🟢 Green bars = high score (≥0.8)
   - 🟡 Yellow bars = medium score (0.6-0.8)
   - 🔴 Red bars = low score (<0.6)
3. **DPO creation:** Needs score difference ≥0.3 AND best score ≥0.7
4. **Stop watching:** Press Ctrl+C

---

## 🔧 Troubleshooting

**Nothing showing up?**
```bash
# Check if workers are running
ps aux | grep worker

# Restart workers if needed
./runpod-start.sh

# Check logs exist
ls -lh /workspace/logs/
```

**Old data showing?**
- That's normal! The watcher shows historical data first
- Send a new query to see fresh output

**Want to see past data?**
```bash
# View dashboard
./rlvr-dashboard.sh --auto

# Debug logs
./debug-logs.sh
```

---

## 🎊 That's It!

Just run `./watch-pipeline.sh` and enter queries in your UI!

**Perfect for demos - one terminal, real-time updates, beautiful formatting!** ✨

