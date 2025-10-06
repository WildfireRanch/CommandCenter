#!/bin/bash
# CrewAI Studio Deployment Status Checker
# Run this to check if Studio is ready for testing

echo "========================================="
echo "CrewAI Studio - Deployment Status Check"
echo "========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check 1: Health Endpoint
echo "1. Checking Studio health endpoint..."
HEALTH=$(curl -s https://studio.wildfireranch.us/_stcore/health 2>&1)
if [ "$HEALTH" = "ok" ]; then
    echo -e "   ${GREEN}✅ Health check: OK${NC}"
else
    echo -e "   ${RED}❌ Health check: FAILED${NC}"
    echo "   Response: $HEALTH"
fi
echo ""

# Check 2: Main Page
echo "2. Checking Studio main page..."
PAGE_TITLE=$(curl -s https://studio.wildfireranch.us/ | grep -o '<title>[^<]*</title>' | sed 's/<[^>]*>//g')
if [ ! -z "$PAGE_TITLE" ]; then
    echo -e "   ${GREEN}✅ Page serving: $PAGE_TITLE${NC}"
else
    echo -e "   ${RED}❌ Page not loading${NC}"
fi
echo ""

# Check 3: HTTP Status
echo "3. Checking HTTP status..."
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://studio.wildfireranch.us/)
if [ "$HTTP_STATUS" = "200" ]; then
    echo -e "   ${GREEN}✅ HTTP Status: 200 OK${NC}"
else
    echo -e "   ${YELLOW}⚠️  HTTP Status: $HTTP_STATUS${NC}"
fi
echo ""

# Check 4: Railway Service Status
echo "4. Checking Railway service status..."
RAILWAY_STATUS=$(railway status 2>&1 | grep -E "Project|Environment|Service")
if [ ! -z "$RAILWAY_STATUS" ]; then
    echo -e "   ${GREEN}✅ Railway CLI connected${NC}"
    echo "$RAILWAY_STATUS" | sed 's/^/   /'
else
    echo -e "   ${YELLOW}⚠️  Railway CLI not available${NC}"
fi
echo ""

# Check 5: Database Connectivity (from Railway)
echo "5. Checking database configuration..."
DB_VAR=$(railway variables --service CommandCenter 2>&1 | grep "DATABASE_URL" | head -1)
if [ ! -z "$DB_VAR" ]; then
    echo -e "   ${GREEN}✅ DATABASE_URL configured${NC}"
else
    echo -e "   ${RED}❌ DATABASE_URL not found${NC}"
fi
echo ""

# Summary
echo "========================================="
echo "Summary:"
echo "========================================="

if [ "$HEALTH" = "ok" ] && [ "$HTTP_STATUS" = "200" ]; then
    echo -e "${GREEN}✅ Studio appears to be deployed and running!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Open https://studio.wildfireranch.us in browser"
    echo "2. Press Ctrl+Shift+R for hard refresh"
    echo "3. You should see CrewAI Studio interface"
    echo "4. If you see blank page, check browser console (F12)"
    echo ""
    echo "Ready for testing!"
else
    echo -e "${YELLOW}⚠️  Studio may still be deploying...${NC}"
    echo ""
    echo "Check deployment logs:"
    echo "  railway logs --service CommandCenter"
    echo ""
    echo "Or visit Railway dashboard:"
    echo "  https://railway.com/project/c4d59bc8-c761-4bdc-8a74-844227083c5c"
fi

echo ""
echo "========================================="
