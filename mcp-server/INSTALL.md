# MCP Server Installation Guide

## ✅ Step 1: Verify Setup

The MCP server is already built and tested! You should see:

```
✅ Health: healthy
✅ Database: Connected
✅ OpenAI: Configured
✅ API connection: Working
```

## 📋 Step 2: Configure Claude Desktop

### Find Your Config File

**macOS:**
```bash
open ~/Library/Application\ Support/Claude/
# Look for: claude_desktop_config.json
```

**Windows:**
```bash
# File location: %APPDATA%\Claude\claude_desktop_config.json
# Usually: C:\Users\YourName\AppData\Roaming\Claude\claude_desktop_config.json
```

**Linux:**
```bash
~/.config/Claude/claude_desktop_config.json
```

### Add CommandCenter MCP Server

**Option A: If config file exists**, add to the `mcpServers` section:

```json
{
  "mcpServers": {
    "commandcenter": {
      "command": "node",
      "args": [
        "/workspaces/CommandCenter/mcp-server/dist/index.js"
      ],
      "env": {
        "RAILWAY_API_URL": "https://api.wildfireranch.us",
        "API_KEY": "c8AeEqNFckwzjTRzVhjOgAtXBd88vEprAtFZxNJXY8Gc"
      }
    }
  }
}
```

**Option B: If config file doesn't exist**, create it with:

```json
{
  "mcpServers": {
    "commandcenter": {
      "command": "node",
      "args": [
        "/workspaces/CommandCenter/mcp-server/dist/index.js"
      ],
      "env": {
        "RAILWAY_API_URL": "https://api.wildfireranch.us",
        "API_KEY": "c8AeEqNFckwzjTRzVhjOgAtXBd88vEprAtFZxNJXY8Gc"
      }
    }
  }
}
```

**⚠️ IMPORTANT**:
- Replace `/workspaces/CommandCenter` with your **actual absolute path**
- If you're on **Windows**, use double backslashes: `C:\\Users\\...\\CommandCenter\\mcp-server\\dist\\index.js`

### Finding Your Absolute Path

**macOS/Linux:**
```bash
cd /workspaces/CommandCenter/mcp-server
pwd
# Copy the output
```

**Windows (PowerShell):**
```powershell
cd C:\path\to\CommandCenter\mcp-server
pwd
# Copy the output
```

## 🚀 Step 3: Restart Claude Desktop

1. **Quit Claude Desktop completely** (not just close the window)
   - macOS: `Cmd + Q`
   - Windows: Right-click taskbar icon → Quit

2. **Relaunch Claude Desktop**

3. **Verify MCP Server is Loaded**:
   - Look for a 🔌 icon or "Tools" indicator
   - Start a new chat
   - Type: "What MCP servers are available?"

## 🧪 Step 4: Test the Integration

In Claude Desktop, try these commands:

### Test 1: Ask the Agent
```
Use the ask_agent tool to ask: "What's my current battery level?"
```

### Test 2: Get Energy Data
```
Use get_energy_data to get the latest energy snapshot
```

### Test 3: View Conversations
```
Use get_conversations to list recent conversations
```

## 📊 What You Can Do Now

### Energy Monitoring
- "What's my battery status?"
- "Show me solar production stats for the last 24 hours"
- "Get the latest energy data"

### Conversations
- "Show me recent conversations with the agent"
- "Get conversation details for [id]"

### Multi-turn Conversations
The agent has memory! Continue conversations by using the `session_id` returned in responses.

## 🔧 Troubleshooting

### MCP Server Not Detected

1. **Check Node.js version** (need 18+):
   ```bash
   node --version
   ```

2. **Verify build succeeded**:
   ```bash
   cd /workspaces/CommandCenter/mcp-server
   ls -la dist/index.js
   ```

3. **Test server manually**:
   ```bash
   node test-server.js
   ```

4. **Check Claude Desktop logs**:
   - macOS: `~/Library/Logs/Claude/`
   - Windows: `%APPDATA%\Claude\logs\`

### API Connection Fails

1. **Verify Railway API is up**:
   ```bash
   curl https://api.wildfireranch.us/health
   ```

2. **Check API key** in config matches your `.env`

### Tools Not Appearing

1. **Restart Claude Desktop completely** (not just reload)
2. **Check config file syntax** (valid JSON, no trailing commas)
3. **Verify absolute path** is correct

## 🎯 Next Steps

Now that MCP is working, you can:

1. ✅ **Use agent from Claude Desktop** (complete!)
2. 🔄 **Set up CrewAI Studio** (next session)
3. 🎨 **Build web frontend** (future)

## 📝 Quick Reference

**Config location (macOS):**
```
~/Library/Application Support/Claude/claude_desktop_config.json
```

**Test command:**
```bash
node /workspaces/CommandCenter/mcp-server/test-server.js
```

**Rebuild server:**
```bash
cd /workspaces/CommandCenter/mcp-server
npm run build
```

---

🎉 **You're all set!** Your CommandCenter agent is now accessible from Claude Desktop via MCP.
