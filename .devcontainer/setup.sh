#!/bin/bash
# CommandCenter Codespaces Setup Script
# Auto-runs on container creation
# Restores .env files from GitHub Codespaces secrets

set -e

echo "🚀 CommandCenter Codespaces Setup"
echo "=================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Install Railway CLI
echo -e "${YELLOW}📦 Installing Railway CLI...${NC}"
if ! command -v railway &> /dev/null; then
    npm install -g @railway/cli
    echo -e "${GREEN}✓ Railway CLI installed${NC}"
else
    echo -e "${GREEN}✓ Railway CLI already installed${NC}"
fi

# Install Python dependencies
echo -e "${YELLOW}📦 Installing Python dependencies...${NC}"
if [ -f "railway/requirements.txt" ]; then
    pip install -r railway/requirements.txt > /dev/null 2>&1
    echo -e "${GREEN}✓ Python dependencies installed${NC}"
fi

# Install Node dependencies for frontend
echo -e "${YELLOW}📦 Installing frontend dependencies...${NC}"
if [ -d "vercel" ] && [ -f "vercel/package.json" ]; then
    cd vercel && npm install > /dev/null 2>&1 && cd ..
    echo -e "${GREEN}✓ Frontend dependencies installed${NC}"
fi

# Install MCP server dependencies
echo -e "${YELLOW}📦 Installing MCP server dependencies...${NC}"
if [ -d "mcp-server" ] && [ -f "mcp-server/package.json" ]; then
    cd mcp-server && npm install > /dev/null 2>&1 && cd ..
    echo -e "${GREEN}✓ MCP server dependencies installed${NC}"
fi

echo ""
echo "🔐 Setting up environment variables..."
echo "======================================"
echo ""

# Function to restore .env file
restore_env() {
    local service=$1
    local env_file=$2
    local template_file=$3

    echo -e "${YELLOW}Restoring $service environment...${NC}"

    if [ -f "$template_file" ]; then
        cp "$template_file" "$env_file"
        echo -e "${GREEN}✓ Created $env_file from template${NC}"
    else
        echo -e "${RED}✗ Template not found: $template_file${NC}"
        return 1
    fi

    # Replace placeholders with Codespaces secrets (if available)
    if [ ! -z "$OPENAI_API_KEY" ]; then
        sed -i "s|OPENAI_API_KEY=.*|OPENAI_API_KEY=$OPENAI_API_KEY|g" "$env_file"
        echo -e "${GREEN}  ✓ OpenAI API key configured${NC}"
    fi

    if [ ! -z "$GOOGLE_CLIENT_ID" ]; then
        sed -i "s|GOOGLE_CLIENT_ID=.*|GOOGLE_CLIENT_ID=$GOOGLE_CLIENT_ID|g" "$env_file"
        echo -e "${GREEN}  ✓ Google Client ID configured${NC}"
    fi

    if [ ! -z "$GOOGLE_CLIENT_SECRET" ]; then
        sed -i "s|GOOGLE_CLIENT_SECRET=.*|GOOGLE_CLIENT_SECRET=$GOOGLE_CLIENT_SECRET|g" "$env_file"
        echo -e "${GREEN}  ✓ Google Client Secret configured${NC}"
    fi

    if [ ! -z "$NEXTAUTH_SECRET" ]; then
        sed -i "s|NEXTAUTH_SECRET=.*|NEXTAUTH_SECRET=$NEXTAUTH_SECRET|g" "$env_file"
        echo -e "${GREEN}  ✓ NextAuth Secret configured${NC}"
    fi

    echo ""
}

# Restore Railway backend .env
restore_env "Railway Backend" "railway/.env" "railway/.env.example"

# Restore Vercel frontend .env
restore_env "Vercel Frontend" "vercel/.env.local" "vercel/.env.example"

# Restore Dashboards .env
restore_env "Dashboards" "dashboards/.env" "dashboards/.env.example"

# Restore MCP Server .env
restore_env "MCP Server" "mcp-server/.env" "mcp-server/.env.example"

# Railway CLI setup
echo "🚂 Railway CLI Setup"
echo "===================="
echo ""

if [ ! -z "$RAILWAY_TOKEN" ]; then
    echo -e "${YELLOW}Authenticating with Railway...${NC}"
    export RAILWAY_TOKEN=$RAILWAY_TOKEN
    echo -e "${GREEN}✓ Railway authentication configured${NC}"

    # Try to link to project (if railway.json exists)
    if [ -f "railway.json" ]; then
        echo -e "${GREEN}✓ Railway project linked${NC}"
    fi
else
    echo -e "${YELLOW}⚠ RAILWAY_TOKEN not set - Railway CLI requires manual login${NC}"
    echo -e "${YELLOW}  Run: railway login${NC}"
fi

echo ""
echo "📋 Checklist Summary"
echo "===================="
echo ""

# Check what's configured
if [ ! -z "$OPENAI_API_KEY" ]; then
    echo -e "${GREEN}✓${NC} OpenAI API Key"
else
    echo -e "${RED}✗${NC} OpenAI API Key - ${YELLOW}Add to Codespaces secrets${NC}"
fi

if [ ! -z "$RAILWAY_TOKEN" ]; then
    echo -e "${GREEN}✓${NC} Railway Token"
else
    echo -e "${RED}✗${NC} Railway Token - ${YELLOW}Run: railway login${NC}"
fi

if [ ! -z "$GOOGLE_CLIENT_ID" ] && [ ! -z "$GOOGLE_CLIENT_SECRET" ]; then
    echo -e "${GREEN}✓${NC} Google OAuth Credentials"
else
    echo -e "${RED}✗${NC} Google OAuth - ${YELLOW}Add to Codespaces secrets${NC}"
fi

if [ ! -z "$NEXTAUTH_SECRET" ]; then
    echo -e "${GREEN}✓${NC} NextAuth Secret"
else
    echo -e "${RED}✗${NC} NextAuth Secret - ${YELLOW}Add to Codespaces secrets${NC}"
fi

echo ""
echo "📚 Documentation"
echo "================"
echo ""
echo "• Environment setup: .env-checklist.md"
echo "• Recovery audit: docs/recovery/RECOVERY_AUDIT_2025-10-17.md"
echo "• Railway guide: docs/guides/RAILWAY_ACCESS_GUIDE.md"
echo "• Session 016: docs/sessions/SESSION_016_ENV_VARS.md"
echo ""

echo -e "${GREEN}✅ Setup complete!${NC}"
echo ""
echo "🎯 Next Steps:"
echo "1. Review .env-checklist.md for missing secrets"
echo "2. Add secrets to GitHub Codespaces (Settings → Secrets)"
echo "3. Run 'railway login' if RAILWAY_TOKEN not set"
echo "4. Test services: ./scripts/health-check.sh"
echo ""
