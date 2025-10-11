# CommandCenter Architecture Decisions

**Purpose:** Document key architectural decisions, trade-offs, and rationale
**Last Updated:** October 11, 2025

---

## 🏗️ Core Architecture: Specialized Multi-Agent System

### Decision: 3-Tier Specialized Agents vs. General Agent

**Date:** V1.0 (Validated Session 027, October 11, 2025)

**Context:**
- Energy management system requires different types of expertise
- Users ask status queries (80%), planning questions (15%), documentation (5%)
- Response time and accuracy are critical for user experience

**Options Considered:**

1. **Single General Agent** (Rejected)
   - Pros: Simple routing, handles all queries
   - Cons: Slow (10-15s), expensive, less accurate, hard to maintain

2. **Specialized Agents with Router** (CHOSEN)
   - Pros: Fast (5-6s), accurate, optimized prompts, clear responsibilities
   - Cons: Requires routing logic, edge case handling

**Decision:** Use specialized agents with Manager router

**Rationale:**
- 80%+ of queries are energy-specific (battery, solar, load)
- Specialized tools reduce prompt size and improve accuracy
- KB fast-path provides 400ms responses for documentation (50x faster)
- Clear separation makes debugging and maintenance easier
- Cost-effective: smaller prompts = fewer tokens per query

**Trade-offs Accepted:**
- Edge case handling requires additional logic (meta queries, off-topic)
- Manager routing adds 1-2s overhead vs. direct agent call
- Keyword-based fast-path less intelligent than LLM routing

**Validation (Session 027):**
- ✅ Query accuracy: >95% for energy queries
- ✅ Response time: 5-6s (status), 13-15s (planning), 400ms (KB)
- ✅ User satisfaction: High for primary use cases
- ⚠️ Edge case handling: 15% of queries need improvement

**Recommendation:** KEEP specialized architecture, improve edge case fallback

---

## 🚀 KB Fast-Path: Keyword Bypass vs. Full Routing

### Decision: Add Keyword-Based Fast-Path for Documentation Queries

**Date:** V1.5 (October 2025)

**Problem:**
- Documentation queries ("what is the threshold?") via Manager took 20+ seconds
- Users frustrated by slow responses to simple questions
- Manager routing added unnecessary overhead for KB searches

**Options Considered:**

1. **Always Route Through Manager** (Original)
   - Pros: Intelligent routing, consistent flow
   - Cons: 20+ second response time, poor UX

2. **Keyword-Based Fast-Path** (CHOSEN)
   - Pros: 400ms response (50x faster), simple implementation
   - Cons: Brittle matching, misses some queries

3. **LLM Intent Classification**
   - Pros: More intelligent than keywords
   - Cons: Still adds 2-3s overhead, complexity

**Decision:** Implement keyword-based fast-path at API level

**Implementation:**
```python
kb_keywords = ['specification', 'specs', 'threshold', 'policy',
               'procedure', 'maintain', 'documentation', 'guide',
               'manual', 'instructions', 'how do i', 'how to']

if any(keyword in query_lower for keyword in kb_keywords):
    # Direct KB search - bypass Manager
    return search_knowledge_base(query)
```

**Trade-offs Accepted:**
- Keyword matching less intelligent than LLM routing
- False negatives: Some KB queries miss fast-path
- Maintenance: Need to update keywords as patterns emerge

**Results:**
- ✅ Response time: 400ms (vs. 20+ seconds)
- ✅ User satisfaction: Significantly improved
- ⚠️ Coverage: ~70% of documentation queries hit fast-path
- ⚠️ Edge cases: "what is command center" misses fast-path (Session 027)

**Future Improvements (V1.5.1):**
- Add specific patterns: "what is the command", "system overview"
- Monitor query patterns to expand keyword list
- Consider hybrid: keywords + LLM confidence scoring

---

## 📊 Knowledge Base: Two-Tier System

### Decision: Context Files + Semantic Search

**Date:** V1.5 (October 2025)

**Context:**
- Some information is critical and should always be available (Tier 1)
- Detailed documentation should be searchable on-demand (Tier 2)
- Embedding every document into every prompt is expensive and slow

**Options Considered:**

1. **Load Everything into System Prompt** (Rejected)
   - Pros: Always available, no search needed
   - Cons: Massive prompts (10k+ tokens), expensive, slow

2. **Search Everything On-Demand** (Rejected)
   - Pros: Small prompts, flexible
   - Cons: Critical info might not be found, slower

3. **Two-Tier: Context + Search** (CHOSEN)
   - Pros: Critical info always loaded, detailed info searchable
   - Cons: Requires classification (what's Tier 1 vs. Tier 2)

**Decision:** Implement two-tier system

**Implementation:**
- **Tier 1 (Context Files):** `is_context_file = TRUE`, always loaded
- **Tier 2 (Full KB):** Vector search with pgvector, on-demand

**Classification Rules:**
- Tier 1: Thresholds, policies, critical procedures, system overview
- Tier 2: Detailed manuals, technical specs, troubleshooting guides

**Results:**
- ✅ Context files provide instant access to critical info
- ✅ Semantic search finds detailed information accurately
- ✅ Prompt size remains manageable (<5k tokens)
- ⚠️ Context file quality matters (Session 027: CommandCenter overview needed)

---

## 🔄 Manager Agent: Router-Only vs. Conversational

### Decision: Manager as Pure Router (No Conversation)

**Date:** V1.5 (Refined Session 023, October 2025)

**Problem:**
- Original Manager tried to "help" by reformatting responses
- This caused confusion and longer response times
- Users wanted specialist responses verbatim

**Options Considered:**

1. **Conversational Manager** (Original)
   - Pros: Can add context, explain routing
   - Cons: Reformats responses, adds latency, confuses users

2. **Pure Router (Verbatim Pass-Through)** (CHOSEN)
   - Pros: Fast, predictable, maintains specialist voice
   - Cons: Can't add meta-commentary or explanations

**Decision:** Manager returns tool output verbatim

**Implementation:**
```python
backstory="""You are a ROUTING-ONLY agent. Your ONLY job is to call the right
tool and return its output EXACTLY as received - DO NOT reformat, summarize,
or add commentary."""
```

**Trade-offs Accepted:**
- Manager can't provide context about routing decisions
- Can't explain why a query was routed to a specific agent
- No opportunity to clarify or qualify specialist responses

**Results:**
- ✅ Faster responses (no reformatting overhead)
- ✅ Clearer specialist expertise (maintains voice)
- ✅ Predictable behavior (tool output = final output)
- ⚠️ Edge cases still need handling (Session 027: meta queries)

**Refinement (Session 027):**
- Add explicit fallback for meta/off-topic queries
- Manager should respond directly (brief) without routing
- Keep verbatim pass-through for energy queries

---

## 🛡️ Edge Case Handling: Fallback Strategy

### Decision: Manager-Level Fallback vs. API-Level Pre-Router

**Date:** V1.5.1 (Planned, October 11, 2025)

**Problem (Session 027):**
- Meta queries ("what is command center") route incorrectly
- Off-topic queries ("who am I") cause hangs or wrong responses
- Current Manager tries to route everything to tools

**Options Considered:**

1. **API-Level Pre-Router** (Pattern Matching)
   - Pros: Fastest (no LLM call), guaranteed correct for obvious cases
   - Cons: Brittle, requires maintenance, less flexible

2. **Manager-Level Fallback** (LLM-Based) (CHOSEN)
   - Pros: Intelligent classification, handles nuance, flexible
   - Cons: Requires LLM call (~1s), relies on prompt engineering

3. **General Agent** (Rejected - Session 027)
   - Pros: Handles all query types naturally
   - Cons: Slow, expensive, less accurate for energy queries

**Decision:** Add intelligent fallback to Manager agent

**Implementation:**
```python
# Update Manager backstory
CRITICAL ROUTING RULES:

1. SYSTEM/META QUERIES → Respond directly (NO TOOL)
2. OFF-TOPIC QUERIES → Polite redirect (NO TOOL)
3. AMBIGUOUS QUERIES → Ask for clarification (NO TOOL)
4. ENERGY QUERIES → Route to appropriate tool
```

**Rationale:**
- Manager already has LLM capability for classification
- Small prompt additions (<500 tokens) won't impact performance
- More maintainable than keyword lists for edge cases
- Preserves optimized routing for primary use cases (80%)

**Expected Results:**
- Meta queries: ~1-2s response (vs. wrong routing)
- Off-topic queries: ~1s polite redirect (vs. hang)
- Energy queries: No change (still 5-6s)
- Coverage: 95%+ queries handled correctly

---

## 📈 Performance vs. Intelligence Trade-offs

### Architectural Principle: Optimize for Common Cases

**Philosophy:**
- 80% of queries are energy status/planning (optimize aggressively)
- 15% are documentation (KB fast-path)
- 5% are edge cases (acceptable to be slower/less optimized)

**Applied Decisions:**

| Query Type | Approach | Speed | Intelligence | Justification |
|-----------|----------|-------|--------------|---------------|
| Energy (80%) | Specialized agents | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Primary use case |
| Documentation (15%) | KB fast-path | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | Speed > perfect routing |
| Edge cases (5%) | Manager fallback | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Acceptable slower |

**Key Insight:** Don't sacrifice 80% performance to optimize 5% edge cases

---

## 🔮 Future Decisions

### Under Consideration (V1.6+)

1. **Hybrid Fast-Path:** Keywords + LLM confidence scoring
   - Pro: Best of both worlds
   - Con: Complexity, harder to debug

2. **Intent Classification Layer:** Pre-router before Manager
   - Pro: Clear categorization, faster routing
   - Con: Additional latency, maintenance

3. **User Feedback Loop:** Learn from routing mistakes
   - Pro: Self-improving system
   - Con: Requires telemetry, user engagement

4. **Context File Auto-Loading:** Load into specialist agents
   - Pro: Always have baseline knowledge
   - Con: Larger prompts, higher costs

### Not Pursuing

❌ **General Agent:** Validated as wrong approach (Session 027)
❌ **Full LLM Routing:** Too slow for KB queries
❌ **Load All KB into Prompts:** Too expensive, impractical

---

## 📚 Decision Log

| Date | Decision | Rationale | Session |
|------|----------|-----------|---------|
| V1.0 | Specialized agents | Accuracy + speed for energy queries | Initial |
| V1.5 | KB fast-path | 50x speedup for documentation | - |
| V1.5 | Manager verbatim | Maintain specialist voice | Session 023 |
| V1.5.1 | Manager fallback | Handle edge cases intelligently | Session 027 |

---

## 🔍 Validation Methodology

**How We Validate Decisions:**

1. **Query Analysis:** Review last 100 conversations, categorize patterns
2. **Performance Metrics:** Measure response times per agent/path
3. **User Feedback:** Track satisfaction, complaints, confusion
4. **Cost Analysis:** Token usage per query type
5. **Maintenance Burden:** Complexity, debugging effort

**Decision Review Triggers:**
- Major user complaints (>5 in a session)
- Performance degradation (>20% slower)
- Cost increase (>50% token usage)
- New use cases that don't fit current architecture

---

**Maintained By:** Wildfire Ranch Technical Team
**Review Cadence:** After each major architecture change
**Status:** Living document - updates as system evolves
