#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
# CommandCenter Repository Setup Script
# ═══════════════════════════════════════════════════════════════════════════
# Purpose: Create complete directory structure for CommandCenter V1
# Run from: Repository root (commandcenter/)
# Usage: chmod +x setup.sh && ./setup.sh
# ═══════════════════════════════════════════════════════════════════════════

set -e  # Exit on error

echo "🚀 Setting up CommandCenter repository structure..."
echo ""

# ─────────────────────────────────────────────────────────────────────────────
# Create Railway Backend Structure
# ─────────────────────────────────────────────────────────────────────────────

echo "📁 Creating railway/ structure..."

mkdir -p railway/src/{agents,crews,tools,integrations,kb,memory,database,api/routes,config}
mkdir -p railway/tests/{test_tools,test_agents,test_api,test_integration}
mkdir -p railway/alembic/versions
mkdir -p railway/logs
mkdir -p railway/data/{index,secrets}

# Create all __init__.py files for Python packages
find railway/src -type d -exec touch {}/__init__.py \;
find railway/tests -type d -exec touch {}/__init__.py \;

echo "  ✅ railway/ structure created"

# ─────────────────────────────────────────────────────────────────────────────
# Create Vercel MCP Server Structure
# ─────────────────────────────────────────────────────────────────────────────

echo "📁 Creating vercel/ structure..."

mkdir -p vercel/app/{api/mcp,admin}
mkdir -p vercel/lib/mcp
mkdir -p vercel/public

echo "  ✅ vercel/ structure created"

# ─────────────────────────────────────────────────────────────────────────────
# Create Supporting Directories
# ─────────────────────────────────────────────────────────────────────────────

echo "📁 Creating supporting directories..."

mkdir -p scripts
mkdir -p .github/workflows

echo "  ✅ Supporting directories created"

# ─────────────────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────────────────

echo ""
echo "✅ Repository structure created successfully!"
echo ""
echo "📂 Directory structure:"
echo ""
tree -L 3 -I '__pycache__|*.pyc|node_modules' . || find . -type d -maxdepth 3 | sort
echo ""
echo "Next steps:"
echo "1. Review the structure above"
echo "2. Add initial configuration files (requirements.txt, package.json)"
echo "3. Start porting tools from Relay"
echo ""
echo "🎉 Ready to build CommandCenter!"