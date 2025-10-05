#!/bin/bash
# Integration Test Script
# Tests all API endpoints and data flow

set -e

API_URL="${API_URL:-https://api.wildfireranch.us}"

echo "🧪 Running Integration Tests..."
echo "API: $API_URL"
echo ""

# Test 1: Health Check
echo "Test 1: API Health Check"
health=$(curl -s "$API_URL/health")
status=$(echo "$health" | jq -r '.status')
if [ "$status" = "healthy" ]; then
    echo "✓ API is healthy"
else
    echo "✗ API health check failed"
    exit 1
fi
echo ""

# Test 2: Latest Energy Data
echo "Test 2: Latest Energy Data"
energy=$(curl -s "$API_URL/energy/latest")
soc=$(echo "$energy" | jq -r '.data.soc')
if [ "$soc" != "null" ]; then
    echo "✓ Energy data available (SOC: $soc%)"
else
    echo "✗ No energy data available"
    exit 1
fi
echo ""

# Test 3: Energy Stats
echo "Test 3: Historical Energy Stats"
stats=$(curl -s "$API_URL/energy/stats?hours=1")
count=$(echo "$stats" | jq -r '.data | length')
if [ "$count" -gt 0 ]; then
    echo "✓ Historical data available ($count records)"
else
    echo "✗ No historical data"
    exit 1
fi
echo ""

# Test 4: Agent Interaction
echo "Test 4: Agent Chat"
response=$(curl -s -X POST "$API_URL/agent/ask" \
    -H "Content-Type: application/json" \
    -d '{"message": "What is my battery level?", "session_id": "test-session"}')
reply=$(echo "$response" | jq -r '.response')
if [ "$reply" != "null" ] && [ "$reply" != "" ]; then
    echo "✓ Agent responded: ${reply:0:50}..."
else
    echo "✗ Agent did not respond"
    exit 1
fi
echo ""

# Test 5: Conversations
echo "Test 5: Recent Conversations"
convs=$(curl -s "$API_URL/conversations/recent?limit=5")
conv_count=$(echo "$convs" | jq -r '.conversations | length')
echo "✓ Found $conv_count recent conversations"
echo ""

# Test 6: System Stats
echo "Test 6: System Statistics"
sys_stats=$(curl -s "$API_URL/system/stats")
snapshots=$(echo "$sys_stats" | jq -r '.total_energy_snapshots')
if [ "$snapshots" != "null" ]; then
    echo "✓ System stats available (Snapshots: $snapshots)"
else
    echo "✗ No system stats"
    exit 1
fi
echo ""

echo "================================"
echo "✅ All integration tests passed!"
exit 0
