#!/bin/bash
# Railway Streamlit Startup Script
# Handles PORT environment variable properly

# Use Railway's PORT or default to 8501
export PORT=${PORT:-8501}
export STREAMLIT_SERVER_PORT=$PORT

echo "Starting Streamlit on port $PORT..."

# Start Streamlit with the port
streamlit run app/app.py \
  --server.address=0.0.0.0 \
  --server.headless=true \
  --server.fileWatcherType=none \
  --browser.gatherUsageStats=false \
  --client.toolbarMode=minimal \
  --server.enableXsrfProtection=false \
  --server.enableCORS=false
