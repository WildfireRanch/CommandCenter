#!/bin/bash
# Railway Streamlit Startup Script
# Handles PORT environment variable properly

# Debug: Show what Railway gave us
echo "=== RAILWAY ENVIRONMENT DEBUG ==="
echo "PORT from Railway: ${PORT}"
echo "STREAMLIT_SERVER_PORT from Railway: ${STREAMLIT_SERVER_PORT}"

# Determine the actual port to use
if [ -z "$PORT" ]; then
  ACTUAL_PORT=8501
  echo "WARNING: PORT not set by Railway, using default 8501"
else
  ACTUAL_PORT=$PORT
  echo "Using Railway PORT: $ACTUAL_PORT"
fi

# CRITICAL: Override STREAMLIT_SERVER_PORT with actual numeric value
# This must be done BEFORE streamlit reads it
export STREAMLIT_SERVER_PORT=$ACTUAL_PORT

echo "=== FINAL CONFIGURATION ==="
echo "ACTUAL_PORT: $ACTUAL_PORT"
echo "STREAMLIT_SERVER_PORT: $STREAMLIT_SERVER_PORT"
echo "================================"

# Start Streamlit - it will now use the correct STREAMLIT_SERVER_PORT
streamlit run app/app.py \
  --server.address=0.0.0.0 \
  --server.headless=true \
  --server.fileWatcherType=none \
  --browser.gatherUsageStats=false \
  --client.toolbarMode=minimal \
  --server.enableXsrfProtection=false \
  --server.enableCORS=false
