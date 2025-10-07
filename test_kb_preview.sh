#!/bin/bash
# Quick test of KB preview endpoint (without auth)

echo "Testing KB API health..."
curl -s https://api.wildfireranch.us/health | jq .

echo -e "\n\nTesting KB stats..."
curl -s https://api.wildfireranch.us/kb/stats | jq .

echo -e "\n\nTesting KB documents list..."
curl -s https://api.wildfireranch.us/kb/documents | jq '.count'

echo -e "\n\nTesting KB sync status..."
curl -s https://api.wildfireranch.us/kb/sync-status | jq '.latest.status'
