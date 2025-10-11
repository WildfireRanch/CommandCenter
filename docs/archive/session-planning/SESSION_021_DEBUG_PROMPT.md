# Session 021: Deep Debugging - Agent/Tool/Frontend Integration

**CRITICAL: System audit reveals major bugs and integration issues**

---

## 🚨 PROBLEM SUMMARY

After Session 020, we have **lots of code but very little functionality**, especially on the frontend. Multiple critical bugs exist in the agent-tool-manager integration chain.

**Status:**
- ✅ Backend API: Running, endpoints exist
- ⚠️ Agent Routing: **BROKEN** - manager.py has critical bugs
- ⚠️ Tools: **INCONSISTENT** - some use .func(), some don't
- ❌ Frontend: **NOT CONNECTED** - chat calls wrong endpoints
- ❌ Integration: **COMPLETELY BROKEN** - end-to-end flow fails

---

## 🔍 CRITICAL BUGS FOUND

### 1. **AGENT FILE NAMING CONFLICT** 🚨

**Problem:** We have TWO different "energy controller" agents!

**Files:**
- `railway/src/agents/solar_controller.py` - Filename says "energy_controller.py" in header comments
- `railway/src/agents/energy_orchestrator.py` - New agent from Session 020

**Impact:**
- Import confusion in manager.py
- Function `create_energy_crew()` exists in `solar_controller.py` but comments say "energy_controller"
- Manager imports from `solar_controller` but file headers are inconsistent

**Evidence:**
```python
# In solar_controller.py line 2:
# FILE: railway/src/agents/energy_controller.py  ❌ WRONG FILENAME

# In manager.py line 22:
from .solar_controller import create_energy_crew  # ✅ Correct import
```

**Fix Required:**
- Decide: is it `solar_controller.py` or `energy_controller.py`?
- Update ALL file headers to match actual filename
- Ensure all imports are consistent

---

### 2. **TOOL WRAPPER INCONSISTENCY** 🚨

**Problem:** Tools use `@tool` decorator but some code calls them with `.func()` and some don't

**Evidence:**

In `manager.py` line 125:
```python
return search_knowledge_base.func(query, limit=5)  # Uses .func()
```

In `solar_controller.py` line 57:
```python
return search_knowledge_base(query, limit=5)  # NO .func() - will FAIL!
```

In `energy_orchestrator.py`:
```python
# Uses search_knowledge_base in tools array
tools=[..., search_knowledge_base]  # Passed as tool object
```

**Impact:**
- `solar_controller.py` calls `search_knowledge_base()` directly → TypeError
- Should call `search_knowledge_base.func()` or import unwrapped function
- Inconsistent pattern across codebase

**Fix Required:**
- EITHER: All tools exposed as unwrapped functions + wrapped versions
- OR: All internal calls use `.func()`
- Document the pattern clearly

---

### 3. **FRONTEND API ENDPOINT MISMATCH** 🚨

**Problem:** Frontend calls `/agent/ask` but API defines `/ask`

**Evidence:**

Frontend (`dashboards/components/api_client.py` line 57):
```python
return self._post("/agent/ask", payload)  # ❌ Wrong endpoint
```

Backend (`railway/src/api/main.py` line 776):
```python
@app.post("/ask", response_model=AskResponse)  # ✅ Actual endpoint
```

**Impact:**
- Frontend chat is completely broken
- All user queries return 404
- Zero functionality in the UI

**Fix Required:**
- Change frontend to call `/ask` OR
- Add route alias at `/agent/ask` → `/ask`
- Test end-to-end chat flow

---

### 4. **MANAGER AGENT CREATES AGENT TWICE** 🚨

**Problem:** `create_manager_crew()` creates the agent twice unnecessarily

**Evidence (`manager.py`):**
```python
def create_manager_crew(query: str, context: str = "") -> Crew:
    agent = create_manager_agent()  # Creates agent #1
    task = create_routing_task(query, context)  # Creates agent #2 inside!

    return Crew(
        agents=[agent],  # Only uses agent #1
        tasks=[task],
    )

def create_routing_task(query: str, context: str = "") -> Task:
    return Task(
        ...
        agent=create_manager_agent(),  # ❌ Creates ANOTHER agent!
    )
```

**Impact:**
- Wasteful - creates 2 identical agents
- Potential state inconsistency
- Poor performance

**Fix Required:**
- Pass agent parameter to `create_routing_task()`
- Don't create agent inside task definition

---

### 5. **SOLAR CONTROLLER ALSO HAS DUPLICATE AGENTS** 🚨

**Same bug in `solar_controller.py`:**

```python
def create_energy_crew(query: str, conversation_context: str = "") -> Crew:
    agent = create_energy_monitor_agent()  # Agent #1
    task = create_status_task(query, conversation_context)  # Agent #2!

    return Crew(
        agents=[agent],
        tasks=[task],
        verbose=True,
    )
```

**Fix Required:**
- Fix this pattern in ALL agents:
  - manager.py
  - solar_controller.py
  - energy_orchestrator.py

---

### 6. **KB SEARCH TOOL HAS TWO NAMES** 🚨

**Problem:** Knowledge base search tool defined twice with different names

**Evidence:**

In `manager.py`:
```python
@tool("Search Knowledge Base")
def search_kb_directly(query: str) -> str:
    return search_knowledge_base.func(query, limit=5)
```

In `solar_controller.py`:
```python
@tool("Search Knowledge Base")
def search_kb_tool(query: str) -> str:
    return search_knowledge_base(query, limit=5)  # Also calls wrong!
```

**Impact:**
- Two different wrappers for same functionality
- One uses `.func()`, one doesn't
- Confusing codebase
- Name collision in tool registry

**Fix Required:**
- Create ONE canonical KB search tool
- Import and reuse it everywhere
- Or use the base `search_knowledge_base` tool directly

---

### 7. **NO ERROR HANDLING IN ROUTING TOOLS** 🚨

**Problem:** Manager routing tools catch exceptions but child agents might not

**Evidence:**

Manager wraps errors:
```python
@tool("Route to Solar Controller")
def route_to_solar_controller(query: str) -> str:
    try:
        crew = create_energy_crew(query)
        result = crew.kickoff()
        return str(result)
    except Exception as e:
        return f"Error routing to Solar Controller: {str(e)}"
```

But if the child agent throws during execution, it bubbles up as an exception, not a string error response.

**Impact:**
- Inconsistent error handling
- Some errors crash the request
- Poor user experience

**Fix Required:**
- Ensure all errors convert to user-friendly messages
- Add error logging before returning error strings
- Test failure modes

---

### 8. **CONVERSATION CONTEXT MIGHT BE BROKEN** 🚨

**Problem:** Conversation context passed to crews but might cause recursive hell

**Evidence in `main.py`:**
```python
# Get conversation context (previous conversations, excluding current)
context = get_conversation_context(
    agent_role=agent_role,
    current_conversation_id=conversation_id,
    max_conversations=3,
    max_messages_per_conversation=6
)

# Create manager crew to route query intelligently
crew = create_manager_crew(request.message, context)
```

Manager then passes context to child agents:
```python
def route_to_solar_controller(query: str) -> str:
    crew = create_energy_crew(query)  # ❌ No context passed!
```

**Impact:**
- Context lost when routing to child agents
- Multi-turn conversations might break
- Context never reaches specialist agents

**Fix Required:**
- Decide: should child agents get context?
- If yes: modify routing functions to pass context
- If no: document why not

---

### 9. **AGENT ROLES HARDCODED AND INCONSISTENT** 🚨

**Problem:** Agent role is hardcoded as "Energy Systems Monitor" but we have 3 agents

**Evidence in `main.py`:**
```python
agent_role = "Energy Systems Monitor"  # ❌ Always this role

# But we have:
# 1. Manager (Query Router and Coordinator)
# 2. Solar Controller (Energy Systems Monitor)
# 3. Energy Orchestrator (Energy Operations Manager)
```

**Impact:**
- Conversation logs show wrong agent
- Can't filter by actual agent used
- Analytics broken

**Fix Required:**
- Detect which agent actually answered
- Log correct agent role
- Update conversation metadata

---

### 10. **FRONTEND CALLS NON-EXISTENT ENDPOINTS** 🚨

**Problem:** Frontend expects more endpoints than backend provides

**Frontend expects (`api_client.py`):**
```python
def get_conversation(self, session_id: str):
    return self._get(f"/conversations/{session_id}")

def get_recent_conversations(self, limit: int = 10):
    return self._get(f"/conversations/recent?limit={limit}")
```

**Backend provides:**
```python
@app.get("/conversations")  # ✅ Exists but different URL!
async def list_conversations(limit: int = 10):

@app.get("/conversations/{conversation_id}")  # ✅ Exists
async def get_conversation_detail(conversation_id: str):
```

**Impact:**
- "Recent conversations" endpoint mismatch
- Frontend calls `/conversations/recent` → 404
- Backend has `/conversations?limit=10`

**Fix Required:**
- Align frontend and backend URLs
- Add `/conversations/recent` alias OR
- Fix frontend to call `/conversations`

---

## 🎯 DEBUGGING TASK LIST

### Phase 1: Fix Core Agent/Tool Issues (2 hours)

**Task 1.1: Standardize Tool Calling Pattern**
```python
# Choose ONE pattern and apply everywhere:

# OPTION A: All tools import as .func()
from ..tools.kb_search import search_knowledge_base
result = search_knowledge_base.func(query, limit=5)

# OPTION B: Tools expose unwrapped functions
from ..tools.kb_search import search_knowledge_base_impl
result = search_knowledge_base_impl(query, limit=5)

# Document chosen pattern in:
# - docs/CommandCenter Code Style Guide.md
# - Add section on "Tool Calling Conventions"
```

**Task 1.2: Fix Agent File Naming**
```bash
# Rename file OR fix all comments
# EITHER:
mv railway/src/agents/solar_controller.py railway/src/agents/energy_controller.py

# OR: Update all file headers to say solar_controller.py

# Then update ALL imports across codebase
```

**Task 1.3: Eliminate Duplicate Agent Creation**
```python
# Fix pattern in all 3 agents:

def create_routing_task(query: str, context: str = "", agent: Agent = None) -> Task:
    if agent is None:
        agent = create_manager_agent()

    return Task(
        description=...,
        agent=agent,  # Use passed agent
    )

def create_manager_crew(query: str, context: str = "") -> Crew:
    agent = create_manager_agent()
    task = create_routing_task(query, context, agent=agent)  # Pass it!

    return Crew(agents=[agent], tasks=[task])
```

**Task 1.4: Consolidate KB Search Tools**
```python
# In kb_search.py - expose BOTH forms:

@tool("Search Knowledge Base")
def search_knowledge_base(query: str, limit: int = 5) -> str:
    """..."""
    # Implementation

# For direct calling:
def search_kb(query: str, limit: int = 5) -> str:
    """Direct callable version without CrewAI wrapper"""
    return search_knowledge_base.func(query, limit)

# Then everywhere else:
from ..tools.kb_search import search_knowledge_base  # For tool arrays
from ..tools.kb_search import search_kb  # For direct calling
```

---

### Phase 2: Fix Frontend Integration (1.5 hours)

**Task 2.1: Fix API Endpoint URLs**
```python
# In dashboards/components/api_client.py:

def ask_agent(self, message: str, session_id: Optional[str] = None):
    payload = {"message": message}
    if session_id:
        payload["session_id"] = session_id
    return self._post("/ask", payload)  # ✅ FIXED: was /agent/ask

def get_recent_conversations(self, limit: int = 10):
    return self._get(f"/conversations?limit={limit}")  # ✅ FIXED: was /conversations/recent
```

**Task 2.2: Test End-to-End Chat Flow**
```bash
# 1. Start backend
cd railway
uvicorn src.api.main:app --reload

# 2. Start frontend
cd dashboards
streamlit run Home.py

# 3. Go to Agent Chat page
# 4. Send test messages:
#    - "What's my battery level?"  (should route to Solar Controller)
#    - "Should we run miners?"     (should route to Energy Orchestrator)
#    - "What is the min SOC?"      (should search KB)

# 5. Check logs for errors
# 6. Verify responses appear in UI
```

**Task 2.3: Add Error Display in Frontend**
```python
# In dashboards/pages/3_🤖_Agent_Chat.py:

# After line 134, add better error handling:
elif "error" in response:
    error_msg = response.get("error", "Unknown error")
    detail = response.get("detail", "")

    st.error(f"❌ Error: {error_msg}")
    if detail:
        with st.expander("Error Details"):
            st.code(detail)
```

---

### Phase 3: Fix Agent Routing Logic (2 hours)

**Task 3.1: Track Actual Agent Used**
```python
# In manager.py routing tools:

@tool("Route to Solar Controller")
def route_to_solar_controller(query: str) -> str:
    try:
        crew = create_energy_crew(query)
        result = crew.kickoff()

        # Return structured response with metadata
        return json.dumps({
            "response": str(result),
            "agent_used": "Solar Controller",
            "agent_role": "Energy Systems Monitor"
        })
    except Exception as e:
        return json.dumps({
            "response": f"Error: {str(e)}",
            "agent_used": "Solar Controller",
            "error": True
        })

# Update all 3 routing functions
```

**Task 3.2: Extract Agent Info in /ask Endpoint**
```python
# In main.py /ask endpoint:

# After crew.kickoff(), parse result
result_str = str(result)

# Try to parse as JSON (from routing tools)
agent_used = "Manager"  # Default
try:
    result_data = json.loads(result_str)
    if "agent_used" in result_data:
        agent_used = result_data["agent_used"]
        agent_role = result_data.get("agent_role", agent_role)
        result_str = result_data["response"]
except:
    pass  # Not JSON, use result as-is

# Update response metadata
return AskResponse(
    response=result_str,
    query=request.message,
    agent_role=agent_used,  # ✅ Actual agent that answered
    duration_ms=duration_ms,
    session_id=conversation_id,
)
```

**Task 3.3: Pass Context to Child Agents**
```python
# Decide if we want this. If yes:

@tool("Route to Solar Controller")
def route_to_solar_controller(query: str, context: str = "") -> str:
    try:
        crew = create_energy_crew(query, context)  # Pass context!
        result = crew.kickoff()
        return str(result)
    except Exception as e:
        return f"Error: {str(e)}"

# But how do tools get context? Manager calls routing tool with query only.
# May need to redesign how context flows through routing layer.
```

---

### Phase 4: Testing & Validation (1.5 hours)

**Task 4.1: Create Agent Test Suite**
```bash
# Create: railway/tests/test_agents/test_manager_routing.py

import pytest
from src.agents.manager import create_manager_crew

def test_status_query_routes_to_solar_controller():
    query = "What's my battery level?"
    crew = create_manager_crew(query)
    result = crew.kickoff()

    # Should contain battery status
    assert "battery" in str(result).lower() or "%" in str(result)

def test_planning_query_routes_to_orchestrator():
    query = "Should we run the miners tonight?"
    crew = create_manager_crew(query)
    result = crew.kickoff()

    # Should contain recommendation
    assert any(word in str(result).lower() for word in ["start", "stop", "maintain", "recommend"])

def test_kb_query_searches_knowledge_base():
    query = "What is the minimum battery SOC threshold?"
    crew = create_manager_crew(query)
    result = crew.kickoff()

    # Should contain KB citation
    assert "source" in str(result).lower() or "soc" in str(result).lower()
```

**Task 4.2: Create Integration Test**
```bash
# Create: railway/tests/test_integration/test_end_to_end.py

import requests
import pytest

BASE_URL = "http://localhost:8000"

def test_ask_endpoint_returns_valid_response():
    response = requests.post(
        f"{BASE_URL}/ask",
        json={"message": "What's my battery level?"}
    )

    assert response.status_code == 200
    data = response.json()

    assert "response" in data
    assert "agent_role" in data
    assert "session_id" in data
    assert len(data["response"]) > 0

def test_conversation_persistence():
    # First message
    resp1 = requests.post(
        f"{BASE_URL}/ask",
        json={"message": "What's my battery level?"}
    )
    session_id = resp1.json()["session_id"]

    # Second message in same conversation
    resp2 = requests.post(
        f"{BASE_URL}/ask",
        json={
            "message": "Is that good?",
            "session_id": session_id
        }
    )

    assert resp2.status_code == 200
    assert resp2.json()["session_id"] == session_id

    # Get conversation history
    resp3 = requests.get(f"{BASE_URL}/conversations/{session_id}")
    assert resp3.status_code == 200

    messages = resp3.json()["messages"]
    assert len(messages) >= 4  # 2 user + 2 assistant
```

**Task 4.3: Manual Frontend Testing Checklist**
```markdown
# Frontend Testing Checklist

## Agent Chat Page
- [ ] Page loads without errors
- [ ] Can send message: "What's my battery level?"
- [ ] Response appears within 10 seconds
- [ ] Response contains battery percentage
- [ ] Session ID shown in UI
- [ ] Clear Chat button works
- [ ] Can continue conversation with "Is that good?"
- [ ] Agent maintains context from previous message

## Error Handling
- [ ] Backend offline → Shows clear error message
- [ ] Invalid query → Returns graceful error
- [ ] Long query (>500 chars) → Handles properly
- [ ] Special characters in query → No crashes

## Multi-Agent Routing
- [ ] Status query ("battery level") → Goes to Solar Controller
- [ ] Planning query ("should we run miners") → Goes to Energy Orchestrator
- [ ] KB query ("what is min SOC") → Searches knowledge base
- [ ] Agent role displayed correctly in response
```

---

## 📝 DOCUMENTATION UPDATES REQUIRED

### Update: `docs/INDEX.md`
```markdown
## Agent System Architecture

### Agents
1. **Manager Agent** (`railway/src/agents/manager.py`)
   - Routes queries to specialists
   - Analyzes intent
   - Coordinates multi-agent queries

2. **Solar Controller** (`railway/src/agents/solar_controller.py`)
   - Real-time status monitoring
   - Battery, solar, load, grid data
   - Tool: Get SolArk Status

3. **Energy Orchestrator** (`railway/src/agents/energy_orchestrator.py`)
   - Planning and optimization
   - Battery optimizer, miner coordinator, energy planner
   - Tools: Battery Optimizer, Miner Coordinator, Energy Planner

### Tools
- `search_knowledge_base` - Semantic search in KB
- `get_solark_status` - Real-time inverter data
- `optimize_battery` - Charge/discharge recommendations
- `coordinate_miners` - Miner on/off decisions
- `create_energy_plan` - 24-hour energy planning

### API Endpoints
- `POST /ask` - Send query to agent system
- `GET /conversations` - List recent conversations
- `GET /conversations/{id}` - Get conversation details
- `GET /health` - System health check
```

### Update: `docs/CommandCenter Code Style Guide.md`
Add new section:

```markdown
## Tool Calling Conventions

### CrewAI Tool Pattern

All tools are decorated with `@tool()` and can be used two ways:

1. **As CrewAI Tools** (in agent.tools array):
```python
from ..tools.kb_search import search_knowledge_base

agent = Agent(
    tools=[search_knowledge_base],  # Pass tool object
)
```

2. **Direct Function Calls** (in other tools or utilities):
```python
from ..tools.kb_search import search_knowledge_base

# Call with .func() method
result = search_knowledge_base.func(query, limit=5)
```

### Never Do This:
```python
# ❌ WRONG - will raise TypeError
result = search_knowledge_base(query, limit=5)
```

### Creating New Tools

1. Decorate with `@tool("Tool Name")`
2. Add comprehensive docstring
3. Type hint all parameters
4. Handle errors gracefully
5. Add CLI test interface at bottom

Example template:
```python
from crewai.tools import tool
import logging

logger = logging.getLogger(__name__)

@tool("My New Tool")
def my_new_tool(param: str, optional: int = 10) -> str:
    \"\"\"
    One-line description.

    Detailed explanation of what this tool does and when to use it.

    Args:
        param: Description of required parameter
        optional: Description of optional parameter (default: 10)

    Returns:
        str: Description of return value

    Examples:
        >>> my_new_tool("test")
        "Result for test"
    \"\"\"
    try:
        # Implementation
        result = do_something(param, optional)
        return result
    except Exception as e:
        logger.error(f"My tool error: {e}")
        return f"Error in my_new_tool: {str(e)}"


# CLI Testing
if __name__ == "__main__":
    import sys
    test_input = sys.argv[1] if len(sys.argv) > 1 else "default"
    print(my_new_tool.func(test_input))
```
```

### Update: `docs/sessions/SESSION_020_SUMMARY.md`
Create summary of Session 020:

```markdown
# Session 020 Summary

## What Was Built
✅ Battery Optimizer tool
✅ Miner Coordinator tool
✅ Energy Planner tool
✅ Energy Orchestrator agent
✅ Manager routing updated

## What Was NOT Tested
❌ End-to-end frontend integration
❌ Manager routing logic
❌ Tool calling patterns
❌ Error handling

## Bugs Introduced
1. Inconsistent tool calling (.func() vs direct)
2. Duplicate agent creation in crews
3. KB search tool defined twice with different names
4. Frontend API endpoint mismatch
5. Agent role tracking broken
6. Context not passed to child agents

## Next Session Priority
Session 021 must focus on:
1. Fix all bugs listed above
2. Test end-to-end chat flow
3. Verify all 3 agents work
4. Update documentation
5. Create integration tests
```

---

## 🎯 SUCCESS CRITERIA

Session 021 is complete when:

- [ ] All 10 critical bugs FIXED
- [ ] Frontend chat works end-to-end
- [ ] Status queries route to Solar Controller and return results
- [ ] Planning queries route to Energy Orchestrator and return results
- [ ] KB queries search knowledge base and return citations
- [ ] Error messages clear and helpful
- [ ] Integration tests passing
- [ ] Documentation updated
- [ ] No TypeErrors from tool calling
- [ ] No 404s from frontend
- [ ] Agent roles correctly logged in database

---

## 📊 TIME ESTIMATE

- Phase 1 (Core Fixes): 2 hours
- Phase 2 (Frontend): 1.5 hours
- Phase 3 (Routing): 2 hours
- Phase 4 (Testing): 1.5 hours

**Total: 7 hours**

---

## 🚀 START HERE

```bash
# 1. Review this entire document
# 2. Start with Phase 1, Task 1.1 (standardize tool calling)
# 3. Work through tasks sequentially
# 4. Test after each phase
# 5. Update documentation as you go

# Current status: V1.5 at 95% → But 0% actually works!
# After Session 021: V1.5 at 100% → And it ACTUALLY WORKS!
```

**Let's debug this system and make it work!** 🔧
