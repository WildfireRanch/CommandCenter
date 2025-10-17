#!/bin/bash
# Backup .env files to GitHub Codespaces Secrets
# This script helps you save critical env vars as Codespaces secrets

set -e

echo "🔐 Environment Backup to GitHub Codespaces Secrets"
echo "==================================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Check if gh CLI is installed
if ! command -v gh &> /dev/null; then
    echo -e "${RED}✗ GitHub CLI (gh) is not installed${NC}"
    echo "Install: https://cli.github.com"
    exit 1
fi

# Check if logged in
if ! gh auth status &> /dev/null; then
    echo -e "${YELLOW}⚠ Not logged into GitHub CLI${NC}"
    echo "Run: gh auth login"
    exit 1
fi

echo -e "${BLUE}This script will help you backup your .env files as Codespaces secrets.${NC}"
echo ""
echo "Codespaces secrets are stored encrypted and automatically injected"
echo "into your devcontainer when it's created."
echo ""
echo -e "${YELLOW}⚠ IMPORTANT: Never commit .env files to git!${NC}"
echo ""

# Function to extract value from .env file
get_env_value() {
    local file=$1
    local key=$2
    grep "^${key}=" "$file" 2>/dev/null | cut -d'=' -f2- | sed 's/^"//;s/"$//'
}

# Function to set Codespaces secret
set_codespace_secret() {
    local key=$1
    local value=$2

    if [ -z "$value" ]; then
        echo -e "${YELLOW}  ⊘ Skipping $key (empty value)${NC}"
        return
    fi

    # Check if it's a placeholder
    if [[ "$value" == *"your-"* ]] || [[ "$value" == *"YOUR_"* ]]; then
        echo -e "${YELLOW}  ⊘ Skipping $key (placeholder value)${NC}"
        return
    fi

    echo -e "${GREEN}  ✓ Setting $key${NC}"
    echo "$value" | gh secret set "$key" --app codespaces
}

echo "📦 Extracting secrets from .env files..."
echo ""

# Railway backend secrets
if [ -f "railway/.env" ]; then
    echo -e "${BLUE}Railway Backend (.env):${NC}"
    OPENAI_KEY=$(get_env_value "railway/.env" "OPENAI_API_KEY")
    GOOGLE_CID=$(get_env_value "railway/.env" "GOOGLE_CLIENT_ID")
    GOOGLE_CS=$(get_env_value "railway/.env" "GOOGLE_CLIENT_SECRET")
    GOOGLE_SA=$(get_env_value "railway/.env" "GOOGLE_SERVICE_ACCOUNT_JSON")
    GOOGLE_FOLDER=$(get_env_value "railway/.env" "GOOGLE_DOCS_KB_FOLDER_ID")
    SOLARK_EMAIL=$(get_env_value "railway/.env" "SOLARK_EMAIL")
    SOLARK_PASS=$(get_env_value "railway/.env" "SOLARK_PASSWORD")
    VICTRON_USER=$(get_env_value "railway/.env" "VICTRON_VRM_USERNAME")
    VICTRON_PASS=$(get_env_value "railway/.env" "VICTRON_VRM_PASSWORD")
    VICTRON_INSTALL=$(get_env_value "railway/.env" "VICTRON_INSTALLATION_ID")

    set_codespace_secret "OPENAI_API_KEY" "$OPENAI_KEY"
    set_codespace_secret "GOOGLE_CLIENT_ID" "$GOOGLE_CID"
    set_codespace_secret "GOOGLE_CLIENT_SECRET" "$GOOGLE_CS"
    set_codespace_secret "GOOGLE_SERVICE_ACCOUNT_JSON" "$GOOGLE_SA"
    set_codespace_secret "GOOGLE_DOCS_KB_FOLDER_ID" "$GOOGLE_FOLDER"
    set_codespace_secret "SOLARK_EMAIL" "$SOLARK_EMAIL"
    set_codespace_secret "SOLARK_PASSWORD" "$SOLARK_PASS"
    set_codespace_secret "VICTRON_VRM_USERNAME" "$VICTRON_USER"
    set_codespace_secret "VICTRON_VRM_PASSWORD" "$VICTRON_PASS"
    set_codespace_secret "VICTRON_INSTALLATION_ID" "$VICTRON_INSTALL"
    echo ""
fi

# Vercel frontend secrets
if [ -f "vercel/.env.local" ]; then
    echo -e "${BLUE}Vercel Frontend (.env.local):${NC}"
    NEXTAUTH_SEC=$(get_env_value "vercel/.env.local" "NEXTAUTH_SECRET")
    ALLOWED_EMAIL=$(get_env_value "vercel/.env.local" "ALLOWED_EMAIL")

    set_codespace_secret "NEXTAUTH_SECRET" "$NEXTAUTH_SEC"
    set_codespace_secret "ALLOWED_EMAIL" "$ALLOWED_EMAIL"
    echo ""
fi

# Railway token (if you have it)
echo -e "${BLUE}Railway CLI Token:${NC}"
if [ ! -z "$RAILWAY_TOKEN" ]; then
    set_codespace_secret "RAILWAY_TOKEN" "$RAILWAY_TOKEN"
else
    echo -e "${YELLOW}  ⊘ RAILWAY_TOKEN not in environment${NC}"
    echo -e "${YELLOW}    Get from: railway whoami --token${NC}"
fi
echo ""

echo -e "${GREEN}✅ Backup complete!${NC}"
echo ""
echo "📋 Saved secrets are now available in:"
echo "   https://github.com/settings/codespaces"
echo ""
echo "🔄 Next time you create a Codespace, these secrets will be"
echo "   automatically restored by .devcontainer/setup.sh"
echo ""
echo "🔗 Manual setup:"
echo "   To manually add/update secrets:"
echo "   gh secret set SECRET_NAME --app codespaces"
echo ""
