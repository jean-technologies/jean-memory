# VS Code MCP Setup for Jean Memory

## Complete Setup Guide

### Step 1: Enable MCP in VS Code Settings

#### Find Your settings.json File:

**Mac:**
1. Press `Cmd+Shift+P` to open command palette
2. Type: `Open Settings (JSON)` (not "User" - just "Open Settings JSON")
3. Select "Preferences: Open Settings (JSON)"

**Alternative Mac Path:**
- Go to: `~/Library/Application Support/Code/User/settings.json`
- Open in any text editor

**Windows:**
- Path: `%APPDATA%\Code\User\settings.json`

**Linux:**
- Path: `~/.config/Code/User/settings.json`

#### Add These Lines to settings.json:

```json
{
  "chat.mcp.enabled": true,
  "chat.mcp.discovery.enabled": true
}
```

### Step 2: Create MCP Configuration File

#### Location: `.vscode/mcp.json` in your project root

**How to create it:**

1. **In VS Code:**
   - Open your project folder
   - Right-click in the Explorer sidebar
   - Select "New Folder" → name it `.vscode` (if it doesn't exist)
   - Right-click on `.vscode` folder
   - Select "New File" → name it `mcp.json`

2. **Or via Terminal:**
```bash
mkdir -p .vscode
touch .vscode/mcp.json
```

3. **Add this content to `.vscode/mcp.json`:**

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

4. **IMPORTANT**: Replace `YOUR_USER_ID_HERE` with your actual Jean Memory user ID (e.g., `2822dc63-74a4-4ba1-b406-166352591123`)

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



### Troubleshooting

#### Can't find settings.json?
1. In VS Code, try: `Cmd+Shift+P` → type `Open Settings JSON` (without "User")
2. Or directly open: `~/Library/Application Support/Code/User/settings.json` on Mac
3. Make sure VS Code is open when using command palette

#### Tools not showing up?
1. Make sure both MCP settings are enabled in VS Code settings.json
2. Verify your `.vscode/mcp.json` is in the project root
3. Check that you replaced `YOUR_USER_ID_HERE` with your actual ID
4. Restart VS Code completely (not just reload)
5. Make sure you're in "Agent" mode in the chat panel

#### "Trust" prompt appears?
- Click "Trust" when prompted - this is normal for MCP servers

#### Connection errors?
1. Check your internet connection
2. Verify the URL is correct: `https://api.jeanmemory.com/mcp/claude/sse/YOUR_USER_ID`
3. Make sure you have `npx` and `supergateway` available

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
3. Ensure `supergateway` is installed: `npm install -g supergateway`