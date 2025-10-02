# Phase 1: Discovery - Selective Porting Approach

## Philosophy: Fresh Start with Selective Import

**Approach:** Start with clean slate, audit old code, import only what's proven and working.

**Why this matters:**
- Avoid inheriting bugs and technical debt
- Opportunity to rethink architecture
- Document what you're bringing over (and why)
- Learn what each piece does in the process
- Build on solid foundation

---

## Discovery Sub-Phases

### 1.1: Old Stack Audit (2-3 hours)

**Goal:** Document what exists, what works, what doesn't

**Deliverable:** `docs/01-old-stack-audit.md`

**Tasks:**
- [ ] List all code files in old repo
- [ ] Document what each file/module does
- [ ] Rate each component:
  - ✅ **KEEP** - Works well, bring over as-is
  - 🔧 **REFACTOR** - Good logic, needs cleanup
  - ♻️ **REWRITE** - Good idea, bad implementation
  - ❌ **SKIP** - Buggy/unused/outdated
- [ ] Identify dependencies between components
- [ ] Note any configuration files needed

**Questions to answer:**
- What agents/functions exist?
- Which ones actually work?
- Which ones do you use regularly?
- What's the core functionality you need?
- What can be left behind?

**Template for each component:**
```markdown
### Component: [Name]
- **File:** path/to/file.py
- **Purpose:** What it does
- **Status:** Working / Buggy / Unused
- **Decision:** KEEP / REFACTOR / REWRITE / SKIP
- **Reason:** Why this decision
- **Dependencies:** What it needs
- **Priority:** High / Medium / Low
```

---

### 1.2: Functional Requirements (1-2 hours)

**Goal:** Define what the NEW system must do

**Deliverable:** `docs/02-requirements.md`

**Tasks:**
- [ ] List core features (must-have)
- [ ] List nice-to-have features
- [ ] Define success criteria
- [ ] Identify data sources needed
- [ ] Document workflows
- [ ] Note performance requirements
- [ ] Define budget constraints

**Questions to answer:**
- What problems are you solving?
- Who/what will use this system?
- What are the critical paths?
- What can wait for v2?

**Template:**
```markdown
## Must-Have Features
1. [Feature] - Why: [reason] - Priority: [1-5]

## Nice-to-Have Features
1. [Feature] - Why: [reason] - Can defer: [yes/no]

## Workflows
1. [Workflow name]
   - Step 1: [action]
   - Step 2: [action]
   - Expected outcome: [result]

## Data Sources
- [Source 1]: [What data / How accessed]
- [Source 2]: [What data / How accessed]

## Performance Requirements
- Response time: [target]
- Concurrent users: [number]
- Uptime target: [percentage]

## Budget
- Monthly budget: $[amount]
- One-time setup: $[amount]
```

---

### 1.3: Selective Port Plan (1-2 hours)

**Goal:** Create migration strategy for chosen components

**Deliverable:** `docs/03-port-plan.md`

**Tasks:**
- [ ] Prioritize components to port
- [ ] Create migration order
- [ ] Identify code that can be directly copied
- [ ] Identify code that needs refactoring
- [ ] Plan for testing each ported component
- [ ] Document dependencies to resolve

**Migration Priority Matrix:**
```markdown
## High Priority (Port First)
1. [Component name]
   - From: old-repo/path/file.py
   - To: commandcenter/src/agents/new_name.py
   - Strategy: KEEP / REFACTOR / REWRITE
   - Dependencies: [list]
   - Estimated time: [hours]

## Medium Priority (Port Second)
[same format]

## Low Priority (Port Later/Maybe)
[same format]

## Skip (Not Porting)
1. [Component name]
   - Reason: [why skipping]
```

---

### 1.4: Architecture Design (2-3 hours)

**Goal:** Design NEW system architecture (clean slate)

**Deliverable:** `docs/04-architecture.md` + diagram

**Tasks:**
- [ ] Design agent roles and responsibilities
- [ ] Map data flows
- [ ] Define MCP integration points
- [ ] Plan service architecture
- [ ] Design folder structure
- [ ] Document deployment strategy
- [ ] Create visual diagram

**Questions to answer:**
- How many agents do you need?
- What role does each play?
- How do they communicate?
- Where does data live?
- How does MCP fit in?
- What runs where (Vercel vs Railway)?

---

## Discovery Workflow

### Week 1: Understanding

**Day 1-2: Old Stack Audit**
```bash
# In your old repo (just for reading):
1. Open old codebase (read-only)
2. Go through each file
3. Document in audit spreadsheet/markdown
4. Rate: KEEP/REFACTOR/REWRITE/SKIP
```

**Day 3: Requirements Definition**
```bash
1. Review audit results
2. Write down what you actually need
3. Separate must-have from nice-to-have
4. Define success criteria
```

**Day 4: Port Planning**
```bash
1. From audit + requirements
2. Decide what to port and in what order
3. Create migration checklist
4. Estimate time for each component
```

**Day 5: Architecture Design**
```bash
1. Design NEW system (fresh thinking)
2. Incorporate ported components
3. Create visual diagram
4. Document decisions
```

---

## Porting Strategies

### Strategy 1: KEEP (Copy as-is)
```python
# When: Code works perfectly, no changes needed
# Process:
1. Copy file from old repo
2. Add to commandcenter/src/
3. Update imports
4. Add tests
5. Verify functionality
6. Document
```

### Strategy 2: REFACTOR (Clean up)
```python
# When: Good logic, messy code
# Process:
1. Copy file to commandcenter/src/
2. Run linter/formatter
3. Improve variable names
4. Add type hints
5. Add docstrings
6. Update to modern patterns
7. Add tests
8. Verify functionality
```

### Strategy 3: REWRITE (Fresh implementation)
```python
# When: Good idea, bad implementation
# Process:
1. Document what old version does
2. Design new implementation
3. Write from scratch in commandcenter
4. Use old code as reference only
5. Implement better patterns
6. Add tests
7. Compare results with old version
```

### Strategy 4: SKIP (Leave behind)
```python
# When: Buggy, unused, or outdated
# Process:
1. Document why skipping
2. Note if needed later
3. Move on
```

---

## Tools for Discovery

### Audit Spreadsheet Template
```
Component | File Path | Purpose | Status | Decision | Priority | Notes
----------|-----------|---------|--------|----------|----------|-------
Agent 1   | path.py   | Does X  | Works  | KEEP     | High     | Core feature
Tool 2    | path.py   | Does Y  | Buggy  | REWRITE  | Med      | Good idea, bad code
```

### Decision Log Template
```markdown
# Decision: [What you decided]
**Date:** YYYY-MM-DD
**Context:** What situation led to this decision
**Options Considered:**
1. Option A - Pros/Cons
2. Option B - Pros/Cons
**Decision:** Chose [option] because [reason]
**Consequences:** What this means going forward
```

---

## Key Principles

### DO:
✅ Start completely fresh
✅ Audit everything before porting
✅ Document decisions
✅ Test each ported component
✅ Ask "do I really need this?"
✅ Simplify when possible

### DON'T:
❌ Copy entire old repo
❌ Port bugs from old system
❌ Rush the audit process
❌ Skip documentation
❌ Port components you don't understand
❌ Bring over unused code

---

## Success Criteria for Discovery Phase

**Phase complete when:**
- [ ] Every old component audited and rated
- [ ] Requirements clearly documented
- [ ] Port plan created with priorities
- [ ] New architecture designed
- [ ] Team (you) understands what's being built
- [ ] Have confidence in the plan

**Outputs:**
- `docs/01-old-stack-audit.md` ✅
- `docs/02-requirements.md` ✅
- `docs/03-port-plan.md` ✅
- `docs/04-architecture.md` ✅
- Architecture diagram ✅

---

## Next Steps After Discovery

Once discovery is complete:

1. **Review with Claude** - discuss findings
2. **Adjust plan** if needed
3. **Get approval** (from yourself 😊)
4. **Move to Phase 2: Planning** - detailed implementation plan
5. **Start building!**

---

## Time Estimate

**Total Discovery Time:** 8-15 hours
- Old stack audit: 2-3 hours
- Requirements: 1-2 hours  
- Port planning: 1-2 hours
- Architecture design: 2-3 hours
- Reviews and iteration: 2-5 hours

**Calendar Time:** 3-5 days (at 2-3 hours per day)

---

## Questions to Ask Yourself During Discovery

1. **Purpose:** Why did I build this originally?
2. **Usage:** Do I actually use this regularly?
3. **Value:** What problems does this solve?
4. **Quality:** Is this code I'm proud of?
5. **Maintainability:** Can I maintain this going forward?
6. **Alternatives:** Could I do this better now?
7. **Necessity:** Do I really need this?

**If answer is "no" or "uncertain" to most → SKIP or REWRITE**

---

## Red Flags (Indicators to SKIP)

🚩 Code you don't understand anymore
🚩 "Hacky" workarounds
🚩 Commented-out code everywhere
🚩 No tests or documentation
🚩 "Will fix later" TODOs
🚩 Dependencies on deprecated libraries
🚩 Copy-pasted code from Stack Overflow
🚩 Features you never use

**Don't port technical debt!**

---

## Starting Point: First Discovery Session

**Ready to begin? Start with:**

1. **Clone old repo** (read-only, separate from Codespace)
2. **Open in VSCode** (or your editor)
3. **Create** `docs/01-old-stack-audit.md` in commandcenter
4. **Go through old code** file by file
5. **Document findings** using template above
6. **We review together** and make decisions

**I can help via Claude Code to:**
- List all files in old repo
- Analyze code structure
- Suggest ratings (you decide final)
- Create audit documents
- Ask probing questions

---

**Ready to start the audit?** 🔍