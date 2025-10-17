#!/bin/bash
# Quick V1.6 Validation Test Script
# Run this after deployment completes

echo "================================"
echo "V1.6 VALIDATION TESTS"
echo "================================"
echo ""

# Test 1: API Health
echo "TEST 1: API Health"
echo "-------------------"
curl -s https://api.wildfireranch.us/health | jq '.status' || echo "❌ API DOWN"
echo ""

# Test 2: System Knowledge (CRITICAL)
echo "TEST 2: System Knowledge (V1.6 - CRITICAL)"
echo "-------------------------------------------"
echo "Question: What inverter are you managing?"
RESPONSE=$(curl -s -X POST https://api.wildfireranch.us/ask \
  -H "Content-Type: application/json" \
  -d '{"message": "What inverter model are you managing?"}')

echo "$RESPONSE" | jq -r '.response' | head -5
echo ""
echo "Agent: $(echo "$RESPONSE" | jq -r '.agent_role')"
echo "Duration: $(echo "$RESPONSE" | jq -r '.duration_ms')ms"
echo ""

if echo "$RESPONSE" | jq -r '.response' | grep -qi "solark\|15k"; then
    echo "✅ PASS: Agent knows SolArk"
else
    echo "❌ FAIL: Agent doesn't know specific hardware"
fi
echo ""

# Test 3: Policy Knowledge (CRITICAL)
echo "TEST 3: Policy Knowledge (V1.6 - CRITICAL)"
echo "-------------------------------------------"
echo "Question: What is the critical minimum battery SOC?"
RESPONSE=$(curl -s -X POST https://api.wildfireranch.us/ask \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the critical minimum battery SOC?"}')

echo "$RESPONSE" | jq -r '.response' | head -3
echo ""
echo "Agent: $(echo "$RESPONSE" | jq -r '.agent_role')"
echo ""

if echo "$RESPONSE" | jq -r '.response' | grep -q "30"; then
    echo "✅ PASS: Agent knows 30% policy"
else
    echo "❌ FAIL: Agent doesn't know policy"
fi
echo ""

# Test 4: Multi-Turn Context (CRITICAL)
echo "TEST 4: Multi-Turn Context (V1.6 - CRITICAL)"
echo "---------------------------------------------"
echo "Turn 1: What is my battery level?"
RESPONSE1=$(curl -s -X POST https://api.wildfireranch.us/ask \
  -H "Content-Type: application/json" \
  -d '{"message": "What is my battery level?"}')

SID=$(echo "$RESPONSE1" | jq -r '.session_id')
echo "Session ID: $SID"
echo "Response: $(echo "$RESPONSE1" | jq -r '.response' | head -2)"
echo ""

echo "Turn 2: Is that safe?"
RESPONSE2=$(curl -s -X POST https://api.wildfireranch.us/ask \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"Is that safe?\", \"session_id\": \"$SID\"}")

echo "Response: $(echo "$RESPONSE2" | jq -r '.response' | head -3)"
echo ""

if echo "$RESPONSE2" | jq -r '.response' | grep -qi "battery\|level\|soc\|%"; then
    echo "✅ PASS: Context preserved across turns"
else
    echo "❌ FAIL: Context lost"
fi
echo ""

echo "================================"
echo "VALIDATION COMPLETE"
echo "================================"
echo ""
echo "Next steps:"
echo "1. If all 3 tests PASS: V1.6 is working! Run full test suite"
echo "2. If any tests FAIL: Check V1.6_COMPLETION_PLAN.md for troubleshooting"
echo "3. Review SESSION_SUMMARY.md for complete status"
