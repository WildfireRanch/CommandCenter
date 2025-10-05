#!/bin/bash
# Railway Streamlit Startup Script
# Handles PORT environment variable properly

# Use Railway's PORT or default to 8501
PORT=${PORT:-8501}

echo "Starting Streamlit on port $PORT..."

# Start Streamlit with the port
streamlit run app/app.py \
  --server.address=0.0.0.0 \
  --server.port=$PORT \
  --server.headless=true \
  --server.fileWatcherType=none \
  --browser.gatherUsageStats=false \
  --client.toolbarMode=minimal \
  --server.enableXsrfProtection=false \
  --server.enableCORS=false
