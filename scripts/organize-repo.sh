#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
# FILE: organize-repo.sh
# PURPOSE: Organize CommandCenter repository for Session 016
#
# WHAT IT DOES:
#   - Archives CrewAI Studio docs (not using anymore)
#   - Creates new KB design document
#   - Creates Session 016 prompt
#   - Updates progress tracking
#
# USAGE:
#   chmod +x organize-repo.sh
#   ./organize-repo.sh
# ═══════════════════════════════════════════════════════════════════════════

set -e  # Exit on error

echo "📋 Organizing CommandCenter Repository..."
echo ""

# Create archive directory
echo "1️⃣  Creating archive directory..."
mkdir -p docs/archive
echo "   ✅ docs/archive/ created"

# Move Studio docs to archive
echo ""
echo "2️⃣  Archiving CrewAI Studio documentation..."
if [ -f "docs/CREWAI_STUDIO_SETUP.md" ]; then
    echo "# ARCHIVED - Not Used in CommandCenter V1" | cat - docs/CREWAI_STUDIO_SETUP.md > docs/archive/CREWAI_STUDIO_SETUP.md
    rm docs/CREWAI_STUDIO_SETUP.md
    echo "   ✅ CREWAI_STUDIO_SETUP.md archived"
fi

if [ -f "docs/CREWAI_STUDIO_QUICKSTART.md" ]; then
    echo "# ARCHIVED - Not Used in CommandCenter V1" | cat - docs/CREWAI_STUDIO_QUICKSTART.md > docs/archive/CREWAI_STUDIO_QUICKSTART.md
    rm docs/CREWAI_STUDIO_QUICKSTART.md
    echo "   ✅ CREWAI_STUDIO_QUICKSTART.md archived"
fi

# Archive Studio-related session summaries
echo ""
echo "3️⃣  Archiving Studio session summaries..."
mv docs/sessions/SESSION_014*.md docs/archive/ 2>/dev/null || echo "   ℹ️  No SESSION_014 files to archive"

# Create sessions directory if it doesn't exist
mkdir -p docs/sessions
echo "   ✅ docs/sessions/ ready"

# Create new document placeholders
echo ""
echo "4️⃣  Creating new documentation..."
echo "   ⏳ KB design doc (see Claude's artifact: 06-knowledge-base-design.md)"
echo "   ⏳ Session 016 prompt (see Claude's artifact: SESSION_016_PROMPT.md)"
echo ""
echo "   💡 Copy these from Claude's artifacts to:"
echo "      - docs/06-knowledge-base-design.md"
echo "      - docs/sessions/SESSION_016_PROMPT.md"

# Update progress.md
echo ""
echo "5️⃣  Updating progress tracking..."
cat >> docs/progress.md << 'EOF'

---

### Session 015 - October 6, 2025
**Type:** Architecture Decision + Documentation
**Duration:** ~2 hours
**Status:** ✅ **COMPLETE - DECISIONS FINALIZED**

**Key Decisions:**
1. **Removed CrewAI Studio** - Not needed for solo developer workflow
   - Too complex (5,874 lines, 20-30 min deployments)
   - Better to use Claude Code directly
   - Archived all Studio documentation

2. **Knowledge Base Design Finalized**
   - Two-tier system: Context files (always loaded) + Full KB (searchable)
   - Google SSO for authentication + Drive/Docs access
   - Manual sync button in frontend
   - Daily automatic sync (cron)

3. **Session 016 Planned**
   - Google OAuth setup
   - KB sync implementation
   - Frontend /kb page
   - Agent integration

**Documentation Created:**
- 06-knowledge-base-design.md (complete KB architecture)
- SESSION_016_PROMPT.md (4-hour implementation guide)
- organize-repo.sh (cleanup script)

**Next Session:** SESSION_016 - Google SSO + KB Implementation (~4 hours)

EOF

echo "   ✅ progress.md updated"

# Git status
echo ""
echo "6️⃣  Current git status:"
git status --short

# Final instructions
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "✅ Repository Organization Complete!"
echo ""
echo "📋 Next Steps:"
echo "   1. Copy KB design doc from Claude's artifact to:"
echo "      docs/06-knowledge-base-design.md"
echo ""
echo "   2. Copy Session 016 prompt from Claude's artifact to:"
echo "      docs/sessions/SESSION_016_PROMPT.md"
echo ""
echo "   3. Review changes:"
echo "      git diff"
echo ""
echo "   4. Commit everything:"
echo "      git add ."
echo "      git commit -m 'Session 015: Architecture decisions + Session 016 prep'"
echo "      git push origin main"
echo ""
echo "   5. Start Session 016 when ready:"
echo "      cat docs/sessions/SESSION_016_PROMPT.md"
echo ""
echo "═══════════════════════════════════════════════════════════════"