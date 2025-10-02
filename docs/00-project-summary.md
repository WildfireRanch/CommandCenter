Agent Stack Migration - Complete Project Summary
Date: October 1, 2025
Status: Discovery Phase - Project Setup
Project Overview
Mission
Migrate existing agent/KB/doc stack to a modern, self-hosted architecture using:

Framework: CrewAI (MIT license, open source)
Platforms: Vercel (frontend/MCP) + Railway (backend services)
MCP Integration: Using Vercel's mcp-handler for Next.js
Development: GitHub Codespaces + Claude Code
GUI Tool: AutoGen Studio for prototyping

User Context

Technical background with limited coding skills
Solo developer wanting to own their stack
Values GUI/visual tools and clear documentation
Needs step-by-step guidance and good project management
Important: Starting fresh - selective porting from old repo, not copying everything

Key Decisions Made
1. Framework Selection: CrewAI
Finalists Considered:

CrewAI (MIT license)
Agno (performance-focused)
AutoGen (Microsoft-backed)
Google ADK (GCP-native)
PydanticAI (type-safe)

Winner: CrewAI

MIT license - 100% free, no vendor lock-in
Easy to use with role-based agent design
100,000+ certified developers in community
No dependencies on other frameworks
Self-hostable with no usage limits

2. Platform Selection: Vercel + Railway
Considered:

Vercel + Railway (chosen)
Google Cloud Platform
Pure self-hosted

Why Vercel + Railway:

300% faster cold starts vs GCP (Railway benchmark)
Simple, predictable pricing vs GCP complexity
Zero-configuration deployment
Excellent developer experience
Platform-agnostic - can migrate later if needed
Cost: ~$15-50/month to start vs ~$100+ for GCP

Cost Comparison:

Railway: $5/month base + pay-per-use
Vercel: $0-20/month (Hobby → Pro)
GCP: Complex billing with surprise charges

3. MCP Integration Strategy
Approach: Next.js + Vercel MCP Handler

Requires only a few lines of code
Deploy-ready templates available
Built-in AI SDK support
Streamable HTTP transport (50% less CPU usage)

4. GUI/Management Tool: AutoGen Studio
Why AutoGen Studio won:

Official Microsoft product (vs community CrewAI Studio)
True drag-and-drop interface
Declarative JSON - export to any framework
890,000+ downloads, active development
Can prototype visually, then export to CrewAI code

Workflow:

Build agents in AutoGen Studio (visual)
Test and iterate (no code)
Export to CrewAI when ready (code)
Deploy to production (Vercel/Railway)

5. Fresh Start Approach
Decision: Start with clean slate, selectively port from old repo

Avoid inheriting bugs and technical debt
Opportunity to rethink architecture
Document what's being brought over (and why)
Build on solid foundation
Audit → Rate (KEEP/REFACTOR/REWRITE/SKIP) → Port selectively

Architecture Decisions
Stack Overview
┌─────────────────────────────────────────┐
│         User / AI Clients               │
│      (Claude, Cursor, etc.)             │
└──────────────┬──────────────────────────┘
               │ MCP Protocol
┌──────────────▼──────────────────────────┐
│    Vercel (Frontend + MCP Server)       │
│    - Next.js application                │
│    - MCP Handler (Streamable HTTP)      │
│    - Fluid Compute enabled              │
└──────────────┬──────────────────────────┘
               │ API calls
┌──────────────▼──────────────────────────┐
│    CrewAI Agents (Orchestration)        │
│    - Role-based agents                  │
│    - Task delegation                    │
│    - Tool integration                   │
└──────────────┬──────────────────────────┘
               │ Data/Services
┌──────────────▼──────────────────────────┐
│    Railway (Backend Services)           │
│    - PostgreSQL database                │
│    - Redis cache                        │
│    - Background jobs                    │
│    - File storage                       │
└─────────────────────────────────────────┘
Component Details
Frontend/MCP Layer (Vercel):

Next.js 14+ with App Router
Vercel MCP Handler for tool exposure
Fluid Compute for 90% cost savings
Global edge network

Agent Layer (CrewAI):

Python-based framework
Role-based agent architecture
Runs on Railway or Vercel Functions
Integrated with MCP tools

Backend Services (Railway):

Pay-per-use pricing (idle = cheap)
Vertical autoscaling
4 datacenter locations
MCP server for meta-deployment

Development:

GitHub Codespaces (free tier)
Claude Code (direct terminal access)
AutoGen Studio (local GUI)
Git-based workflow

Technology Comparison Matrix
FeatureCrewAIAgnoAutoGenGoogle ADKEase of Use⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐Multi-Agent✅ Role-based✅ Lightweight✅ Conversation✅ HierarchicalMemoryLimited✅ Session✅ Flexible✅ PersistentMCP SupportCommunityNative✅ Native✅ NativeLicenseMIT (Free)Open SourceApache 2.0Apache 2.0GUI Available⭐⭐⭐ Community❌ No⭐⭐⭐⭐⭐ Official⭐⭐⭐ BasicProduction Ready✅ Yes✅ Yes✅ Yes✅ YesCommunity100k+Growing290+ contributorsGoogle-backed
Platform Comparison
Vercel + Railway vs Google Cloud
AspectVercel/RailwayGoogle CloudSetup TimeMinutesHours/DaysLearning CurveLowHighPricingSimple, predictableComplex, surprise chargesDXExcellentRequires DevOpsCold StartsFast (Railway)Slow (Cloud Run)Cost (Small)$15-50/month$50-200/monthCost (Large)$500+/month$300+/month (cheaper at scale)Enterprise FeaturesBasicComprehensiveVendor Lock-inHigherLower (more portable)
Project Management Approach
GitHub Structure
commandcenter/
├── docs/
│   ├── sessions/           # Session summaries
│   ├── 01-old-stack-audit.md
│   ├── 02-requirements.md
│   ├── 03-port-plan.md
│   ├── 04-architecture.md
│   └── progress.md
├── src/
│   ├── agents/            # CrewAI agents
│   ├── tools/             # Custom tools
│   ├── mcp/               # MCP server
│   └── config/
├── old-stack/             # Reference only (ported selectively)
├── tests/
└── README.md
Workflow

Planning Sessions (Claude chat) - Architecture, decisions
Implementation Sessions (Claude Code) - Coding, testing, deploying
Review Sessions (Claude chat) - Progress checks, troubleshooting

Session Protocol
Start: State type (planning/implementation), time available, goal
During: Share errors, ask when stuck, request breaks
End: Create summary, update progress, commit code, plan next session
Tracking

GitHub Projects with kanban board
Milestone-based workflow (5 phases)
Weekly rhythm: Plan Monday, Code Tue-Thu, Review Friday
Session summaries after every work session

Development Phases
Phase 1: Discovery (1-2 weeks)

1.1: Old stack audit (rate KEEP/REFACTOR/REWRITE/SKIP)
1.2: Requirements definition
1.3: Selective port plan
1.4: Architecture design

Phase 2: Planning (2-3 days)

Create detailed implementation plan
Set up development environment
Initialize project structure

Phase 3: Build (2-3 weeks)

Environment setup
Port agents one by one (priority order)
MCP integration
Railway services setup

Phase 4: Deploy (3-5 days)

Staging deployment
Testing
Production deployment
Monitoring setup

Phase 5: Optimize (Ongoing)

Performance tuning
Cost optimization
Feature additions

Current Status
Completed ✅

Claude Project created with custom instructions
Project Knowledge base established
GitHub repo: wildfireranch/commandcenter
Fresh Codespace created (blank slate)
README and issue templates added
GitHub Projects board created
Framework and platform decisions finalized
Selective porting strategy defined

Next Steps ⏳

Connect Codespace to repo
Install dependencies (Python, CrewAI, etc.)
Create initial folder structure
Add labels to GitHub repo
Begin Discovery Phase 1.1: Old Stack Audit

Key Questions for Discovery

What does your old agent stack do?
What technologies are you currently using?
Which components work well?
Which components have bugs?
What are must-have vs nice-to-have features?

Resources & Links
Documentation

CrewAI: https://docs.crewai.com/
Vercel MCP: https://vercel.com/docs/mcp
Railway: https://railway.com/
AutoGen Studio: https://microsoft.github.io/autogen/

Project Links

GitHub Repository: https://github.com/wildfireranch/commandcenter
Project Board: [link when created]
Vercel Dashboard: [link when deployed]
Railway Dashboard: [link when deployed]

Success Criteria
Technical Goals

✅ All useful agents successfully migrated
✅ MCP server deployed and working
✅ Response times < 2 seconds
✅ 99% uptime
✅ Cost under $100/month initially

Personal Goals

✅ User can maintain and modify the system
✅ Clear documentation for future reference
✅ Confidence to add new agents
✅ Understanding of architecture
✅ No technical debt from old system

Important Principles
DO:
✅ Start completely fresh
✅ Audit everything before porting
✅ Document all decisions
✅ Test each ported component
✅ Ask "do I really need this?"
✅ Use Claude Code for implementation
✅ Create session summaries
✅ Simplify when possible
DON'T:
❌ Copy entire old repo
❌ Port bugs from old system
❌ Rush the audit process
❌ Skip documentation
❌ Port components you don't understand
❌ Bring over unused code
❌ Use localStorage in artifacts
❌ Deploy without testing locally
Notes & Context

User hired Claude specifically for this project
Emphasis on GUI/visual tools due to limited coding skills
Need for clear documentation and step-by-step guidance
Solo project - no team dependencies
Open to learning but wants efficient implementation
Values owning the stack (no vendor lock-in)
Budget-conscious but willing to invest in right solution
Critical: Starting fresh to avoid technical debt


Last Updated: October 1, 2025
Next Review: After initial Codespace setup
Status: Ready to begin Discovery Phase