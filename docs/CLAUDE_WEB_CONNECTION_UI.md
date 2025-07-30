# Updated Claude Connection UI Copy

## For Claude Web (OAuth - Recommended)

### Main Heading
**Connect Jean Memory to Claude**

### Description
**Jean Memory provides AI assistants with secure access to your personal knowledge and memories.**

---

### Primary Option (Claude Web)
**🌐 Connect to Claude Web**

**Simply add this URL to Claude's MCP settings:**

```
https://jean-memory-api-virginia.onrender.com/mcp
```

**Setup Instructions:**
1. Copy the URL above
2. In Claude, go to Settings → Feature Preview → Model Context Protocol  
3. Add new MCP server and paste the URL
4. Follow Claude's OAuth login flow
5. Grant Jean Memory access to your memories

**✨ Benefits:**
- ✅ Secure OAuth authentication
- ✅ No API keys to manage  
- ✅ Works in Claude web and mobile
- ✅ Automatic login and setup

---

### Alternative Option (Claude Desktop)
**💻 Claude Desktop Extension**

For Claude Desktop app users who prefer manual setup:

```bash
npx -y supergateway --stdio https://jean-memory-api-virginia.onrender.com/mcp/v2/claude/2282060d-5b91-437f-b068-a710c93bc040
```

**Note:** This method requires your User ID and works only with Claude Desktop. The web version above is recommended for most users.

---

### Which Should I Choose?

| Method | Best For | Authentication | Setup |
|--------|----------|----------------|-------|
| **Claude Web** | Most users, web/mobile | Secure OAuth | One-click |
| **Claude Desktop** | Desktop app, advanced users | API Key | Manual |

**Recommendation:** Use the Claude Web option unless you specifically need the desktop extension.

---

### Troubleshooting

**Claude Web not working?**
- Ensure you're using the exact URL: `https://jean-memory-api-virginia.onrender.com/mcp`
- Try the OAuth flow in an incognito/private browser window
- Check that you have a Jean Memory account

**Need help?** Contact support with your User ID: `2282060d-5b91-437f-b068-a710c93bc040`
