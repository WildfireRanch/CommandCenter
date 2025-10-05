# MCP Server Quick Start 🚀

## What You Have Now

✅ **MCP Server Built & Ready**
- Location: `/workspaces/CommandCenter/mcp-server/`
- Status: Tested and validated
- API: Connected to Railway

## 3-Step Setup

### Step 1: Find Your Path

```bash
cd /workspaces/CommandCenter/mcp-server
pwd
# Copy this path!
```

### Step 2: Configure Claude Desktop

Edit your config file:
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

Add this (replace `YOUR_PATH_HERE`):

```json
{
  "mcpServers": {
    "commandcenter": {
      "command": "node",
      "args": ["YOUR_PATH_HERE/mcp-server/dist/index.js"],
      "env": {
        "RAILWAY_API_URL": "https://api.wildfireranch.us",
        "API_KEY": "c8AeEqNFckwzjTRzVhjOgAtXBd88vEprAtFZxNJXY8Gc"
      }
    }
  }
}
```

### Step 3: Restart & Test

1. **Quit Claude Desktop** (Cmd+Q on Mac)
2. **Relaunch Claude Desktop**
3. **Test**: Ask Claude to "Use ask_agent to check my battery level"

## What You Can Do

### Energy Monitoring
- "What's my current battery status?"
- "Show me solar production for the last 24 hours"
- "Get the latest energy snapshot"

### Conversations
- "List recent conversations"
- "Get conversation [id]"

### Agent Queries
- Ask anything about your energy system
- Conversations have memory across sessions

## Tools Available

1. **ask_agent** - Query the Solar Controller
2. **get_energy_data** - Retrieve energy metrics
3. **get_conversations** - View conversation history

## Resources Available

- `commandcenter://energy/latest` - Latest snapshot
- `commandcenter://health` - System status

## Troubleshooting

**MCP not detected?**
```bash
# Verify build
ls -la dist/index.js

# Test connection
node test-server.js
```

**API errors?**
```bash
# Check Railway API
curl https://api.wildfireranch.us/health
```

## Need Help?

- Full instructions: [INSTALL.md](INSTALL.md)
- Server docs: [README.md](README.md)
- Session summary: [../docs/sessions/SESSION_009_SUMMARY.md](../docs/sessions/SESSION_009_SUMMARY.md)

---

🎉 **That's it!** You now have CommandCenter in Claude Desktop.
