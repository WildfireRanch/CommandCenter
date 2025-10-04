\# CommandCenter Code Style Guide

\#\# File Header Template

Every code file should start with this:

\`\`\`python  
\# ═══════════════════════════════════════════════════════════════════════════  
\# FILE: railway/src/api/main.py  
\# PURPOSE: FastAPI application entrypoint for CommandCenter backend  
\#   
\# WHAT IT DOES:  
\#   \- Starts the API server  
\#   \- Configures CORS for Vercel  
\#   \- Sets up health endpoints  
\#   \- Loads all route modules  
\#  
\# DEPENDENCIES:  
\#   \- FastAPI (web framework)  
\#   \- uvicorn (ASGI server)  
\#   \- python-dotenv (environment variables)  
\#  
\# ENVIRONMENT VARIABLES:  
\#   \- ALLOWED\_ORIGINS: Comma-separated list of allowed CORS origins  
\#   \- OPENAI\_API\_KEY: OpenAI API key for CrewAI  
\#   \- DATABASE\_URL: PostgreSQL connection string  
\#  
\# RUNS ON:  
\#   \- Railway (production)  
\#   \- Local: uvicorn src.api.main:app \--reload  
\# ═══════════════════════════════════════════════════════════════════════════  
\`\`\`

\---

\#\# Section Headers

Use these to break up code into clear sections:

\`\`\`python  
\# ─────────────────────────────────────────────────────────────────────────────  
\# Configuration & Settings  
\# ─────────────────────────────────────────────────────────────────────────────

\# Code here...

\# ─────────────────────────────────────────────────────────────────────────────  
\# Helper Functions  
\# ─────────────────────────────────────────────────────────────────────────────

\# Code here...

\# ─────────────────────────────────────────────────────────────────────────────  
\# Main Application  
\# ─────────────────────────────────────────────────────────────────────────────

\# Code here...  
\`\`\`

\---

\#\# Function Comments

Every function should explain WHAT, WHY, and HOW:

\`\`\`python  
def parse\_cors\_origins(value: str | None) \-\> list\[str\]:  
    """  
    Parse CORS origins from environment variable.  
      
    WHAT: Converts comma/space-separated string into list of origins  
    WHY: We need to allow Vercel MCP server to call our API  
    HOW: Split by comma, strip whitespace, deduplicate  
      
    Args:  
        value: String like "https://app.com,https://api.com" or None  
          
    Returns:  
        List of unique origin URLs, e.g., \["https://app.com", "https://api.com"\]  
        Returns empty list if value is None or empty  
          
    Example:  
        \>\>\> parse\_cors\_origins("https://a.com, https://b.com")  
        \["https://a.com", "https://b.com"\]  
    """  
    if not value:  
        return \[\]  
      
    \# Split by comma first, then by spaces (handles various formats)  
    parts \= \[p.strip() for chunk in value.split(",") for p in chunk.split() if p.strip()\]  
      
    \# Remove duplicates while preserving order  
    return list(dict.fromkeys(parts))  
\`\`\`

\---

\#\# Inline Comments

Use inline comments for tricky code:

\`\`\`python  
\# BAD: No explanation  
response \= await call\_next(request)

\# GOOD: Explains why we're doing this  
\# Pass request through middleware chain and measure response time  
\# This lets us log how long each request takes  
response \= await call\_next(request)  
\`\`\`

\---

\#\# TODO Comments

Mark incomplete work clearly:

\`\`\`python  
\# TODO: Add database connection check  
\# Currently just returns "not\_checked" \- need to add actual DB ping  
\# Priority: Medium | Owner: \[your name\] | Issue: \#123  
checks \= {  
    "database": "not\_checked"  
}  
\`\`\`

\---

\#\# Error Handling Comments

Explain what errors you're catching and why:

\`\`\`python  
try:  
    result \= process\_data(input)  
except ValueError as e:  
    \# ValueError means input format is wrong \- log and return 400  
    \# This is a user error, not a system error  
    logger.warning("invalid\_input error=%s", e)  
    return {"error": "Invalid input format"}, 400  
except Exception as e:  
    \# Unexpected error \- log full traceback and return 500  
    \# This shouldn't happen \- investigate if it does  
    logger.exception("unexpected\_error error=%s", e)  
    return {"error": "Internal server error"}, 500  
\`\`\`

\---

\#\# Configuration Sections

Group related config with clear labels:

\`\`\`python  
\# ─────────────────────────────────────────────────────────────────────────────  
\# Environment Variables  
\# ─────────────────────────────────────────────────────────────────────────────

\# API Configuration  
API\_KEY \= os.getenv("API\_KEY")  \# Required for authentication  
ALLOWED\_ORIGINS \= os.getenv("ALLOWED\_ORIGINS", "")  \# CORS origins

\# OpenAI Configuration    
OPENAI\_API\_KEY \= os.getenv("OPENAI\_API\_KEY")  \# Required for CrewAI  
OPENAI\_MODEL \= os.getenv("OPENAI\_MODEL", "gpt-4o-mini")  \# Default model

\# Database Configuration  
DATABASE\_URL \= os.getenv("DATABASE\_URL")  \# Auto-provided by Railway  
DB\_POOL\_SIZE \= int(os.getenv("DB\_POOL\_SIZE", "10"))  \# Connection pool size  
\`\`\`

\---

\#\# File Organization

Structure files in this order:

\`\`\`python  
\# ═══════════════════════════════════════════════════════════════════════════  
\# FILE: \[path\]  
\# \[header info\]  
\# ═══════════════════════════════════════════════════════════════════════════

\# 1\. Imports (grouped: stdlib, third-party, local)  
import os  
from pathlib import Path

from fastapi import FastAPI  
from pydantic import BaseModel

from .config import settings

\# 2\. Constants & Configuration  
API\_VERSION \= "1.0.0"  
DEFAULT\_TIMEOUT \= 30

\# 3\. Helper Functions  
def helper\_one():  
    pass

\# 4\. Classes (if any)  
class MyClass:  
    pass

\# 5\. Main Logic  
def main():  
    pass

\# 6\. Script Entry Point (if applicable)  
if \_\_name\_\_ \== "\_\_main\_\_":  
    main()  
\`\`\`

\---

\#\# Quick Navigation Comments

Add these for quick jumping:

\`\`\`python  
\# ═══════════════════════════════════════════════════════════════════════════  
\# QUICK NAVIGATION:  
\#   \- Line 50: Configuration  
\#   \- Line 120: Middleware Setup  
\#   \- Line 200: Route Handlers  
\#   \- Line 350: Error Handlers  
\# ═══════════════════════════════════════════════════════════════════════════  
\`\`\`

\---

\#\# Troubleshooting Comments

Add common issues:

\`\`\`python  
def connect\_database():  
    """  
    Connect to PostgreSQL database.  
      
    TROUBLESHOOTING:  
        \- "Connection refused": Check DATABASE\_URL is set  
        \- "Permission denied": Check database user has access  
        \- "Too many connections": Increase DB\_POOL\_SIZE  
    """  
    pass  
\`\`\`

\---

\#\# Summary

\*\*Every file should have:\*\*  
1\. ✅ Clear file path at top  
2\. ✅ Purpose statement  
3\. ✅ Section headers  
4\. ✅ Function docstrings with WHAT/WHY/HOW  
5\. ✅ Inline comments for tricky parts  
6\. ✅ TODO markers for incomplete work  
7\. ✅ Troubleshooting hints

\*\*This makes it easy to:\*\*  
\- Find the right file quickly  
\- Navigate to the right section  
\- Understand what code does  
\- Debug when things break  
\- Patch specific features