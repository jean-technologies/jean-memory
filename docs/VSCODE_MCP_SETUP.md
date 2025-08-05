# VS Code MCP Setup for Jean Memory

## Complete Setup Guide

### Step 1: Enable MCP in VS Code Settings

#### Option A: Using Settings UI
1. Open VS Code
2. Press `Cmd+,` (Mac) or `Ctrl+,` (Windows/Linux) to open Settings
3. Search for "mcp"
4. Check the following boxes:
   - ✅ `Chat: Mcp: Enabled`
   - ✅ `Chat: Mcp: Discovery: Enabled`

#### Option B: Using settings.json
1. Press `Cmd+Shift+P` (Mac) or `Ctrl+Shift+P` (Windows/Linux)
2. Type "Preferences: Open User Settings (JSON)"
3. Add these lines to your settings.json:

```json
{
  "chat.mcp.enabled": true,
  "chat.mcp.discovery.enabled": true
}
```

### Step 2: Create MCP Configuration File

1. Create the `.vscode` folder in your project root (if it doesn't exist):
```bash
mkdir -p .vscode
```

2. Create `.vscode/mcp.json` file with this content:

```json
{
  "mcpServers": {
    "jean-memory": {
      "command": "npx",
      "args": [
        "supergateway",
        "--sse",
        "https://api.jeanmemory.com/mcp/claude/sse/YOUR_USER_ID_HERE"
      ]
    }
  }
}
```

3. **IMPORTANT**: Replace `YOUR_USER_ID_HERE` with your actual Jean Memory user ID (e.g., `2822dc63-74a4-4ba1-b406-166352591123`)

### Step 3: Verify Installation

1. **Restart VS Code completely** (Quit and reopen, not just reload window)

2. Open the Chat panel:
   - Press `Ctrl+Alt+I` (Windows/Linux) or `Cmd+Alt+I` (Mac)
   - Or click the chat icon in the sidebar

3. Switch to Agent mode:
   - Look for the mode selector at the top of the chat panel
   - Select "Agent" mode

4. Click on "Tools" in the chat interface

5. You should see Jean Memory tools available

### Alternative: Using HTTP Transport (Recommended)

If the SSE method doesn't work, try the HTTP transport:

`.vscode/mcp.json`:
```json
{
  "mcpServers": {
    "jean-memory": {
      "uri": "https://jean-memory-api-virginia.onrender.com/mcp/v2/claude/YOUR_USER_ID_HERE"
    }
  }
}
```

### Troubleshooting

#### Tools not showing up?
1. Make sure both MCP settings are enabled in VS Code settings
2. Verify your `.vscode/mcp.json` is in the project root
3. Check that you replaced `YOUR_USER_ID_HERE` with your actual ID
4. Restart VS Code completely (not just reload)
5. Make sure you're in "Agent" mode in the chat panel

#### "Trust" prompt appears?
- Click "Trust" when prompted - this is normal for MCP servers

#### Connection errors?
1. Check your internet connection
2. Verify the URL is correct
3. Try the alternative HTTP transport method

### Finding Your User ID

Your Jean Memory user ID can be found:
1. In the Jean Memory dashboard at https://jeanmemory.com
2. In the installation instructions for other integrations
3. It looks like: `2822dc63-74a4-4ba1-b406-166352591123`

### What You Get

Once connected, VS Code can:
- Store and retrieve memories
- Search your knowledge base
- Access documents and context
- Build up project-specific knowledge over time

### Need Help?

If you're still having issues:
1. Check VS Code Output panel (View → Output → Select "MCP" from dropdown)
2. Look for error messages in the Developer Tools (Help → Toggle Developer Tools)
3. Try the HTTP transport instead of SSE