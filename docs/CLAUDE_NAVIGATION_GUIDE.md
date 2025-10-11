# Claude Navigation Guide for CommandCenter

**Purpose:** Guide Claude Code/AI assistants to navigate CommandCenter documentation efficiently
**Last Updated:** December 10, 2025 (V1.5.0 Release)

---

## 🎯 Quick Start for AI Assistants

When working with CommandCenter, **ALWAYS start here:**

### 1. **First Thing to Read**
```
docs/V1.5_MASTER_REFERENCE.md
```
This is the **PRIMARY REFERENCE** for current system state. Contains:
- Architecture diagram
- All API endpoints
- Database schema
- Active agents and tools
- Environment variables
- Quick troubleshooting

**Read this FIRST before answering questions about current system.**

### 2. **Second Thing to Check**
```
docs/INDEX.md
```
Complete documentation index showing where everything is located.

---

## 📂 Documentation Structure

### **Root Level (docs/)**
Core documentation only (9 files):
```
V1.5_MASTER_REFERENCE.md          ← START HERE
INDEX.md                           ← Navigation
05-architecture.md                 ← Detailed architecture
06-knowledge-base-design.md        ← KB system design
07-knowledge-base-sync.md          ← KB implementation
08-Remaining_v1-5.md               ← V1.5 checklist
ORCHESTRATION_LAYER_DESIGN.md     ← Manager agent design
ARCHIVE_SUMMARY.md                 ← Organization guide
CLAUDE_NAVIGATION_GUIDE.md         ← This file
```

### **Organized Folders**
```
docs/
├── guides/          ← How-to guides (4 files)
├── reference/       ← Standards & conventions (3 files)
├── status/          ← Status reports (5 files)
├── deployment/      ← Deployment guides (5 files)
├── sessions/        ← Development history (30 files)
└── archive/         ← Historical docs (44 files)
```

---

## 🔍 Navigation Rules for Common Questions

### Question: "What's the current system architecture?"
**Read:**
1. `V1.5_MASTER_REFERENCE.md` - Architecture Diagram section
2. `05-architecture.md` - Detailed architecture (if needed)

### Question: "How do I deploy this?"
**Read:**
1. `deployment/` folder - Check README.md first
2. Railway: `deployment/RAILWAY_DEPLOYMENT_OPTIMIZATION.md`
3. Vercel: `deployment/VERCEL_DEPLOYMENT.md`

### Question: "What agents are available?"
**Read:**
1. `V1.5_MASTER_REFERENCE.md` - Active Agents section
2. `ORCHESTRATION_LAYER_DESIGN.md` - Manager agent details

### Question: "How do I authenticate?"
**Read:**
1. `guides/AUTHENTICATION_GUIDE.md`

### Question: "What are the API endpoints?"
**Read:**
1. `V1.5_MASTER_REFERENCE.md` - API Endpoints section

### Question: "What's in the database?"
**Read:**
1. `V1.5_MASTER_REFERENCE.md` - Database Schema section

### Question: "How do I test the KB?"
**Read:**
1. `guides/KB_USER_TESTING_GUIDE.md`

### Question: "What are the code standards?"
**Read:**
1. `reference/CommandCenter Code Style Guide.md`

### Question: "What was completed in V1.5?"
**Read:**
1. `status/V1.5_COMPLETION_STATUS.md`

### Question: "Why was X designed this way?"
**Read:**
1. `05-architecture.md` - Design decisions with history
2. `sessions/SESSION_0XX_SUMMARY.md` - Specific session

### Question: "What happened in early development?"
**Read:**
1. `archive/early-sessions/` - Sessions 001-011
2. `archive/v1-planning/` - Original planning

---

## 🚫 What NOT to Read (Unless Necessary)

### **archive/** Folder
Historical documentation - only read if:
- User asks about history/decisions
- Need to understand why something was built certain way
- Researching evolution of a feature

**Don't read archive/ for current system state!**

### **sessions/** Folder
Development history - only read if:
- User asks about specific session
- Need implementation details from when feature was built
- Debugging something that broke recently

**Don't read all sessions! Use INDEX.md to find relevant one.**

---

## 💡 Efficient Navigation Patterns

### Pattern 1: User Asks About Current System
```
1. Read: V1.5_MASTER_REFERENCE.md (relevant section)
2. If more detail needed: Read specific doc (05-08.md)
3. Answer user with current state
```

### Pattern 2: User Asks How to Do Something
```
1. Check: guides/ folder README
2. Read: Relevant guide
3. If not in guides/: Check deployment/ or reference/
4. Answer with step-by-step instructions
```

### Pattern 3: User Reports Bug/Issue
```
1. Read: V1.5_MASTER_REFERENCE.md (troubleshooting section)
2. Check: Relevant component in architecture
3. If recent change: Check sessions/ for latest work
4. Diagnose and suggest fix
```

### Pattern 4: User Asks About Feature Implementation
```
1. Read: V1.5_MASTER_REFERENCE.md (to understand current)
2. Search: sessions/ for implementation (use INDEX.md)
3. Read: Specific session summary
4. Explain implementation
```

### Pattern 5: User Wants to Modify System
```
1. Read: V1.5_MASTER_REFERENCE.md (current state)
2. Read: reference/Code Style Guide.md
3. Read: Relevant architecture section (05-08.md)
4. Plan changes following standards
```

---

## 📋 Prompt Templates for Humans

### Template 1: Understanding Current System
```
I need to understand [COMPONENT]. Please:
1. Read docs/V1.5_MASTER_REFERENCE.md
2. Explain how [COMPONENT] works
3. Show me the relevant code locations
```

### Template 2: How to Deploy/Setup
```
I need to deploy/setup [FEATURE]. Please:
1. Check docs/deployment/ or docs/guides/
2. Give me step-by-step instructions
3. Include all environment variables needed
```

### Template 3: Adding New Feature
```
I want to add [FEATURE]. Please:
1. Read current architecture (V1.5_MASTER_REFERENCE.md)
2. Read code style guide (reference/)
3. Suggest implementation approach
4. Show where to add code
```

### Template 4: Debugging Issue
```
[ISSUE DESCRIPTION]. Please:
1. Check V1.5_MASTER_REFERENCE.md troubleshooting
2. Review relevant component architecture
3. Check recent sessions/ for related changes
4. Help me debug
```

### Template 5: Historical Context
```
Why was [DECISION] made? Please:
1. Check archive/v1-planning/ for original design
2. Check sessions/ for implementation discussion
3. Explain the reasoning
```

---

## 🎨 Best Practices for AI Assistants

### DO:
✅ Always read V1.5_MASTER_REFERENCE.md first
✅ Use INDEX.md to find specific docs
✅ Check folder READMEs before diving into files
✅ Prefer current docs over archive
✅ Reference file paths in answers (e.g., `railway/src/agents/manager.py:42`)
✅ Use markdown links for file references: `[filename](path/to/file)`

### DON'T:
❌ Read entire sessions/ folder linearly
❌ Start with archive/ unless user asks for history
❌ Assume old docs are current
❌ Skip V1.5_MASTER_REFERENCE.md
❌ Read all files before answering simple questions
❌ Ignore folder structure/organization

---

## 🗺️ Documentation Map by Purpose

### Current System State
- **Primary:** V1.5_MASTER_REFERENCE.md
- **Detailed:** 05-architecture.md
- **Components:** 06-knowledge-base-design.md, 07-knowledge-base-sync.md
- **Agents:** ORCHESTRATION_LAYER_DESIGN.md

### How-To Guides
- **Folder:** guides/
- **Auth:** guides/AUTHENTICATION_GUIDE.md
- **Testing:** guides/KB_USER_TESTING_GUIDE.md

### Reference Material
- **Folder:** reference/
- **Standards:** reference/CommandCenter Code Style Guide.md
- **Progress:** reference/progress.md

### Deployment
- **Folder:** deployment/
- **Railway:** deployment/RAILWAY_*.md
- **Vercel:** deployment/VERCEL_DEPLOYMENT.md

### Status & Completion
- **Folder:** status/
- **V1.5 Complete:** status/V1.5_COMPLETION_STATUS.md
- **Audit:** status/CODEBASE_AUDIT_OCT2025.md

### Historical Context
- **Folder:** archive/
- **Planning:** archive/v1-planning/
- **Early Work:** archive/early-sessions/
- **Session Planning:** archive/session-planning/

---

## 🔧 Troubleshooting Navigation Issues

### "I can't find documentation about X"
1. Check INDEX.md
2. Check V1.5_MASTER_REFERENCE.md table of contents
3. Check relevant folder README.md
4. If still not found, check archive/ (may be deprecated)

### "Documentation seems outdated"
1. Check date in file header
2. If older than V1.5 release (Dec 2025), check archive/
3. Prefer V1.5_MASTER_REFERENCE.md for current state

### "Too many session files to search"
1. Use INDEX.md "Session History" section
2. Session summaries grouped by topic
3. Only read specific session if needed

### "Conflicting information in different docs"
1. V1.5_MASTER_REFERENCE.md is authoritative
2. Older docs may contain historical info
3. Check file dates to determine current state

---

## 📖 Example Navigation Workflows

### Workflow 1: New AI Assistant Starting Fresh
```
1. Read: docs/V1.5_MASTER_REFERENCE.md (entire file)
2. Read: docs/INDEX.md (overview)
3. Skim: docs/ARCHIVE_SUMMARY.md (understand organization)
4. Ready to answer questions!
```

### Workflow 2: Answering Architecture Question
```
User: "How does the KB fast-path work?"
1. Read: V1.5_MASTER_REFERENCE.md → "KB Fast-Path System"
2. If more detail: 05-architecture.md → KB Fast-Path section
3. Answer with code examples and performance metrics
```

### Workflow 3: Implementing New Feature
```
User: "Add a new agent for weather forecasting"
1. Read: V1.5_MASTER_REFERENCE.md → "Active Agents"
2. Read: ORCHESTRATION_LAYER_DESIGN.md → Agent patterns
3. Read: reference/Code Style Guide.md → Agent conventions
4. Plan implementation following patterns
5. Create new agent following standards
```

### Workflow 4: Debugging Production Issue
```
User: "KB search is timing out"
1. Read: V1.5_MASTER_REFERENCE.md → "Quick Troubleshooting" → "Agent Timeout"
2. Check: V1.5_MASTER_REFERENCE.md → "KB Fast-Path System"
3. Read: 05-architecture.md → "KB Fast-Path Implementation"
4. Check: sessions/SESSION_024_*.md (performance optimization)
5. Diagnose and fix
```

---

## 🎓 Learning Path for New AI Assistants

### Level 1: Essential (Required for all questions)
1. V1.5_MASTER_REFERENCE.md
2. INDEX.md

### Level 2: Architecture (For system understanding)
1. 05-architecture.md
2. ORCHESTRATION_LAYER_DESIGN.md
3. 06-knowledge-base-design.md

### Level 3: Implementation (For code changes)
1. reference/Code Style Guide.md
2. Relevant component docs (07, 08, etc.)
3. Recent sessions/ for examples

### Level 4: Historical (For context/decisions)
1. archive/v1-planning/
2. archive/early-sessions/
3. Specific session summaries

---

## 💬 Communication Tips

### When Answering Questions
- Always cite file locations: `See railway/src/agents/manager.py:42`
- Use markdown links: `[Manager Agent](railway/src/agents/manager.py)`
- Reference doc sections: "Per V1.5_MASTER_REFERENCE.md, the KB fast-path..."
- Be specific about current vs. historical info

### When Suggesting Changes
- Follow code style guide
- Reference existing patterns from V1.5_MASTER_REFERENCE.md
- Point to similar implementations in codebase
- Consider impact on documented architecture

### When Unsure
- Say "Let me check the documentation..."
- Read relevant section
- Provide answer with source citation
- Better to take 30 seconds to check than give wrong info

---

## 📝 Summary

**Golden Rule:** V1.5_MASTER_REFERENCE.md is your primary source for current system state.

**Navigation Hierarchy:**
1. V1.5_MASTER_REFERENCE.md (current state)
2. Specific component docs (05-08, ORCHESTRATION)
3. Guides/reference folders (how-to)
4. Sessions (recent implementation)
5. Archive (historical context)

**Key Principle:** Start specific (primary reference), expand as needed. Don't read everything to answer simple questions.

---

**End of Navigation Guide**

This guide helps AI assistants navigate CommandCenter documentation efficiently. For humans: use this as a template for asking questions!
