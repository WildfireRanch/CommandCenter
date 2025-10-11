# Phase 1.3: Selective Port Plan

**Date:** October 3, 2025  
**Project:** CommandCenter V1  
**Phase:** Discovery - Selective Porting Strategy  
**Previous Phase:** Requirements Definition Complete ✅

---

## Executive Summary

This document maps Relay repository components to CommandCenter V1 requirements and provides exact migration instructions for each portable component.

**Strategy:** Extract working tools and concepts, discard broken orchestration, rebuild in CrewAI.

**Components to Port:** ~15-20% of Relay code (mostly tools and integrations)  
**Components to Reference:** ~30% (concepts, UI, tests)  
**Components to Skip:** ~50-55% (custom orchestration, broken systems)

---

## Port Priority Matrix

### 🔴 HIGH PRIORITY - Port First (Week 1)

These are critical, working components that provide immediate value.

#### 1. Hardware Control Tools ✅ KEEP

**From Relay:**
- `backend/solark_control.py` - SolArk browser automation
- `tools/shelly_control.py` - Shelly device API
- `tools/miner_control.py` - Bitcoin miner SSH control
- `services/victron_client.py` - Victron API integration
- `tools/nodered_trigger.py` - Node-RED webhooks
- `services/postgres_client.py` - Database queries

**To CommandCenter:**
- `src/tools/solark.py` - Wrapped as CrewAI tool
- `src/tools/shelly.py` - Wrapped as CrewAI tool
- `src/tools/miners.py` - Wrapped as CrewAI tool
- `src/tools/victron.py` - Wrapped as CrewAI tool
- `src/tools/nodered.py` - Wrapped as CrewAI tool
- `src/tools/database.py` - Wrapped as CrewAI tool

**Strategy:** KEEP - Copy and wrap as CrewAI tools

**Migration Steps:**
1. Copy files from Relay to CommandCenter
2. Add CrewAI `@tool` decorator
3. Add type hints and docstrings
4. Add safety checks (dry-run, validation)
5. Write unit tests
6. Test in isolation before integration

**Estimated Time:** 4-6 hours

**Dependencies:**
- Selenium (for SolArk)
- requests (for Shelly, Victron)
- paramiko (for miners via SSH)
- psycopg2 (for PostgreSQL)

**Example Port:**
```python
# FROM: relay/backend/solark_control.py
def set_solark_mode(mode):
    # ... selenium automation code ...
    pass

# TO: commandcenter/src/tools/solark.py
from crewai_tools import tool
from typing import Literal

@tool("Set SolArk inverter mode")
def set_solark_mode(
    mode: Literal["grid", "battery", "generator"],
    dry_run: bool = False,
    confirm: bool = True
) -> dict:
    """
    Set the operating mode of the SolArk 8K inverter.
    
    Args:
        mode: Operating mode (grid/battery/generator)
        dry_run: If True, simulate without executing
        confirm: If True, require user confirmation
    
    Returns:
        dict: {success: bool, message: str, previous_mode: str}
    """
    if dry_run:
        return {"success": True, "message": f"DRY RUN: Would set mode to {mode}"}
    
    # ... original selenium code with safety checks ...
    pass
```

---

#### 2. PostgreSQL Schema & Data ✅ KEEP

**From Relay:**
- `database/schema.sql` - Table definitions
- Existing data in PostgreSQL (telemetry, logs)

**To CommandCenter:**
- `src/database/schema.sql` - Migrate schema
- Preserve existing data (no data loss)

**Strategy:** KEEP - Migrate schema, preserve data

**Migration Steps:**
1. Export Relay schema: `pg_dump --schema-only relay_db > relay_schema.sql`
2. Review tables - identify which are needed
3. Create CommandCenter schema (add new tables, keep relevant old ones)
4. Add migration script for schema updates
5. Test with copy of production data

**Tables to Keep:**
- `system_status` - Historical telemetry
- `action_log` - Command history
- `preferences` - User settings

**Tables to Add (New for CommandCenter):**
- `agent_sessions` - Session memory
- `kb_documents` - Knowledge base index
- `kb_embeddings` - Document embeddings

**Estimated Time:** 2-3 hours

---

#### 3. Google Docs Integration ✅ REFACTOR

**From Relay:**
- `services/google_docs_sync.py` - Two-way sync (broken)
- `services/google_auth.py` - OAuth handling

**To CommandCenter:**
- `src/integrations/google_docs.py` - ONE-WAY sync only (V1)
- `src/integrations/google_auth.py` - OAuth (simplified)

**Strategy:** REFACTOR - Extract working OAuth, simplify to read-only

**Migration Steps:**
1. Copy OAuth code (this works)
2. Strip out two-way sync (broken/complex)
3. Keep read + index functionality
4. Add scheduled sync (cron job on Railway)
5. Test with real Google Docs folder

**What to Keep:**
- ✅ OAuth flow
- ✅ Document reading
- ✅ Folder traversal

**What to Discard:**
- ❌ Two-way sync
- ❌ Conflict resolution
- ❌ Real-time watching

**Estimated Time:** 3-4 hours

---

### 🟡 MEDIUM PRIORITY - Port Second (Week 2)

#### 4. Integration Services ⚠️ EXTRACT CONCEPTS

**From Relay:**
- `services/gmail_client.py` - Gmail API
- `services/github_client.py` - GitHub API

**To CommandCenter:**
- `src/integrations/gmail.py` - Simplified (if needed)
- `src/integrations/github.py` - Simplified (if needed)

**Strategy:** EXTRACT - Decide if needed for V1, simplify if so

**Decision Point:**
- Are Gmail/GitHub needed for V1?
- If YES: Extract minimal functionality (read-only)
- If NO: Defer to V2

**Estimated Time:** 2-3 hours (if needed)

**Recommendation:** Defer to V2 - focus on core energy orchestration

---

#### 5. Frontend UI Components 📋 REFERENCE

**From Relay:**
- `frontend/` - Next.js application
- React components
- Shadcn UI components

**To CommandCenter:**
- `src/frontend/` - Reference architecture
- Adapt API contracts for CrewAI backend

**Strategy:** REFERENCE - Learn from, adapt for new backend

**Migration Steps:**
1. Review frontend structure
2. Identify reusable components (auth, layout, forms)
3. Update API endpoints to match CrewAI backend
4. Simplify (remove features tied to broken backend)

**What to Keep:**
- ✅ Authentication flow
- ✅ Layout/navigation
- ✅ Component library choices

**What to Rebuild:**
- Agent interaction UI (different backend)
- Dashboard (simpler V1 version)
- Settings/preferences

**Estimated Time:** 6-8 hours (if building UI in V1)

**Recommendation:** CLI first, web UI in V2

---

### 🟢 LOW PRIORITY - Port Later/Maybe

#### 6. Agent Role Definitions 📋 EXTRACT CONCEPTS

**From Relay:**
- `agents/planner_agent.py` - Role definition
- `agents/memory_agent.py` - Role definition
- Agent prompts and instructions

**To CommandCenter:**
- `src/agents/energy_orchestrator.py` - CrewAI agent
- Agent role/goal/backstory extracted from Relay

**Strategy:** EXTRACT CONCEPTS - Use role ideas, not code

**Migration Steps:**
1. Read each Relay agent file
2. Document: What role, what responsibilities, what tools
3. Map to CommandCenter agents
4. Rewrite as CrewAI agent definitions (fresh code)

**Example:**
```python
# FROM RELAY (relay/agents/planner_agent.py)
class PlannerAgent:
    def __init__(self):
        self.role = "Task planner who breaks down complex requests"
        # ... custom orchestration code ...

# TO COMMANDCENTER (src/agents/energy_orchestrator.py)
from crewai import Agent

energy_orchestrator = Agent(
    role="Energy System Optimization Specialist",
    goal="Optimize off-grid energy usage to maximize battery health and minimize costs",
    backstory="""You are an expert in off-grid energy systems with deep knowledge 
    of battery management, solar production, and load balancing. You analyze system 
    state and make intelligent decisions about when to charge, discharge, run loads, 
    and preserve battery capacity.""",
    tools=[query_system_status, control_miners, set_inverter_mode],
    verbose=True
)
```

**Estimated Time:** 2-3 hours

---

#### 7. Critic System Concepts 📋 EXTRACT CONCEPTS

**From Relay:**
- `agents/critic_agent/` - 16 specialized critics
- Evaluation criteria and feedback loops

**To CommandCenter:**
- Not porting code, but extracting evaluation ideas

**Strategy:** EXTRACT - Learn from, don't implement in V1

**What to Learn:**
- Quality criteria for agent outputs
- Common failure modes to check
- Validation patterns

**Use For:**
- V2 feature: Agent self-evaluation
- V1 use: Manual evaluation checklist

**Estimated Time:** 1 hour (reading/documenting)

---

### ❌ DO NOT PORT - Skip Entirely

#### 8. Custom Orchestration ❌ SKIP

**From Relay:**
- `core/orchestrator.py` - Custom message passing
- `core/agent_messenger.py` - Agent communication
- Agent coordination code

**Why Skip:**
- **Root cause of unreliability in Relay**
- CrewAI replaces this entirely
- Custom implementation is fragile

**CrewAI Replacement:**
- Crew coordination
- Task delegation
- Agent communication
- Context passing

**Action:** Delete, don't look back

---

#### 9. Custom Memory System ❌ SKIP

**From Relay:**
- `services/memory.py` - Three-tier memory
- Event/entity tracking
- Custom memory retrieval

**Why Skip:**
- User doesn't know if it works
- Over-engineered for needs
- CrewAI has built-in memory

**CrewAI Replacement:**
- Short-term memory (session)
- Long-term memory (across sessions)
- Entity memory (tracking)

**Action:** Use CrewAI memory, start simple

---

#### 10. Mystery Code ❌ SKIP

**From Relay:**
- Any code you don't understand
- Commented-out experiments
- Unused utilities

**Why Skip:**
- Can't maintain what you don't understand
- Likely buggy or outdated

**Action:** If you can't explain what it does, don't port it

---

## Migration Checklist

### Pre-Migration Setup
- [ ] Clone Relay repo (read-only, separate workspace)
- [ ] Create CommandCenter directory structure
- [ ] Set up Python virtual environment
- [ ] Install CrewAI and dependencies
- [ ] Initialize Git repo (commandcenter)

### Hardware Tools (Week 1, Day 1-2)
- [ ] Port SolArk control (`backend/solark_control.py` → `src/tools/solark.py`)
- [ ] Port Shelly control (`tools/shelly_control.py` → `src/tools/shelly.py`)
- [ ] Port miner control (`tools/miner_control.py` → `src/tools/miners.py`)
- [ ] Port Victron client (`services/victron_client.py` → `src/tools/victron.py`)
- [ ] Port Node-RED trigger (`tools/nodered_trigger.py` → `src/tools/nodered.py`)
- [ ] Port PostgreSQL client (`services/postgres_client.py` → `src/tools/database.py`)
- [ ] Add CrewAI `@tool` decorators to all
- [ ] Add safety checks (dry-run, validation)
- [ ] Write unit tests for each tool
- [ ] Test tools in isolation (not in crew yet)

### Database (Week 1, Day 3)
- [ ] Export Relay schema
- [ ] Design CommandCenter schema (preserve + add)
- [ ] Create migration script
- [ ] Test migration with copy of prod data
- [ ] Document schema changes

### Knowledge Base (Week 1, Day 4-5)
- [ ] Port Google OAuth (`services/google_auth.py` → `src/integrations/google_auth.py`)
- [ ] Extract read-only sync logic (`services/google_docs_sync.py` → `src/integrations/google_docs.py`)
- [ ] Remove two-way sync code
- [ ] Add embedding generation
- [ ] Test sync with real Google Docs
- [ ] Schedule daily sync job

### Agent Definitions (Week 2, Day 1-2)
- [ ] Review Relay agent roles
- [ ] Document responsibilities per agent
- [ ] Map to CommandCenter agents:
  - [ ] Hardware Control Agent
  - [ ] Energy Orchestrator
  - [ ] Conversation Interface
- [ ] Write CrewAI agent definitions (fresh code)
- [ ] Define agent tools
- [ ] Test agents individually

### Integration & Testing (Week 2, Day 3-5)
- [ ] Create main crew
- [ ] Test crew workflows
- [ ] Verify tool calls work
- [ ] Test KB retrieval
- [ ] Test memory persistence
- [ ] End-to-end testing

---

## File Mapping Reference

### Tools Layer
| Relay File | CommandCenter File | Action | Time |
|-----------|-------------------|--------|------|
| `backend/solark_control.py` | `src/tools/solark.py` | KEEP + Wrap | 1h |
| `tools/shelly_control.py` | `src/tools/shelly.py` | KEEP + Wrap | 1h |
| `tools/miner_control.py` | `src/tools/miners.py` | KEEP + Wrap | 1h |
| `services/victron_client.py` | `src/tools/victron.py` | KEEP + Wrap | 1h |
| `tools/nodered_trigger.py` | `src/tools/nodered.py` | KEEP + Wrap | 30m |
| `services/postgres_client.py` | `src/tools/database.py` | KEEP + Wrap | 1h |

**Total:** ~5.5 hours

---

### Services Layer
| Relay File | CommandCenter File | Action | Time |
|-----------|-------------------|--------|------|
| `services/google_auth.py` | `src/integrations/google_auth.py` | KEEP | 30m |
| `services/google_docs_sync.py` | `src/integrations/google_docs.py` | REFACTOR | 2h |
| `services/indexer.py` | `src/kb/indexer.py` | REWRITE | 2h |
| `services/semantic_retriever.py` | `src/kb/retriever.py` | REWRITE | 2h |

**Total:** ~6.5 hours

---

### Agent Layer
| Relay File | CommandCenter File | Action | Time |
|-----------|-------------------|--------|------|
| `agents/planner_agent.py` | `src/agents/energy_orchestrator.py` | CONCEPT | 1h |
| `agents/echo_agent.py` | `src/agents/conversation.py` | CONCEPT | 1h |
| `agents/control_agent.py` | `src/agents/hardware_control.py` | CONCEPT | 1h |

**Total:** ~3 hours

---

### Skip Entirely
| Relay File | Reason to Skip |
|-----------|---------------|
| `core/orchestrator.py` | CrewAI replaces |
| `core/agent_messenger.py` | CrewAI replaces |
| `services/memory.py` | CrewAI memory better |
| `agents/memory_agent.py` | Using CrewAI memory |
| `agents/codex_agent.py` | Defer to V2 |
| `agents/metaplanner_agent.py` | Too complex for V1 |
| `agents/janitor_agent.py` | Not needed V1 |
| `agents/simulation_agent.py` | Not needed V1 |
| `agents/critic_agent/*` | Defer to V2 |

---

## Porting Best Practices

### Before Porting ANY File:
1. **Read it completely** - Understand what it does
2. **Identify dependencies** - What else does it need?
3. **Check if it works** - Does it actually function in Relay?
4. **Ask: Do I need this?** - Is it required for V1?
5. **Decide strategy** - KEEP / REFACTOR / REWRITE / SKIP

### While Porting:
1. **One file at a time** - Don't port everything at once
2. **Test immediately** - Verify it works before moving on
3. **Add safety** - Dry-run, validation, error handling
4. **Document changes** - Note what you modified and why
5. **Commit frequently** - Each working file is a commit

### After Porting:
1. **Write tests** - Ensure ported code works
2. **Update docs** - Add to README, architecture docs
3. **Log decision** - Why you ported, what you changed
4. **Mark complete** - Check off in migration checklist

---

## Decision Log Template

For each ported component, document:

```markdown
## Component: [Name]

**Date:** YYYY-MM-DD

**Source:** relay/path/to/file.py

**Destination:** commandcenter/src/path/to/file.py

**Strategy:** KEEP / REFACTOR / REWRITE

**Changes Made:**
- Added type hints
- Added dry-run mode
- Removed dependency on X
- Wrapped with CrewAI @tool decorator

**Testing:**
- [x] Unit test passes
- [x] Works in isolation
- [ ] Integrated in crew (pending)

**Dependencies:**
- Library X (version)
- Service Y (running on Railway)

**Notes:**
- Original code had bug Z, fixed in port
- Simplified error handling
```

---

## Risk Mitigation

### Risk 1: Ported Code Doesn't Work
**Mitigation:** Test each component in isolation before integration

**Action:** Create `tests/tools/test_solark.py` etc.

---

### Risk 2: Missing Dependencies
**Mitigation:** Document all imports, set up requirements.txt early

**Action:** `pip freeze > requirements.txt` after each successful port

---

### Risk 3: Breaking Changes to Relay Format
**Mitigation:** Port to CommandCenter is one-way, Relay stays intact

**Action:** Never modify Relay code, only read/copy

---

### Risk 4: Over-Porting (Scope Creep)
**Mitigation:** Stick to checklist, defer anything not in V1 requirements

**Action:** When tempted to port "just one more thing," add to V2 backlog instead

---

### Risk 5: Mystery Code Breaks Things
**Mitigation:** Don't port anything you don't understand

**Action:** If you can't explain it, skip it

---

## Timeline Estimate

### Week 1: Hardware & Infrastructure
- **Day 1-2:** Port hardware tools (SolArk, Shelly, miners) - 6h
- **Day 3:** Database migration - 3h
- **Day 4-5:** Knowledge base (Google Docs sync) - 6h

**Total Week 1:** ~15 hours

---

### Week 2: Agents & Integration
- **Day 1-2:** Define CrewAI agents - 6h
- **Day 3:** Build main crew - 3h
- **Day 4-5:** Integration testing - 6h

**Total Week 2:** ~15 hours

---

**Total Porting Time:** ~30 hours (calendar: 2 weeks at 15h/week)

---

## Success Criteria

**Port is complete when:**
- [ ] All hardware tools ported and tested
- [ ] Database schema migrated
- [ ] Knowledge base syncing from Google Docs
- [ ] CrewAI agents defined
- [ ] All ported code has tests
- [ ] No Relay dependencies remain
- [ ] CommandCenter can run independently

**Port is successful when:**
- [ ] Ported tools work as well as (or better than) Relay
- [ ] No "mystery code" in CommandCenter
- [ ] User understands every line
- [ ] Foundation ready for V2 features

---

## Next Phase

After completing the port plan:

**Phase 1.4: Architecture Design**
- Design CrewAI crew structure
- Map agent communication flows
- Create data flow diagrams
- Document deployment architecture

**Then Phase 2: Planning**
- Detailed implementation plan
- Set up Railway + Vercel
- Initialize project structure

---

## Questions During Porting

**If you encounter:**
- "Should I port this?" → Check V1 requirements, if not listed → defer to V2
- "This code is broken" → SKIP, rebuild from scratch
- "I don't understand this" → SKIP, don't port mystery code
- "This seems useful but..." → If not in V1 scope → V2 backlog
- "Can I improve this while porting?" → Yes, that's REFACTOR strategy

**Golden Rule:** When in doubt, SKIP and move on. Better to under-port than over-port.

---

**Port Plan Complete. Ready for Phase 1.4: Architecture Design.**