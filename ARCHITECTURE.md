# 🏗️ CommandCenter Architecture

## System Overview

CommandCenter is a full-stack solar energy management and AI agent system with multiple integrated services.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          COMMANDCENTER SYSTEM                            │
└─────────────────────────────────────────────────────────────────────────┘

┌──────────────────────┐
│   USER INTERFACES    │
└──────────────────────┘
         │
         │
    ┌────▼────────────────────────────────────────────────────────┐
    │                                                              │
    │  VERCEL (Next.js 14 Frontend)                              │
    │  ┌──────────┬──────────┬─────────┬──────────┬──────────┐   │
    │  │ Home     │Dashboard │ Chat    │ Operator │ Energy   │   │
    │  │          │          │         │ Studio   │          │   │
    │  └──────────┴──────────┴─────────┴──────────┴──────────┘   │
    │         │                                           │        │
    └─────────┼───────────────────────────────────────────┼────────┘
              │                                           │
              │ HTTPS                                     │ iframe
              │                                           │
    ┌─────────▼───────────────────────────────────────────▼────────┐
    │                                                              │
    │  RAILWAY PLATFORM                                           │
    │                                                              │
    │  ┌──────────────────────────────────────────────────────┐   │
    │  │                                                       │   │
    │  │  FastAPI Backend (api.wildfireranch.us)              │   │
    │  │  ┌─────────────────────────────────────────────┐     │   │
    │  │  │ Endpoints:                                  │     │   │
    │  │  │  • /health          - System health         │     │   │
    │  │  │  • /energy/*        - Energy data & stats   │     │   │
    │  │  │  • /agent/*         - AI agent interaction  │     │   │
    │  │  │  • /conversations/* - Chat history          │     │   │
    │  │  │  • /system/*        - System stats          │     │   │
    │  │  └─────────────────────────────────────────────┘     │   │
    │  │                          │                            │   │
    │  └──────────────────────────┼────────────────────────────┘   │
    │                             │                                │
    │  ┌──────────────────────────▼────────────────────────────┐   │
    │  │                                                       │   │
    │  │  PostgreSQL + TimescaleDB                            │   │
    │  │  ┌─────────────────────────────────────────────┐     │   │
    │  │  │ Tables:                                     │     │   │
    │  │  │  • energy_snapshots (TimescaleDB hypertable)│     │   │
    │  │  │  • conversations                            │     │   │
    │  │  │  • messages                                 │     │   │
    │  │  │  • agent_executions                         │     │   │
    │  │  │  • crewai_* (CrewAI Studio tables)          │     │   │
    │  │  └─────────────────────────────────────────────┘     │   │
    │  │                                                       │   │
    │  └───────────────────────────────────────────────────────┘   │
    │                                                              │
    │  ┌───────────────────────────────────────────────────────┐   │
    │  │                                                       │   │
    │  │  CrewAI Studio (Streamlit)                           │   │
    │  │  ┌─────────────────────────────────────────────┐     │   │
    │  │  │ Features:                                   │     │   │
    │  │  │  • Agent management (no-code)               │     │   │
    │  │  │  • Crew configuration                       │     │   │
    │  │  │  • Task workflows                           │     │   │
    │  │  │  • Knowledge sources                        │     │   │
    │  │  │  • Custom tools                             │     │   │
    │  │  │  • Multi-LLM support                        │     │   │
    │  │  └─────────────────────────────────────────────┘     │   │
    │  │                          │                            │   │
    │  └──────────────────────────┼────────────────────────────┘   │
    │                             │                                │
    └─────────────────────────────┼────────────────────────────────┘
                                  │
                                  │ Shared DB
                                  │
                       ┌──────────▼──────────┐
                       │                     │
                       │  LOCAL SERVICES     │
                       │                     │
                       │  ┌───────────────┐  │
                       │  │ MCP Server    │  │
                       │  │ (Port 8080)   │  │
                       │  │               │  │
                       │  │ Claude Tools: │  │
                       │  │ • energy_data │  │
                       │  │ • ask_agent   │  │
                       │  │ • solar_stats │  │
                       │  └───────────────┘  │
                       │                     │
                       │  ┌───────────────┐  │
                       │  │ Streamlit Ops │  │
                       │  │ (Port 8502)   │  │
                       │  │               │  │
                       │  │ Admin Pages:  │  │
                       │  │ • Monitor     │  │
                       │  │ • Chat        │  │
                       │  │ • Logs        │  │
                       │  └───────────────┘  │
                       └─────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                      DATA SOURCES                                │
└─────────────────────────────────────────────────────────────────┘
                                  │
                       ┌──────────▼──────────┐
                       │                     │
                       │  SolArk Inverter    │
                       │  (API Integration)  │
                       │                     │
                       │  • Battery SOC      │
                       │  • Solar Power      │
                       │  • Load Power       │
                       │  • Grid Power       │
                       └─────────────────────┘
```

## Service Communication

### 1. **Frontend → API**
- Protocol: HTTPS
- Format: JSON
- Endpoints: RESTful API
- Auth: None (internal network)

### 2. **API → Database**
- Protocol: PostgreSQL wire protocol
- Connection: Railway internal network
- Features: TimescaleDB for time-series data

### 3. **Frontend → CrewAI Studio**
- Protocol: HTTPS (iframe embed)
- Method: Direct embedding with query params
- CORS: Disabled for embedding
- Features: Streamlit embed options

### 4. **MCP Server → API**
- Protocol: HTTP
- Port: 8080 → Railway API
- Purpose: Claude Desktop integration
- Tools: Energy data, agent interaction

## Technology Stack

### Frontend (Vercel)
- **Framework**: Next.js 14 (App Router)
- **UI**: React 18 + TypeScript
- **Styling**: Tailwind CSS
- **Charts**: Recharts
- **Icons**: Lucide React
- **Deployment**: Vercel (auto-deploy from GitHub)

### Backend (Railway)
- **API**: FastAPI (Python 3.12)
- **Database**: PostgreSQL 16 + TimescaleDB
- **ORM**: SQLAlchemy
- **Agent**: CrewAI + LangChain
- **LLM**: OpenAI GPT-4
- **ASGI**: Uvicorn

### CrewAI Studio (Railway)
- **Framework**: Streamlit
- **Database**: Shared PostgreSQL (SQLite fallback)
- **Features**: No-code agent builder
- **LLM Support**: OpenAI, Anthropic, Ollama, Groq

### Operations Dashboard (Local)
- **Framework**: Streamlit
- **Port**: 8502
- **Purpose**: Admin monitoring
- **Features**: Energy monitor, agent chat, logs

### MCP Server (Local)
- **Protocol**: Model Context Protocol
- **Port**: 8080
- **Client**: Claude Desktop
- **Tools**: Energy, agent, solar stats

## Data Flow

### 1. **Energy Data Collection**
```
SolArk API → FastAPI (/energy/collect) → PostgreSQL (energy_snapshots)
                                              ↓
                                         TimescaleDB
                                         (time-series)
```

### 2. **User Queries Energy**
```
User → Next.js → FastAPI (/energy/latest) → PostgreSQL → Response
                                                  ↓
                                            JSON + Charts
```

### 3. **Agent Conversation**
```
User → Next.js (/chat) → FastAPI (/agent/ask) → CrewAI Agent → OpenAI
                              ↓                        ↓
                         PostgreSQL              Energy Tools
                         (messages)              (fetch data)
                              ↓                        ↓
                         Response ← ← ← ← ← ← ← ← Response
```

### 4. **CrewAI Studio Workflow**
```
User → Next.js (/studio) → iframe → CrewAI Studio (Streamlit)
                                            ↓
                                    Agent/Crew Config
                                            ↓
                                    PostgreSQL (crewai_*)
                                            ↓
                                    Execute Crew → LLM
```

## Deployment Environments

### Production
- **Frontend**: Vercel (global CDN)
- **Backend**: Railway (US region)
- **Database**: Railway PostgreSQL
- **Studio**: Railway (to be deployed)

### Development
- **Frontend**: localhost:3001
- **Backend**: localhost:8000
- **Database**: Railway (shared)
- **Studio**: localhost:8501
- **Ops Dashboard**: localhost:8502
- **MCP Server**: localhost:8080

## Security Considerations

1. **API Keys**: Environment variables only, never committed
2. **Database**: Railway internal network, not public
3. **CORS**: Disabled for Streamlit embedding
4. **HTTPS**: All external communication encrypted
5. **Auth**: To be implemented (OAuth/JWT)

## Scaling Strategy

1. **Frontend**: Auto-scaled by Vercel
2. **API**: Railway horizontal scaling
3. **Database**: Vertical scaling, read replicas
4. **Studio**: Railway auto-scaling

## Monitoring

1. **Health Checks**: `/health` endpoint
2. **Metrics**: Railway dashboard
3. **Logs**: Railway logs + Vercel logs
4. **Alerts**: To be configured
5. **Uptime**: External monitoring service

## Future Enhancements

- [ ] Authentication (Auth0/Clerk)
- [ ] WebSocket for real-time updates
- [ ] Redis caching layer
- [ ] Grafana dashboards
- [ ] Automated testing (Pytest, Jest)
- [ ] CI/CD pipelines
- [ ] Mobile app (React Native)
- [ ] Multi-tenant support

---

*Last Updated: 2025-10-05*
*Version: 1.0*
