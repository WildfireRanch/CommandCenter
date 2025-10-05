#!/bin/bash
# CommandCenter Health Check Script
# Tests all services and reports status

set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
API_URL="${API_URL:-https://api.wildfireranch.us}"
FRONTEND_URL="${FRONTEND_URL:-http://localhost:3001}"
STUDIO_URL="${STUDIO_URL:-http://localhost:8501}"

echo -e "${BLUE}🔍 CommandCenter Health Check${NC}"
echo -e "${BLUE}================================${NC}\n"

# Function to check HTTP status
check_http() {
    local url=$1
    local name=$2
    local expected=${3:-200}

    echo -n "Checking $name... "

    status=$(curl -s -o /dev/null -w "%{http_code}" "$url" || echo "000")

    if [ "$status" = "$expected" ]; then
        echo -e "${GREEN}✓ OK${NC} (HTTP $status)"
        return 0
    else
        echo -e "${RED}✗ FAILED${NC} (HTTP $status)"
        return 1
    fi
}

# Function to check JSON endpoint
check_json() {
    local url=$1
    local name=$2
    local field=$3
    local expected=$4

    echo -n "Checking $name... "

    response=$(curl -s "$url")
    value=$(echo "$response" | jq -r ".$field" 2>/dev/null || echo "error")

    if [ "$value" = "$expected" ]; then
        echo -e "${GREEN}✓ OK${NC} ($field: $value)"
        return 0
    else
        echo -e "${RED}✗ FAILED${NC} ($field: $value)"
        echo "Response: $response"
        return 1
    fi
}

# Track failures
FAILURES=0

echo -e "${YELLOW}1. Frontend (Next.js)${NC}"
check_http "$FRONTEND_URL" "Home Page" 200 || ((FAILURES++))
check_http "$FRONTEND_URL/dashboard" "Dashboard" 200 || ((FAILURES++))
check_http "$FRONTEND_URL/chat" "Chat" 200 || ((FAILURES++))
check_http "$FRONTEND_URL/studio" "Operator Studio" 200 || ((FAILURES++))
check_http "$FRONTEND_URL/energy" "Energy" 200 || ((FAILURES++))
check_http "$FRONTEND_URL/logs" "Logs" 200 || ((FAILURES++))
check_http "$FRONTEND_URL/status" "Status" 200 || ((FAILURES++))
echo ""

echo -e "${YELLOW}2. Backend API${NC}"
check_http "$API_URL/health" "API Health" 200 || ((FAILURES++))
check_json "$API_URL/health" "API Status" "status" "healthy" || ((FAILURES++))
check_http "$API_URL/energy/latest" "Latest Energy" 200 || ((FAILURES++))
check_http "$API_URL/docs" "API Docs" 200 || ((FAILURES++))
echo ""

echo -e "${YELLOW}3. CrewAI Studio${NC}"
check_http "$STUDIO_URL" "Studio Home" 200 || ((FAILURES++))
echo ""

echo -e "${YELLOW}4. Database${NC}"
check_json "$API_URL/health" "Database" "checks.database_connected" "true" || ((FAILURES++))
echo ""

# Summary
echo -e "${BLUE}================================${NC}"
if [ $FAILURES -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed!${NC}"
    exit 0
else
    echo -e "${RED}✗ $FAILURES check(s) failed${NC}"
    exit 1
fi
