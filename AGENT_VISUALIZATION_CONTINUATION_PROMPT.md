# Multi-Agent Visualization Dashboard - Continuation Prompt

**Context:** We're building a sophisticated agent monitoring dashboard integrated into the `/chat` page.

**Status:** Phase 1 Foundation Complete (5/11 components done)

---

## 🎯 What to Build Next

Continue implementing the **ChatAgentPanel** - the main side panel component that integrates all agent insights into the chat interface.

---

## 📋 Quick Context

### What's Already Done ✅
1. **Types**: `vercel/src/types/insights.ts` - All TypeScript interfaces
2. **Hook**: `vercel/src/hooks/useSessionInsights.ts` - Data fetching with auto-refresh
3. **Components**:
   - `AgentBadge.tsx` - Color-coded agent indicators
   - `TokenUsageBar.tsx` - Token usage visualization with context breakdown

### What's Next ⏳
1. **ChatAgentPanel.tsx** - Main collapsible side panel (280px wide)
2. **Update chat/page.tsx** - Integrate panel with toggle button
3. **AgentContributionGraph.tsx** - Pie chart showing agent contributions
4. **ContextBreakdownChart.tsx** - V1.8 Smart Context visualization
5. **API endpoints** - Backend session insights

---

## 🚀 Step-by-Step Implementation Plan

### Step 1: Create ChatAgentPanel Component

**File:** `vercel/src/components/chat/ChatAgentPanel.tsx`

**Requirements:**
- Collapsible side panel (slides from right)
- 280px wide when open
- Tab navigation: Overview | Agents | Context | Performance
- Real-time session insights display
- Smooth animations with Framer Motion
- Responsive (slides from bottom on mobile)

**Key Features:**
```tsx
// Overview Tab:
- Session summary stats
- Agent contribution pie chart
- Token usage timeline
- Cache hit rate gauge

// Agents Tab:
- List of agents used in session
- Each agent's contribution percentage
- Response times
- Success rates

// Context Tab (V1.8):
- Token breakdown (System/KB/Conversation/User)
- Query type distribution
- Cache performance
- Cost savings calculator

// Performance Tab:
- Response time trends
- Token efficiency
- Tool usage stats
- Error tracking
```

**Props:**
```tsx
interface ChatAgentPanelProps {
  isOpen: boolean
  onClose: () => void
  sessionId: string
  messages: Message[]
  insights: SessionInsights | null
  liveMetrics: LiveMetrics | null
  loading?: boolean
}
```

---

### Step 2: Update Chat Page

**File:** `vercel/src/app/chat/page.tsx`

**Changes:**
1. Add panel state: `const [panelOpen, setPanelOpen] = useState(false)`
2. Import and use `useSessionInsights` hook
3. Add toggle button in header (BarChart3 icon from lucide-react)
4. Adjust layout to accommodate panel
5. Pass props to ChatAgentPanel

**Layout adjustment:**
```tsx
<div className="h-full flex flex-col">
  {/* Header with toggle */}
  <div className="bg-white border-b p-4 flex items-center justify-between">
    <div>
      <h1>AI Energy Assistant</h1>
      <p>Session: {sessionId.slice(0, 8)}...</p>
    </div>
    <div className="flex gap-2">
      <button onClick={() => setPanelOpen(!panelOpen)}>
        <BarChart3 className="w-5 h-5" />
        Insights
      </button>
      {/* existing buttons */}
    </div>
  </div>

  {/* Chat area - adjust margin when panel open */}
  <div className={`flex-1 overflow-y-auto ${panelOpen ? 'mr-80' : ''}`}>
    {/* existing messages */}
  </div>

  {/* Agent Panel */}
  <ChatAgentPanel
    isOpen={panelOpen}
    onClose={() => setPanelOpen(false)}
    sessionId={sessionId}
    messages={messages}
    insights={insights}
    liveMetrics={liveMetrics}
    loading={loading}
  />
</div>
```

---

### Step 3: Create AgentContributionGraph

**File:** `vercel/src/components/chat/AgentContributionGraph.tsx`

**Requirements:**
- Use Recharts PieChart
- Show % contribution per agent
- Color-coded by agent
- Interactive legend
- Click to highlight agent messages
- Animated entrance

**Example:**
```tsx
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts'
import { AgentContribution } from '@/types/insights'

// Transform data for pie chart
const chartData = contributions.map(c => ({
  name: c.agent,
  value: c.percentage,
  queries: c.query_count
}))

<PieChart>
  <Pie
    data={chartData}
    dataKey="value"
    nameKey="name"
    cx="50%"
    cy="50%"
    innerRadius={60}
    outerRadius={80}
  >
    {chartData.map((entry, index) => (
      <Cell key={index} fill={AGENT_COLORS[entry.name].bg} />
    ))}
  </Pie>
  <Tooltip />
  <Legend />
</PieChart>
```

---

### Step 4: Create ContextBreakdownChart

**File:** `vercel/src/components/chat/ContextBreakdownChart.tsx`

**Requirements:**
- Stacked bar chart using Recharts
- Show System/KB/Conversation/User context distribution
- Color-coded by CONTEXT_COLORS
- Per-message view or aggregated
- Tooltip with token counts
- Export to PNG button

**Data structure:**
```tsx
const data = [
  {
    category: 'System',
    tokens: breakdown.system_context,
    percentage: (breakdown.system_context / total) * 100,
    color: CONTEXT_COLORS.system
  },
  // ... other categories
]
```

---

### Step 5: Add API Endpoint (Backend)

**File:** `railway/src/api/main.py`

**Endpoint:** `GET /chat/sessions/{session_id}/insights`

**Implementation:**
```python
@app.get("/chat/sessions/{session_id}/insights")
async def get_session_insights(session_id: str):
    """
    Get aggregated insights for a chat session.

    Returns:
    - Agent contributions
    - Token metrics
    - Cache performance
    - Cost analysis
    """
    try:
        from ..utils.conversation import get_conversation_context
        from ..services.context_manager import ContextManager

        # Query conversations table for session messages
        messages = query_all(
            conn,
            """
            SELECT
                role,
                content,
                created_at,
                agent_role,
                duration_ms,
                -- V1.8 metadata (if stored)
                metadata->>'context_tokens' as context_tokens,
                metadata->>'cache_hit' as cache_hit,
                metadata->>'query_type' as query_type
            FROM conversations
            WHERE conversation_id = %s
            ORDER BY created_at ASC
            """,
            (session_id,),
            as_dict=True
        )

        # Calculate insights
        insights = calculate_session_insights(messages)

        return {
            "success": True,
            "data": insights
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
```

---

## 🎨 Design Reference

**Panel Layout:**
```
┌─────────────────────────────────┐
│ 🎯 Session Insights        [×] │ Header
├─────────────────────────────────┤
│ [Overview][Agents][Context]    │ Tabs
├─────────────────────────────────┤
│                                 │
│  📊 Quick Stats                │
│  ┌────┬────┬────┬────┐         │
│  │ 6  │85% │2.4k│67% │         │
│  │ Q  │Suc │Tok │Hit │         │
│  └────┴────┴────┴────┘         │
│                                 │
│  Agent Contributions            │
│  ┌─────────────────────────┐   │
│  │  [Pie Chart]           │   │
│  │  Manager: 15%          │   │
│  │  Solar: 85%            │   │
│  └─────────────────────────┘   │
│                                 │
│  Token Usage                    │
│  ┌─────────────────────────┐   │
│  │  [Bar Chart]           │   │
│  │  System: 1800tk        │   │
│  │  KB: 400tk             │   │
│  │  Conversation: 200tk   │   │
│  └─────────────────────────┘   │
│                                 │
│  Cache Performance              │
│  ┌─────────────────────────┐   │
│  │   67% [Gauge]          │   │
│  │   4 hits / 6 queries   │   │
│  └─────────────────────────┘   │
│                                 │
├─────────────────────────────────┤
│ 🟢 Live • Updated 2s ago       │ Footer
└─────────────────────────────────┘
```

---

## 📦 Components to Import/Use

**Already Created:**
```tsx
import AgentBadge from '@/components/chat/AgentBadge'
import TokenUsageBar from '@/components/chat/TokenUsageBar'
import { useSessionInsights } from '@/hooks/useSessionInsights'
import { AGENT_COLORS, CONTEXT_COLORS } from '@/types/insights'
```

**From Libraries:**
```tsx
import { motion, AnimatePresence } from 'framer-motion'
import { BarChart3, X, TrendingUp, Activity, Zap, DollarSign } from 'lucide-react'
import { PieChart, Pie, BarChart, Bar, LineChart, Line, Cell } from 'recharts'
```

---

## ✅ Testing Checklist

After implementation, verify:
- [ ] Panel slides in/out smoothly
- [ ] Tab navigation works
- [ ] Charts render correctly with real data
- [ ] Mobile responsive (panel from bottom)
- [ ] No performance impact on chat
- [ ] Data updates in real-time
- [ ] Loading states display correctly
- [ ] Error handling graceful
- [ ] Keyboard accessible (ESC to close)
- [ ] Dark mode compatible (future)

---

## 🚀 Quick Start Commands

```bash
# Navigate to project
cd /workspaces/CommandCenter/vercel

# Create component
touch src/components/chat/ChatAgentPanel.tsx

# Start dev server (if needed)
npm run dev

# Test the chat page
# Navigate to http://localhost:3000/chat
```

---

## 📚 Key Files to Reference

1. **Progress tracking**: `AGENT_VISUALIZATION_PROGRESS.md`
2. **Type definitions**: `src/types/insights.ts`
3. **Data hook**: `src/hooks/useSessionInsights.ts`
4. **Existing agent page**: `src/app/agents/page.tsx` (for chart examples)
5. **Chat page**: `src/app/chat/page.tsx` (to modify)

---

## 🎯 Success Criteria

**Phase 1 Complete When:**
1. Panel toggles smoothly in chat interface
2. All tabs display correctly
3. Agent contributions visualized
4. Token usage shows breakdown
5. Real-time updates working
6. No console errors
7. Responsive on mobile
8. Loading/error states handled

**Estimated Time:** 2-3 hours for complete Phase 1 implementation

---

## 💡 Implementation Tips

1. **Start simple**: Get basic panel showing, then add features
2. **Use existing patterns**: Reference `src/app/agents/page.tsx` for chart code
3. **Test incrementally**: Check panel, then tabs, then charts
4. **Reuse components**: AgentBadge and TokenUsageBar are ready to use
5. **Fallback data**: useSessionInsights calculates from messages if API unavailable
6. **Mobile-first**: Use `className={panelOpen ? 'mr-80 lg:mr-80 mr-0' : ''}` for responsive

---

## 🔄 Next Prompt (If Stuck)

```
Continue implementing the ChatAgentPanel component for the multi-agent visualization dashboard.

Status: [Describe what you completed]
Issue: [Describe any blockers]

Please help with: [Specific request]

Reference: AGENT_VISUALIZATION_CONTINUATION_PROMPT.md
```

---

**Ready to build!** Start with ChatAgentPanel.tsx and watch the sophisticated agent insights come to life! 🚀
