#!/bin/bash
# Sync environment variables from master config to all .env files
#
# Usage: bash docs/configuration/sync-env.sh

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

MASTER_FILE="docs/configuration/.env.master"
ROOT_DIR="/workspaces/CommandCenter"

echo -e "${BLUE}🔄 Environment Variable Sync${NC}"
echo "=============================="
echo ""

# Check if master file exists
if [ ! -f "$MASTER_FILE" ]; then
    echo -e "${RED}✗ Master config not found: $MASTER_FILE${NC}"
    exit 1
fi

# Source the master file
source "$MASTER_FILE"

echo -e "${YELLOW}📋 Reading master config...${NC}"
echo ""

# Function to update .env file
update_env() {
    local service=$1
    local env_file=$2

    echo -e "${BLUE}Updating: $service${NC}"
    echo "  File: $env_file"

    if [ ! -f "$env_file" ]; then
        echo -e "  ${RED}✗ File not found, skipping${NC}"
        echo ""
        return
    fi

    # Update variables (only if they have values in master)
    [ ! -z "$OPENAI_API_KEY" ] && sed -i "s|^OPENAI_API_KEY=.*|OPENAI_API_KEY=$OPENAI_API_KEY|g" "$env_file"
    [ ! -z "$DATABASE_URL" ] && sed -i "s|^DATABASE_URL=.*|DATABASE_URL=$DATABASE_URL|g" "$env_file"
    [ ! -z "$REDIS_URL" ] && sed -i "s|^REDIS_URL=.*|REDIS_URL=$REDIS_URL|g" "$env_file"
    [ ! -z "$GOOGLE_CLIENT_ID" ] && sed -i "s|^GOOGLE_CLIENT_ID=.*|GOOGLE_CLIENT_ID=$GOOGLE_CLIENT_ID|g" "$env_file"
    [ ! -z "$GOOGLE_CLIENT_SECRET" ] && sed -i "s|^GOOGLE_CLIENT_SECRET=.*|GOOGLE_CLIENT_SECRET=$GOOGLE_CLIENT_SECRET|g" "$env_file"
    [ ! -z "$GOOGLE_SERVICE_ACCOUNT_JSON" ] && sed -i "s|^GOOGLE_SERVICE_ACCOUNT_JSON=.*|GOOGLE_SERVICE_ACCOUNT_JSON=$GOOGLE_SERVICE_ACCOUNT_JSON|g" "$env_file"
    [ ! -z "$GOOGLE_DOCS_KB_FOLDER_ID" ] && sed -i "s|^GOOGLE_DOCS_KB_FOLDER_ID=.*|GOOGLE_DOCS_KB_FOLDER_ID=$GOOGLE_DOCS_KB_FOLDER_ID|g" "$env_file"
    [ ! -z "$NEXTAUTH_SECRET" ] && sed -i "s|^NEXTAUTH_SECRET=.*|NEXTAUTH_SECRET=$NEXTAUTH_SECRET|g" "$env_file"
    [ ! -z "$NEXTAUTH_URL" ] && sed -i "s|^NEXTAUTH_URL=.*|NEXTAUTH_URL=$NEXTAUTH_URL|g" "$env_file"
    [ ! -z "$ALLOWED_EMAIL" ] && sed -i "s|^ALLOWED_EMAIL=.*|ALLOWED_EMAIL=$ALLOWED_EMAIL|g" "$env_file"
    [ ! -z "$SOLARK_EMAIL" ] && sed -i "s|^SOLARK_EMAIL=.*|SOLARK_EMAIL=$SOLARK_EMAIL|g" "$env_file"
    [ ! -z "$SOLARK_PASSWORD" ] && sed -i "s|^SOLARK_PASSWORD=.*|SOLARK_PASSWORD=$SOLARK_PASSWORD|g" "$env_file"
    [ ! -z "$VICTRON_VRM_USERNAME" ] && sed -i "s|^VICTRON_VRM_USERNAME=.*|VICTRON_VRM_USERNAME=$VICTRON_VRM_USERNAME|g" "$env_file"
    [ ! -z "$VICTRON_VRM_PASSWORD" ] && sed -i "s|^VICTRON_VRM_PASSWORD=.*|VICTRON_VRM_PASSWORD=$VICTRON_VRM_PASSWORD|g" "$env_file"
    [ ! -z "$VICTRON_INSTALLATION_ID" ] && sed -i "s|^VICTRON_INSTALLATION_ID=.*|VICTRON_INSTALLATION_ID=$VICTRON_INSTALLATION_ID|g" "$env_file"
    [ ! -z "$NEXT_PUBLIC_API_URL" ] && sed -i "s|^NEXT_PUBLIC_API_URL=.*|NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL|g" "$env_file"
    [ ! -z "$NEXT_PUBLIC_STUDIO_URL" ] && sed -i "s|^NEXT_PUBLIC_STUDIO_URL=.*|NEXT_PUBLIC_STUDIO_URL=$NEXT_PUBLIC_STUDIO_URL|g" "$env_file"
    [ ! -z "$RAILWAY_API_URL" ] && sed -i "s|^RAILWAY_API_URL=.*|RAILWAY_API_URL=$RAILWAY_API_URL|g" "$env_file"

    echo -e "  ${GREEN}✓ Updated${NC}"
    echo ""
}

# Update all .env files
update_env "Railway Backend" "railway/.env"
update_env "Vercel Frontend" "vercel/.env.local"
update_env "Streamlit Dashboard" "dashboards/.env"
update_env "MCP Server" "mcp-server/.env"

echo -e "${GREEN}✅ Sync complete!${NC}"
echo ""
echo -e "${BLUE}📊 Summary:${NC}"
echo "  Master config: $MASTER_FILE"
echo "  Updated files:"
echo "    - railway/.env"
echo "    - vercel/.env.local"
echo "    - dashboards/.env"
echo "    - mcp-server/.env"
echo ""
echo -e "${YELLOW}🔐 Next steps:${NC}"
echo "  1. Review updated .env files"
echo "  2. Test services locally"
echo "  3. Backup to Codespaces: bash .devcontainer/backup-env.sh"
echo ""
