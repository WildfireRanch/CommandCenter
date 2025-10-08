# 🚀 START HERE: Session 020 - Build Energy Orchestrator

**Welcome to your next CommandCenter session!**

---

## 📍 Where You Are

**System Status:** V1.5 at 80% complete
**Last Session:** 019 - Orchestration Layer Complete
**This Session:** Build Energy Orchestrator Agent
**Next Session:** Polish & Ship V1.5! 🎉

---

## 🎯 Your Task

Build the **Energy Orchestrator Agent** - an intelligent planning system that:
- Optimizes battery charge/discharge
- Controls bitcoin miner operations
- Creates 24-hour energy action plans
- Uses policies from Knowledge Base

**Time Required:** 6-8 hours (one focused session)

---

## 📖 Full Instructions

**👉 Open this file:** [docs/NEXT_SESSION_PROMPT_020.md](docs/NEXT_SESSION_PROMPT_020.md)

This file contains:
- Complete step-by-step instructions
- Code templates for all 3 tools
- Agent creation guide
- Testing procedures
- Deployment steps
- Troubleshooting help

**Copy the entire contents** of that file and paste it into a new Claude Code chat to begin.

---

## 📚 Key Documents to Read First

Before you start coding, skim these (5-10 min):

1. **[docs/CODEBASE_AUDIT_OCT2025.md](docs/CODEBASE_AUDIT_OCT2025.md)**
   - Complete system inventory
   - Shows what exists, what's missing
   - You'll reference this often

2. **[docs/ORCHESTRATION_LAYER_DESIGN.md](docs/ORCHESTRATION_LAYER_DESIGN.md)**
   - Manager agent architecture
   - Routing logic examples
   - Shows how to integrate new agents

3. **[docs/sessions/SESSION_019_ORCHESTRATION_SUMMARY.md](docs/sessions/SESSION_019_ORCHESTRATION_SUMMARY.md)**
   - Last session summary
   - What was accomplished
   - Current state

---

## 🏗️ What You'll Build

### 3 Tools:
1. **Battery Optimizer** (`railway/src/tools/battery_optimizer.py`)
   - Recommends charge/discharge actions
   - Based on SOC, time, weather

2. **Miner Coordinator** (`railway/src/tools/miner_coordinator.py`)
   - Decides when to run bitcoin miners
   - Based on available power and SOC

3. **Energy Planner** (`railway/src/tools/energy_planner.py`)
   - Creates 24-hour action plans
   - Hour-by-hour scheduling

### 1 Agent:
**Energy Orchestrator** (`railway/src/agents/energy_orchestrator.py`)
- Uses the 3 tools above
- Searches KB for policies
- Gets current status from Solar Controller
- Makes intelligent planning decisions

### Manager Integration:
- Add routing to Manager agent
- Manager will route planning queries to Orchestrator
- Test end-to-end flow

---

## ✅ Success Criteria

**You're done when:**
- [ ] All 3 tools working individually
- [ ] Energy Orchestrator agent created
- [ ] Manager routes planning queries correctly
- [ ] Integration tests pass
- [ ] Deployed to Railway
- [ ] No critical errors

---

## 🎉 After This Session

**You'll have:**
- ✅ Energy Orchestrator operational
- ✅ Manager routing to 3 agents (Solar Controller, Orchestrator, KB)
- ✅ V1.5 at 95% complete!

**Then ONE MORE SESSION:**
- Polish chat interface (2-3 hours)
- Add source display
- End-to-end testing
- **Ship V1.5! 🚀**

---

## 🚀 Ready to Start?

1. Open [docs/NEXT_SESSION_PROMPT_020.md](docs/NEXT_SESSION_PROMPT_020.md)
2. Copy the entire contents
3. Start a new Claude Code chat
4. Paste the prompt
5. Follow the step-by-step instructions

**Good luck! You're almost there!** 💪

---

**System Status:** All documentation updated and committed
**Git Status:** All changes pushed to GitHub
**Deployment:** Railway auto-deploying latest commit
**Ready to code:** YES! ✅
