# Railway Deployment Optimization Guide

**Issue:** CrewAI Studio deployments taking 20-30 minutes
**Date:** October 6, 2025
**Status:** In Progress

---

## Current Deployment Timeline

**Observed Steps:**
1. ✅ Indexing code (1-2 min)
2. ✅ Uploading code (1-2 min)
3. 🐌 **Sharing credentials for production-us-west2.railway-registry.com** (5-10 min) ← SLOW
4. 🐌 **Building Docker image** (10-15 min) ← SLOW
   - Installing Python packages
   - Compiling C extensions (docling, snowflake-connector-python)
5. ⏳ Pushing to registry (2-3 min)
6. ⏳ Deploying container (1-2 min)

**Total: 20-30 minutes per deployment**

---

## Root Causes of Slow Builds

### 1. Heavy Dependencies in requirements.txt

**Problem packages:**
- **`docling`** - PDF processing library with heavy ML dependencies (10+ min)
- **`snowflake-connector-python`** - Large database connector (5-10 min)
- **`crewai`** + full `langchain` suite - Many dependencies
- **Multiple LLM providers** - langchain-openai, langchain-groq, langchain-anthropic, langchain-ollama

**Combined size:** 500+ MB of dependencies

### 2. Railway Registry Authentication

**Step:** "Sharing credentials for production-us-west2.railway-registry.com"
**Duration:** 5-10 minutes
**Cause:** Railway's internal process, network latency

### 3. No Build Caching

**Issue:** Every deployment rebuilds from scratch
**Impact:** No benefit from previous builds

---

## Optimization Strategies

### Strategy 1: Remove Unused Dependencies (Immediate Impact)

**Review requirements.txt and remove what's not needed:**

```diff
# /workspaces/CommandCenter/crewai-studio/requirements.txt

 crewai
 crewai-tools
 langchain
 langchain-community
 langchain-openai
-langchain-groq
-langchain-anthropic
-langchain-ollama
 streamlit
 python-dotenv
-pdfminer.six
 sqlalchemy
 psycopg2-binary
-snowflake-connector-python
 markdown
-docling
 duckduckgo-search>=8.0.2
 embedchain>=0.1.100
```

**Removals:**
- ❌ **`docling`** - Only needed if processing PDFs (not in current use)
- ❌ **`snowflake-connector-python`** - Not using Snowflake database
- ❌ **`pdfminer.six`** - Redundant with embedchain
- ❌ **`langchain-groq`** - Remove if not using Groq LLM
- ❌ **`langchain-anthropic`** - Remove if only using OpenAI
- ❌ **`langchain-ollama`** - Remove if not using local models

**Expected savings:** 10-15 minutes per build

### Strategy 2: Pin Specific Versions (Stability)

```diff
# Currently: unpinned (gets latest every time)
-crewai
-crewai-tools
-langchain

# Recommended: pin to tested versions
+crewai==0.86.0
+crewai-tools==0.17.0
+langchain==0.3.13
+langchain-community==0.3.13
+langchain-openai==0.2.13
```

**Benefits:**
- Faster dependency resolution
- Consistent builds
- No surprise breaking changes

### Strategy 3: Use Railway Build Cache

**Add to railway.json:**

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "Dockerfile",
    "buildCommand": null,
    "watchPatterns": ["crewai-studio/**"]
  },
  "deploy": {
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 3,
    "numReplicas": 1
  }
}
```

**`watchPatterns`:** Only rebuild when crewai-studio files change

### Strategy 4: Optimize Dockerfile Layers

**Current Dockerfile:**
```dockerfile
COPY ./crewai-studio/requirements.txt .
RUN pip install -r requirements.txt
COPY ./crewai-studio .
```

**Problem:** Any code change invalidates requirements install

**Optimized Dockerfile:**
```dockerfile
# Stage 1: Dependencies (cached)
FROM python:3.12.10-slim-bookworm AS dependencies
WORKDIR /CrewAI-Studio
COPY ./crewai-studio/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Application (changes frequently)
FROM dependencies
COPY ./crewai-studio .
RUN chmod +x start.sh
EXPOSE 8080
CMD ["/bin/bash", "./start.sh"]
```

**Benefits:**
- Dependency layer cached
- Only rebuilds when requirements.txt changes
- Code changes don't trigger full rebuild

### Strategy 5: Pre-built Docker Image (Advanced)

**Concept:** Build image locally/CI, push to Docker Hub, Railway pulls

**Steps:**
1. Build image locally: `docker build -t username/crewai-studio:latest .`
2. Push to Docker Hub: `docker push username/crewai-studio:latest`
3. Update Railway to use image instead of building

**Benefits:**
- Build once, deploy many times
- Control build environment
- Faster Railway deployments (just pull image)

**Trade-offs:**
- More complex workflow
- Need Docker Hub account
- Manual build process

---

## Recommended Action Plan

### Phase 1: Quick Wins (Do Now)

1. **Remove unused dependencies** from requirements.txt
   - Remove: docling, snowflake-connector-python, pdfminer.six
   - Remove unused langchain providers
   - **Expected savings:** 10-15 minutes

2. **Pin versions** for stability
   - Add specific version numbers
   - **Expected savings:** 2-3 minutes

**Total savings: 12-18 minutes** (build time: 10-15 min instead of 25-30 min)

### Phase 2: Docker Optimization (Next Session)

1. **Optimize Dockerfile** with multi-stage build
   - **Expected savings:** 5-10 minutes on subsequent builds

2. **Add .dockerignore**
   - Exclude unnecessary files from build context
   - **Expected savings:** 1-2 minutes

### Phase 3: Advanced (Future)

1. **Pre-built images** on Docker Hub
   - Build in GitHub Actions
   - Railway pulls instead of builds
   - **Expected savings:** 15-20 minutes

---

## Implementation: Phase 1 (Quick Wins)

### Step 1: Update requirements.txt

**Create minimal requirements.txt:**

```txt
# Core CrewAI
crewai==0.86.0
crewai-tools==0.17.0

# LangChain (only what we need)
langchain==0.3.13
langchain-community==0.3.13
langchain-openai==0.2.13

# Web Interface
streamlit==1.50.0

# Database
sqlalchemy==2.0.36
psycopg2-binary==2.9.10

# Utilities
python-dotenv==1.0.1
markdown==3.7

# Tools
duckduckgo-search>=8.0.2
embedchain>=0.1.100
```

### Step 2: Test Locally

```bash
cd /workspaces/CommandCenter/crewai-studio
pip install -r requirements.txt
streamlit run app/app.py --server.port 8501
```

### Step 3: Commit and Deploy

```bash
git add crewai-studio/requirements.txt
git commit -m "Optimize requirements.txt for faster Railway builds

Remove unused dependencies:
- docling (PDF processing not needed)
- snowflake-connector-python (not using Snowflake)
- pdfminer.six (redundant)
- langchain-groq, langchain-anthropic, langchain-ollama (using OpenAI only)

Pin versions for stability and faster resolution

Expected improvement: 12-18 minute reduction in build time"

git push
```

Railway will auto-deploy (or trigger manually)

### Step 4: Monitor Improvement

**Watch build logs:**
- Should skip heavy packages
- Fewer compilation steps
- Faster overall build

**Expected new timeline:**
1. Indexing/uploading: 2-3 min
2. Registry auth: 5-10 min (can't optimize this easily)
3. Building: 3-5 min (down from 15 min)
4. Deploying: 2-3 min

**New total: 12-18 minutes** (vs 25-30 currently)

---

## Monitoring Build Performance

### Key Metrics to Track

**Before optimization:**
- Total build time: 25-30 min
- Dependencies install: ~15 min
- Docker build: ~10 min

**After Phase 1:**
- Total build time: 12-18 min ⬇️ 40% reduction
- Dependencies install: ~3-5 min ⬇️ 60% reduction
- Docker build: ~7-10 min (registry auth dominates)

**After Phase 2:**
- Total build time: 8-12 min ⬇️ 60% reduction
- Cached builds: ~5 min ⬇️ 80% reduction

---

## Alternative: Use Railway's Native Python Builder

**Instead of Dockerfile, try Railway's native builder:**

### railway.toml (Alternative Configuration)

```toml
[build]
builder = "NIXPACKS"
buildCommand = "pip install -r crewai-studio/requirements.txt"

[deploy]
startCommand = "streamlit run crewai-studio/app/app.py --server.port $PORT --server.headless true"
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 3
```

**Benefits:**
- Railway optimizes Python builds
- Better caching built-in
- Simpler configuration

**Trade-offs:**
- Less control over environment
- Might not work with all dependencies

---

## Railway Pro Tips

### 1. Deploy During Off-Peak Hours

Registry authentication is faster when Railway has less traffic

**Best times:** Late night / early morning (US Pacific time)

### 2. Use GitHub Actions for Pre-checks

Build and test locally before pushing to Railway:

```yaml
# .github/workflows/test.yml
name: Test Before Deploy
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
      - run: pip install -r crewai-studio/requirements.txt
      - run: python -m pytest tests/
```

Only successful builds get deployed

### 3. Use Railway CLI for Local Testing

```bash
# Test exact Railway environment locally
railway run streamlit run app/app.py
```

Catches issues before deployment

---

## Long-term Solution: Monorepo Optimization

**Current structure:**
```
CommandCenter/
├── crewai-studio/      # Deployed to Railway (CrewAI project)
├── railway/            # API (CommandCenter project)
├── vercel/             # Frontend (Vercel)
└── Dockerfile          # At root (builds crewai-studio)
```

**Issue:** Dockerfile at root causes Railway to upload entire repo

**Optimization:**

### Option 1: Separate Repos (Maximum Speed)

```
crewai-studio/          # Standalone repo, Railway watches this
CommandCenter/          # Main repo, no Studio code
```

**Benefits:**
- Smallest possible upload
- No extraneous files
- Fastest deployments

### Option 2: Git Submodules

Keep monorepo but use submodules for isolation

### Option 3: .dockerignore (Easiest)

```
# .dockerignore
vercel/
railway/
docs/
old-stack/
.git/
*.md
```

Excludes unnecessary files from Docker build context

---

## Success Criteria

**Goal:** Reduce deployment time to under 15 minutes

**Metrics:**
- ✅ Phase 1: 12-18 min (40% improvement)
- ✅ Phase 2: 8-12 min (60% improvement)
- ✅ Phase 3: 5-8 min (80% improvement)

**Current status:** Implementing Phase 1

---

## Next Steps

1. **While current build finishes:** Wait for completion, test deployment
2. **After successful deploy:** Implement Phase 1 optimizations
3. **Next session:** Test faster deployment, implement Phase 2
4. **Future:** Consider Phase 3 if needed

---

**Status:** 🔄 In Progress - Current build running
**Expected completion:** ~20-30 minutes from start
**Next optimization:** Phase 1 (remove unused deps, pin versions)
**Estimated improvement:** 40-60% faster builds

---

**Last Updated:** October 6, 2025
**Session:** 015
