#!/bin/bash
# Railway Streamlit Startup Script
# Handles PORT environment variable properly

# Debug: Show what we're getting
echo "DEBUG: PORT variable is: ${PORT}"
echo "DEBUG: STREAMLIT_SERVER_PORT variable is: ${STREAMLIT_SERVER_PORT}"

# If STREAMLIT_SERVER_PORT contains literal '$PORT', unset it
if [[ "$STREAMLIT_SERVER_PORT" == *'$PORT'* ]]; then
  echo "WARNING: Unsetting STREAMLIT_SERVER_PORT (contains literal \$PORT)"
  unset STREAMLIT_SERVER_PORT
fi

# Use Railway's PORT or default to 8501
export PORT=${PORT:-8501}

echo "Starting Streamlit on port $PORT..."

# Start Streamlit with explicit port argument (bypasses env var issues)
exec streamlit run app/app.py \
  --server.address=0.0.0.0 \
  --server.port="$PORT" \
  --server.headless=true \
  --server.fileWatcherType=none \
  --browser.gatherUsageStats=false \
  --client.toolbarMode=minimal \
  --server.enableXsrfProtection=false \
  --server.enableCORS=false
