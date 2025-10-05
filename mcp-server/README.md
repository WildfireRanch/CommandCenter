# CommandCenter MCP Server

Model Context Protocol server for CommandCenter energy management system.

## What is This?

This MCP server allows Claude Desktop (and other MCP clients) to interact with your CommandCenter agent directly. It exposes:

- **Tools**: Ask the Solar Controller agent questions, get energy data, view conversations
- **Resources**: Access latest energy snapshots and system health

## Installation

### Local Setup

1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your Railway API URL
   ```

3. **Build the server:**
   ```bash
   npm run build
   ```

4. **Test locally:**
   ```bash
   npm run dev
   ```

### Claude Desktop Configuration

Add this to your Claude Desktop config file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "commandcenter": {
      "command": "node",
      "args": [
        "/absolute/path/to/CommandCenter/mcp-server/dist/index.js"
      ],
      "env": {
        "RAILWAY_API_URL": "https://api.wildfireranch.us",
        "API_KEY": "your-api-key-here"
      }
    }
  }
}
```

**Important**: Replace `/absolute/path/to/CommandCenter` with your actual path.

## Available Tools

### 1. `ask_agent`
Ask the Solar Controller agent a question.

**Parameters:**
- `message` (required): Your question
- `session_id` (optional): Continue a conversation

**Example:**
```json
{
  "message": "What's my battery level?",
  "session_id": "abc-123"
}
```

### 2. `get_energy_data`
Retrieve energy system data.

**Parameters:**
- `type` (required): "latest", "recent", or "stats"
- `hours` (optional): Hours to look back
- `limit` (optional): Max records

**Example:**
```json
{
  "type": "stats",
  "hours": 24
}
```

### 3. `get_conversations`
List or retrieve conversations.

**Parameters:**
- `conversation_id` (optional): Get specific conversation
- `limit` (optional): Number of conversations to list

## Available Resources

- `commandcenter://energy/latest` - Latest energy snapshot
- `commandcenter://health` - System health status

## Architecture

```
Claude Desktop → MCP Server → Railway API → PostgreSQL
                  (stdio)      (HTTPS)
```

The MCP server is a lightweight TypeScript application that:
1. Listens on stdio for MCP protocol messages
2. Translates them to HTTP requests to your Railway API
3. Returns formatted responses back to Claude

## Development

Run in development mode with auto-reload:
```bash
npm run dev
```

Build for production:
```bash
npm run build
npm start
```

## Troubleshooting

1. **Server won't start**: Check that Node.js 18+ is installed
2. **API connection fails**: Verify `RAILWAY_API_URL` is correct
3. **Authentication errors**: Check your `API_KEY` if required
4. **Claude Desktop not detecting**: Ensure config file path is correct and server builds successfully

## Next Steps

- [ ] Deploy to Vercel (optional - for SSE transport)
- [ ] Add more tools (hardware control, optimization)
- [ ] Implement prompt templates
