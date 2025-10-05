#!/bin/bash
# Deployment Status Check

echo "🔍 CommandCenter Deployment Status"
echo "===================================="
echo ""

# Check local services
echo "📍 LOCAL SERVICES:"
echo ""
echo "Next.js Frontend:"
curl -s -o /dev/null -w "  Status: %{http_code}\n" http://localhost:3001/ || echo "  Status: NOT RUNNING"

echo "CrewAI Studio:"
curl -s -o /dev/null -w "  Status: %{http_code}\n" http://localhost:8501/ || echo "  Status: NOT RUNNING"

echo "Streamlit Ops:"
curl -s -o /dev/null -w "  Status: %{http_code}\n" http://localhost:8502/ || echo "  Status: NOT RUNNING"

echo ""
echo "🌐 PRODUCTION SERVICES:"
echo ""

echo "FastAPI Backend:"
curl -s https://api.wildfireranch.us/health | jq -r '"  Status: \(.status)"' 2>/dev/null || echo "  Status: ERROR"

echo ""
echo "📋 CONFIGURATION:"
echo ""

echo "Local .env.local:"
if [ -f /workspaces/CommandCenter/vercel/.env.local ]; then
    grep "NEXT_PUBLIC" /workspaces/CommandCenter/vercel/.env.local | sed 's/=.*/=***/' || echo "  No NEXT_PUBLIC vars"
else
    echo "  FILE NOT FOUND"
fi

echo ""
echo "💡 NEXT STEPS:"
echo ""
echo "1. Check your Vercel deployment URL"
echo "   - Visit: https://vercel.com/dashboard"
echo "   - Find your CommandCenter project"
echo "   - Copy the production URL"
echo ""
echo "2. If you deployed CrewAI Studio to Railway:"
echo "   - Go to: https://railway.app/dashboard"
echo "   - Find your CrewAI Studio service"
echo "   - Copy the Railway URL"
echo ""
echo "3. Add to Vercel Environment Variables:"
echo "   NEXT_PUBLIC_STUDIO_URL=<your-railway-url>"
echo ""
echo "4. Redeploy on Vercel"
echo ""
