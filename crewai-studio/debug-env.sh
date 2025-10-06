#!/bin/bash
# Debug script to see all environment variables

echo "=========================================="
echo "ENVIRONMENT VARIABLE DIAGNOSTIC"
echo "=========================================="
echo ""
echo "All environment variables:"
env | sort
echo ""
echo "=========================================="
echo "PORT-related variables:"
env | grep -i port
echo ""
echo "=========================================="
echo "STREAMLIT-related variables:"
env | grep -i streamlit
echo ""
echo "=========================================="
