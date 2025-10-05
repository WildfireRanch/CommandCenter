# Component Inventory - Next.js Frontend

## Complete Component List

### Pages (App Router)

| Route | Component | Purpose | CommandCenter Relevance |
|-------|-----------|---------|------------------------|
| `/dashboard` | Dashboard wizard | Onboarding setup | ⭐⭐ Good UX pattern |
| `/status` | Status page | System health monitoring | ⭐⭐⭐ ESSENTIAL - needs update to Railway API |
| `/ask` | Ask page | Agent chat interface | ⭐⭐⭐ ESSENTIAL - map to `/agent/ask` |
| `/logs` | Logs page | View system logs | ⭐⭐ Useful for debugging |
| `/audit` | Audit page | Audit trail display | ⭐ Nice to have |
| `/action-queue` | Action queue | Queue monitoring | ⭐⭐ Useful for agent actions |
| `/flow-monitor` | Flow monitor | Agentic flow visualization | ⭐⭐ Good for multi-agent crews |
| `/control` | Control panel | System control interface | ⭐⭐⭐ Hardware control |
| `/docs` | Docs viewer | Documentation viewer | ⭐ Knowledge base integration |
| `/search` | Search panel | Search functionality | ⭐ KB search |
| `/settings` | Settings page | Configuration | ⭐⭐ System config |
| `/ops` | Ops panel | Operations interface | ⭐⭐ Operations dashboard |

### Components

#### High Priority (Reuse for CommandCenter)

**StatusPanel** (`components/StatusPanel.tsx`)
- Purpose: System health, environment, context status
- What to keep: Layout pattern, card structure, refresh logic
- What to update: API endpoints → Railway `/health`, `/energy/latest`
- **Action**: Adapt for CommandCenter monitoring

**AskAgent** (`components/AskAgent/`)
- Files: `ChatWindow.tsx`, `ChatMessage.tsx`, `InputBar.tsx`, `useAskEcho.ts`
- Purpose: Agent chat interface with conversation history
- What to keep: Chat UI, message rendering, input handling
- What to update: API endpoint → Railway `/agent/ask`, session management
- **Action**: Primary user interface for agent interaction

**LogsPanel** (`components/LogsPanel/LogsPanel.tsx`)
- Purpose: Real-time log viewing
- What to keep: Log display pattern
- What to update: Connect to Railway logs or database queries
- **Action**: Essential for debugging agent behavior

#### Medium Priority (Adapt Later)

**AgenticFlowMonitor** (`components/AgenticFlowMonitor/`)
- Purpose: Visualize multi-agent workflows
- Relevance: Useful once we have crews running
- **Action**: Save for when CrewAI crews are active

**ActionQueue** (`components/ActionQueue/ActionQueuePanel.tsx`)
- Purpose: Display pending/completed actions
- Relevance: Track hardware commands, agent tasks
- **Action**: Connect to database action logs

**Dashboard** (`components/dashboard/Dashboard.tsx`)
- Purpose: Onboarding wizard
- Relevance: Good UX for first-time setup
- **Action**: Repurpose for CommandCenter onboarding

**MemoryPanel** (`components/MemoryPanel.tsx`)
- Purpose: Display agent memory/context
- Relevance: Show conversation context
- **Action**: Connect to `/conversations/{session_id}`

#### Low Priority (Reference Only)

**DocsSyncPanel** (`components/DocsSyncPanel.tsx`)
- Purpose: Google Docs sync
- Relevance: Knowledge base sync (if we add Google Docs integration)
- **Action**: Save for V2

**DocsViewer** (`components/DocsViewer/`)
- Purpose: View documentation
- Relevance: Display KB content
- **Action**: Nice to have for V2

**GmailOps** (`components/GmailOps/GmailOpsPanel.tsx`)
- Purpose: Gmail integration
- Relevance: Not currently planned
- **Action**: Ignore for now

**SearchPanel** (`components/SearchPanel.tsx`)
- Purpose: Search across docs
- Relevance: KB search functionality
- **Action**: V2 feature

### UI Components (Shadcn/UI)

All reusable UI primitives from Shadcn:
- `button`, `card`, `input`, `label`, `tabs`, `tooltip`, `progress`, etc.
- **Action**: KEEP - These are excellent, well-tested components

### Utilities

**lib/api.ts** - API client configuration
- Current: Points to old Relay service
- Update to: CommandCenter Railway API
- **Action**: Critical - update endpoints

**lib/askClient.ts** - Agent chat client
- Purpose: Handle agent requests/responses
- **Action**: Update for new API format

## 🎯 Recommended Reuse Strategy

### Tier 1: Must Reuse (Immediate Value)
1. **StatusPanel** → Adapt for system health monitoring
2. **AskAgent** → Primary agent interface
3. **Shadcn/UI components** → All UI primitives
4. **API client pattern** → Update endpoints

### Tier 2: Should Reuse (Next Phase)
5. **LogsPanel** → Debugging and monitoring
6. **ActionQueue** → Track agent actions
7. **Dashboard wizard** → Onboarding flow

### Tier 3: Nice to Have (Future)
8. **AgenticFlowMonitor** → Multi-agent visualization
9. **MemoryPanel** → Context awareness
10. **DocsViewer** → KB integration

### Tier 4: Skip for Now
- Gmail integration
- GitHub diagnostics (not relevant)
- Old "Relay" specific features

## 📦 What to Save vs Delete

### Save (Reference Components)
```
docs/frontend-analysis/reference-components/
├── StatusPanel.tsx           ✅ Saved
├── Dashboard.tsx             ✅ Saved
├── api.ts                    ✅ Saved
├── package.json              ✅ Saved
└── AskAgent/ (to save next)  ⬜ Need to copy
```

### Delete (Old Build Artifacts)
```
old-stack/RelayFrontend/       ❌ Delete (100MB+ of build files)
old-stack/frontend-code.zip    ❌ Delete after extraction
```

### Keep (Source Code)
```
old-stack/frontend/src/        ✅ Keep for now (reference)
old-stack/devtools-dashboard/  ❓ Need to review
```

## 🚀 Next Steps

1. **Copy AskAgent components** to reference folder
2. **Review devtools-dashboard** (might have other useful pieces)
3. **Delete old build artifacts** to save space
4. **Decide**: Fix Next.js now or build Streamlit first?

Would you like me to:
- **A) Copy more components** to reference folder
- **B) Review devtools-dashboard** content
- **C) Clean up old-stack** folder
- **D) Start building Streamlit dashboard** immediately

Your call! 🎯
