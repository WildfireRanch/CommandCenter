# Implementation Prompt: V1.8 Smart Context Loading

## Objective

Implement smart context loading with Redis caching to reduce token usage by 40% and improve response times. This addresses the current inefficiency where all context (24KB) is loaded for every request, regardless of query relevance.

---

## Current Problem

**What's Wrong:**
- Every query loads the full 24KB context (system specs + KB docs)
- Costs ~5k-8k tokens per request even for simple queries
- No caching means repeated queries reload the same context
- KB search happens even when not needed
- Context grows unbounded as more documents are added

**Example:**
- User asks: "What's my battery level?"
- Current system loads: Full system specs + all KB docs + conversation history
- Only needs: System specs + current battery tool
- Waste: ~3k-5k tokens ($0.015-$0.025 per query)

---

## Solution Architecture

### Overview
Create a **ContextManager** service that:
1. **Intelligently selects** only relevant context based on query
2. **Caches context bundles** in Redis for 5 minutes
3. **Respects token budgets** (configurable max tokens)
4. **Falls back gracefully** if cache unavailable

### Components to Build

```
railway/src/services/
├── context_manager.py    (NEW) - Main context management logic
├── redis_client.py       (NEW) - Redis connection wrapper
└── context_classifier.py (NEW) - Query classification logic

railway/src/config/
└── context_config.py     (NEW) - Context loading rules

railway/tests/
└── test_context_manager.py (NEW) - Unit tests
```

---

## Detailed Implementation Guide

### 1. Create ContextManager Service

**File:** `railway/src/services/context_manager.py`

**Requirements:**
- Load context based on query type (system query, research query, planning query)
- Cache context bundles in Redis with 5-minute TTL
- Support configurable token budgets (default: 3000 tokens)
- Return structured ContextBundle with metadata
- Handle Redis failures gracefully (fall back to direct loading)

**Key Methods:**
```python
class ContextManager:
    def get_relevant_context(
        query: str,
        user_id: Optional[str],
        max_tokens: int = 3000
    ) -> ContextBundle

    def _classify_query(query: str) -> QueryType
    def _get_system_context() -> str
    def _get_user_preferences(user_id: str) -> str
    def _get_conversation_context(user_id: str, limit: int) -> str
    def _get_relevant_kb_docs(query: str, max_tokens: int) -> str
    def _build_cache_key(user_id: str, query_hash: str) -> str
```

**ContextBundle Structure:**
```python
@dataclass
class ContextBundle:
    system_context: str      # Hardware specs, capabilities (always included)
    user_context: str        # User preferences (if user_id provided)
    conversation_context: str # Recent chat history (last 3-5 messages)
    kb_context: str          # Relevant KB documents (smart filtered)
    total_tokens: int        # Total token count
    cache_hit: bool          # Was this from cache?
    query_type: QueryType    # system|research|planning|general
```

**Query Classification Logic:**
```python
class QueryType(Enum):
    SYSTEM = "system"        # "What's my battery level?" → needs system context only
    RESEARCH = "research"    # "What are best practices?" → needs KB + web search
    PLANNING = "planning"    # "Plan next week" → needs system + historical data
    GENERAL = "general"      # "Hello" → needs minimal context
```

**Classification Rules:**
- **SYSTEM:** Keywords like "my", "current", "now", "battery", "solar", "status"
- **RESEARCH:** Keywords like "best practices", "trends", "should I", "comparison"
- **PLANNING:** Keywords like "plan", "schedule", "forecast", "next", "optimize"
- **GENERAL:** Greetings, thank you, simple questions

### 2. Redis Integration

**File:** `railway/src/services/redis_client.py`

**Requirements:**
- Singleton pattern for connection pooling
- Connection with retry logic (3 attempts)
- Graceful degradation if Redis unavailable
- Support both Railway Redis and local development

**Configuration:**
```python
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
REDIS_TTL = 300  # 5 minutes
REDIS_MAX_RETRIES = 3
REDIS_TIMEOUT = 5  # seconds
```

**Methods Needed:**
```python
class RedisClient:
    def get(key: str) -> Optional[bytes]
    def set(key: str, value: bytes, ttl: int) -> bool
    def delete(key: str) -> bool
    def ping() -> bool  # Health check
    def close() -> None
```

### 3. Smart KB Document Selection

**Enhancement to:** `railway/src/tools/kb_search.py`

**Current Behavior:** Loads all documents matching search
**New Behavior:** Load only top-N most relevant with token budget

**New Function:**
```python
def get_relevant_kb_context(
    query: str,
    max_tokens: int = 1000,
    min_similarity: float = 0.3,
    max_docs: int = 3
) -> str:
    """
    Get KB context within token budget.

    Returns: Formatted string with document excerpts
    """
```

**Output Format:**
```
=== RELEVANT DOCUMENTATION ===

From: Victron_CerboGX_Manual.pdf (relevance: 0.87)
[300-word excerpt with context...]

From: Sol-Ark_Modbus.pdf (relevance: 0.65)
[200-word excerpt with context...]

Total: 2 documents, ~800 tokens
```

### 4. Integration with Existing Agents

**Modify:** `railway/src/agents/solar_controller.py`

**Before:**
```python
def create_energy_crew(query: str, conversation_context: str = None):
    # Loads full context for every request
    full_context = get_context_files()  # 24KB!
```

**After:**
```python
def create_energy_crew(query: str, user_id: str = None):
    # Load smart context
    context_mgr = ContextManager()
    context_bundle = context_mgr.get_relevant_context(
        query=query,
        user_id=user_id,
        max_tokens=3000
    )

    # Use only relevant context
    agent_context = context_bundle.format_for_agent()
```

**Apply to ALL agents:**
- ✅ Solar Controller
- ✅ Energy Orchestrator
- ✅ Research Agent
- ✅ Manager

### 5. Update API Endpoint

**Modify:** `railway/src/api/main.py` - `/ask` endpoint

**Add context metadata to response:**
```python
@app.post("/ask", response_model=AskResponse)
async def ask_agent(request: AskRequest):
    # ... existing code ...

    # NEW: Get smart context
    context_bundle = context_mgr.get_relevant_context(
        query=request.message,
        user_id=request.user_id,  # NEW: add user_id to AskRequest
        max_tokens=3000
    )

    # Use in crew creation
    crew = create_manager_crew(request.message, context_bundle)

    # ... rest of code ...

    # NEW: Return context metadata
    return AskResponse(
        response=result_str,
        query=request.message,
        agent_role=agent_used,
        duration_ms=duration_ms,
        session_id=conversation_id,
        context_tokens=context_bundle.total_tokens,  # NEW
        cache_hit=context_bundle.cache_hit,  # NEW
    )
```

### 6. Add Configuration

**File:** `railway/src/config/context_config.py`

```python
@dataclass
class ContextConfig:
    """Configuration for context loading."""

    # Token budgets per query type
    SYSTEM_QUERY_TOKENS: int = 2000      # System specs + minimal KB
    RESEARCH_QUERY_TOKENS: int = 4000    # System specs + full KB + web
    PLANNING_QUERY_TOKENS: int = 3500    # System specs + historical data
    GENERAL_QUERY_TOKENS: int = 1000     # Minimal context

    # Cache settings
    CACHE_TTL_SECONDS: int = 300         # 5 minutes
    CACHE_ENABLED: bool = True

    # KB search settings
    KB_MIN_SIMILARITY: float = 0.3       # Minimum relevance score
    KB_MAX_DOCS_SYSTEM: int = 1          # Max docs for system queries
    KB_MAX_DOCS_RESEARCH: int = 5        # Max docs for research queries
    KB_MAX_DOCS_PLANNING: int = 3        # Max docs for planning queries

    # Conversation history
    MAX_CONVERSATION_MESSAGES: int = 5   # Last N messages

    # Fallback behavior
    FALLBACK_ON_CACHE_MISS: bool = True
    FALLBACK_ON_ERROR: bool = True

# Load from environment with defaults
config = ContextConfig()
```

### 7. Testing Requirements

**File:** `railway/tests/test_context_manager.py`

**Test Cases:**

1. **Query Classification:**
   - System queries correctly classified
   - Research queries correctly classified
   - Planning queries correctly classified
   - Edge cases handled

2. **Context Loading:**
   - System context always included
   - User context included when user_id provided
   - KB context filtered by relevance
   - Token budget respected

3. **Caching:**
   - Cache hit returns cached data
   - Cache miss loads fresh data
   - Cache expiration works (TTL)
   - Cache key uniqueness per user/query

4. **Token Counting:**
   - Total tokens calculated correctly
   - Token budget not exceeded
   - Truncation happens gracefully

5. **Error Handling:**
   - Redis unavailable → fallback works
   - Invalid query → defaults used
   - Missing context → partial context returned

**Example Test:**
```python
def test_system_query_uses_minimal_context():
    """System queries should not load full KB."""
    ctx_mgr = ContextManager()
    bundle = ctx_mgr.get_relevant_context(
        query="What's my battery level?",
        user_id="test_user"
    )

    assert bundle.query_type == QueryType.SYSTEM
    assert bundle.total_tokens < 2500  # Much less than 5k-8k
    assert "system_specs" in bundle.system_context
    assert bundle.kb_context == "" or len(bundle.kb_context) < 500
```

### 8. Monitoring & Metrics

**Add to:** `railway/src/api/main.py`

**Track Context Metrics:**
```python
# Log context metadata for monitoring
logger.info(
    "context_loaded",
    extra={
        "query_type": context_bundle.query_type,
        "total_tokens": context_bundle.total_tokens,
        "cache_hit": context_bundle.cache_hit,
        "kb_docs_included": len(context_bundle.kb_docs),
        "user_id": user_id
    }
)
```

**Metrics to Track:**
- Average tokens per query (by query type)
- Cache hit rate (target: >60%)
- Context loading time (target: <200ms)
- Token savings vs. baseline (target: 40% reduction)

### 9. Environment Variables

**Add to:** `.env` and Railway

```bash
# Redis Configuration
REDIS_URL=redis://localhost:6379
REDIS_PASSWORD=your-password-if-needed
REDIS_SSL=false

# Context Configuration
CONTEXT_MAX_TOKENS=3000
CONTEXT_CACHE_TTL=300
CONTEXT_CACHE_ENABLED=true
KB_MIN_SIMILARITY=0.3
```

### 10. Migration Strategy

**Phase 1: Build (Week 1)**
- Create ContextManager service
- Add Redis client
- Write unit tests
- Local testing

**Phase 2: Integration (Week 2)**
- Update Solar Controller agent
- Update API endpoint
- Add context metadata to responses
- Test end-to-end

**Phase 3: Rollout (Week 3)**
- Deploy to staging
- A/B test (50% old, 50% new)
- Monitor metrics
- Full cutover if successful

**Phase 4: Cleanup (Week 3)**
- Remove old context loading code
- Update documentation
- Celebrate token savings!

---

## Success Criteria

### Performance Targets

| Metric | Baseline (V1.7) | Target (V2.0) | How to Measure |
|--------|-----------------|---------------|----------------|
| Avg tokens/query | 5k-8k | 3k-5k | OpenAI API logs |
| Context load time | N/A (not cached) | <200ms (cache hit) | API metrics |
| Cache hit rate | 0% | 60%+ | Redis metrics |
| Token cost/query | $0.025-$0.040 | $0.015-$0.025 | OpenAI bills |

### Quality Targets

| Metric | Baseline | Target | How to Measure |
|--------|----------|--------|----------------|
| Agent accuracy | 85% | 90%+ | User feedback |
| Response completeness | Good | Good | Manual testing |
| KB relevance | 70% | 85%+ | Document review |

### Business Targets

| Metric | Baseline | Target | Impact |
|--------|----------|--------|--------|
| Monthly OpenAI cost | $80-100 | $48-60 | 40% reduction |
| User satisfaction | 4.0/5 | 4.5/5 | Faster responses |
| System scalability | 100 queries/day | 500+ queries/day | Lower per-query cost |

---

## Edge Cases to Handle

1. **No Cache Available:**
   - Redis down or unreachable
   - Fallback to direct context loading
   - Log warning but don't fail request

2. **Token Budget Exceeded:**
   - Truncate KB context intelligently (keep most relevant)
   - Always include system context (critical)
   - Log warning for monitoring

3. **Empty Context:**
   - No KB docs match query
   - Return minimal context (system specs only)
   - Agent should handle gracefully

4. **Multiple Concurrent Requests:**
   - Cache stampede protection (don't reload if loading)
   - Request coalescing for same query
   - Rate limiting on cache writes

5. **Stale Cache:**
   - TTL ensures freshness (5 min)
   - Invalidate on system config changes
   - Manual cache clear endpoint

---

## Deliverables Checklist

### Code
- [ ] `context_manager.py` - Core logic
- [ ] `redis_client.py` - Redis wrapper
- [ ] `context_classifier.py` - Query classification
- [ ] `context_config.py` - Configuration
- [ ] Update all 4 agents to use ContextManager
- [ ] Update `/ask` endpoint with metadata

### Tests
- [ ] Unit tests for ContextManager
- [ ] Unit tests for RedisClient
- [ ] Integration tests for agents
- [ ] End-to-end API tests
- [ ] Performance benchmarks

### Documentation
- [ ] Code comments and docstrings
- [ ] Architecture diagram
- [ ] Migration guide
- [ ] Monitoring guide
- [ ] Troubleshooting guide

### Deployment
- [ ] Railway Redis add-on configured
- [ ] Environment variables set
- [ ] Staging deployment tested
- [ ] Production deployment
- [ ] Rollback plan documented

---

## Example Usage

### Before (V1.7 - Current):
```python
# User asks: "What's my battery level?"
# Loads: 24KB context (5k-8k tokens)
# Cost: $0.025-$0.040
# Time: ~5-8s

full_context = get_context_files()  # Everything!
crew = create_energy_crew(query, full_context)
```

### After (V2.0 - Smart):
```python
# User asks: "What's my battery level?"
# Loads: 8KB context (2k-3k tokens) - CACHED
# Cost: $0.010-$0.015
# Time: ~3-5s (cache hit: <1s context load)

context_mgr = ContextManager()
context = context_mgr.get_relevant_context(
    query="What's my battery level?",
    user_id="user123",
    max_tokens=3000
)
# context.query_type = QueryType.SYSTEM
# context.total_tokens = 2400
# context.cache_hit = True
# context.kb_context = "" (not needed for system query)

crew = create_energy_crew(query, context)
```

---

## Questions to Answer During Implementation

1. **Classification Accuracy:** How often does the classifier correctly identify query type?
   - Track: classification accuracy metric
   - Target: 90%+ correct classification

2. **Cache Hit Rate:** Are we getting cache hits for repeated queries?
   - Track: Redis cache hit rate
   - Target: 60%+ hit rate

3. **Token Savings:** Are we actually using fewer tokens?
   - Track: tokens per query (before/after)
   - Target: 40% reduction

4. **Response Quality:** Did accuracy decrease with less context?
   - Track: user feedback scores
   - Target: Maintain or improve accuracy

5. **Performance Impact:** Is context loading faster?
   - Track: context load time
   - Target: <200ms for cache hit

---

## Prompt for Claude Code

**Copy this section when you're ready to implement:**

---

**Task:** Implement 1.8.0 Smart Context Loading with Redis caching

**Goal:** Reduce token usage by 40% and improve response times by intelligently loading only relevant context.

**What to do:**

1. Create `ContextManager` service that:
   - Classifies queries into types (system, research, planning, general)
   - Loads only relevant context based on query type
   - Caches context bundles in Redis with 5-minute TTL
   - Respects token budgets (default: 3000 tokens)
   - Falls back gracefully if Redis unavailable

2. Create `RedisClient` wrapper with:
   - Connection pooling and retry logic
   - Get/set/delete operations
   - Health check endpoint
   - Graceful degradation

3. Update all 4 agents (Solar Controller, Energy Orchestrator, Research Agent, Manager) to use ContextManager instead of loading full context

4. Enhance `/ask` API endpoint to:
   - Use ContextManager for smart context loading
   - Return context metadata (tokens, cache hit, query type)
   - Log context metrics for monitoring

5. Add comprehensive tests for:
   - Query classification accuracy
   - Context loading logic
   - Redis caching behavior
   - Token budget enforcement
   - Error handling

**Reference:** See `docs/V2.0_ROADMAP.md` section #2 for detailed architecture

**Files to create:**
- `railway/src/services/context_manager.py`
- `railway/src/services/redis_client.py`
- `railway/src/services/context_classifier.py`
- `railway/src/config/context_config.py`
- `railway/tests/test_context_manager.py`

**Files to modify:**
- `railway/src/agents/solar_controller.py`
- `railway/src/agents/energy_orchestrator.py`
- `railway/src/agents/research_agent.py`
- `railway/src/agents/manager.py`
- `railway/src/api/main.py`
- `railway/.env`

**Success criteria:**
- [ ] Tokens per query reduced by 40% (5k-8k → 3k-5k)
- [ ] Cache hit rate >60%
- [ ] Context load time <200ms (cache hit)
- [ ] All tests passing
- [ ] Agent accuracy maintained or improved

**Environment setup:**
```bash
# Add to Railway
REDIS_URL=${{Redis.REDIS_URL}}
CONTEXT_MAX_TOKENS=3000
CONTEXT_CACHE_ENABLED=true
```

**Testing:**
```bash
# Test with different query types
curl -X POST https://api.wildfireranch.us/ask \
  -d '{"message": "What is my battery level?", "user_id": "test"}' \
  # Should return: query_type=system, tokens~2500, cache_hit=false (first time)

# Same query again
curl -X POST https://api.wildfireranch.us/ask \
  -d '{"message": "What is my battery level?", "user_id": "test"}' \
  # Should return: query_type=system, tokens~2500, cache_hit=true (cached!)
```

Please implement this feature following the architecture in `PROMPT_V2.0_SMART_CONTEXT.md` and `docs/V2.0_ROADMAP.md` section #2.

---

**Ready to implement!** This prompt gives Claude Code everything needed to build the smart context loading feature. 🚀
