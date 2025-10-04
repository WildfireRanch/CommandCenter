# ═══════════════════════════════════════════════════════════════════════════
# FILE: railway/Dockerfile
# PURPOSE: Docker container configuration for Railway deployment
#
# WHAT IT DOES:
#   - Sets up Python 3.11 environment
#   - Installs dependencies from requirements.txt
#   - Copies application code
#   - Runs FastAPI with uvicorn
#
# RAILWAY CONFIGURATION:
#   This Dockerfile works with railway.json settings
#   Railway will automatically detect and use this file
#
# LOCAL TESTING:
#   docker build -t commandcenter-api .
#   docker run -p 8000:8000 -e PORT=8000 commandcenter-api
# ═══════════════════════════════════════════════════════════════════════════

# Use Python 3.11 slim image (smaller, faster)
FROM python:3.11-slim

# Set working directory inside container
WORKDIR /app

# Copy requirements first (Docker layer caching optimization)
# If requirements.txt doesn't change, this layer is cached
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port (Railway assigns PORT via environment variable)
EXPOSE 8000

# Run the application
# Railway sets $PORT automatically
# Using shell form (without brackets) allows environment variable expansion
CMD uvicorn src.api.main:app --host 0.0.0.0 --port $PORT