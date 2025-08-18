# Jean Memory for Users - Your Universal AI Memory Layer

**Date:** August 7, 2025  
**Status:** Live Product  
**Purpose:** Enable users to have persistent memory across all their AI applications

## Executive Summary

Jean Memory provides users with a centralized memory system that works across all their AI tools - ChatGPT, Claude Desktop, Cursor, Windsurf, and more. By creating a Jean Memory account and connecting your AI applications, you gain persistent context that follows you everywhere, eliminating the need to re-explain yourself to each new AI tool.

## The Problem We Solve

### Current AI Fragmentation
- **ChatGPT** doesn't know what you discussed with **Claude**
- **Cursor** has no context from your **Windsurf** sessions
- Every new AI tool starts from zero, knowing nothing about you
- You constantly repeat context, preferences, and project details
- Your valuable AI interactions are siloed and lost

### The Jean Memory Solution
One account, one memory, infinite AI applications. Your conversations, documents, and context flow seamlessly between all your AI tools.

## How It Works

### 1. Sign Up for Jean Memory

Visit [jeanmemory.com](https://jeanmemory.com) and create your account:
- **Email/Password**: Traditional signup with email verification
- **Google OAuth**: One-click signup with your Google account
- **GitHub OAuth**: Perfect for developers, sign in with GitHub

### 2. Access Your Dashboard

Once logged in, you'll see your personalized dashboard featuring:
- **Apps Connected**: Track which AI tools are using your memory
- **Memories Created**: See your total memory count grow
- **Your Life's Narrative**: AI-synthesized summary of your memories
- **Integration Gallery**: Connect new AI applications

### 3. Connect Your AI Applications

#### Currently Available Integrations:

**🤖 AI Assistants**
- **ChatGPT**: Deep research memories integration
- **Claude Desktop**: One-click MCP install for Claude
- **Cursor**: AI-powered code editor with memory
- **Windsurf**: Another AI code editor

**📝 Document Sources**
- **Notion**: Sync your workspace (Coming Soon)
- **Google Drive**: Import documents automatically
- **Direct Upload**: Add PDFs, text files, and more

**🌐 Social & Content**
- **X (Twitter)**: Weekly sync of your posts
- **Substack**: Automatic import of your writings
- **More coming**: LinkedIn, Medium, etc.

### 4. MCP (Model Context Protocol) Setup

For AI applications that support MCP:

```bash
# Claude Desktop users - add to your config:
{
  "servers": {
    "jean-memory": {
      "command": "npx",
      "args": ["@jean-memory/mcp"],
      "api_key": "your_jean_api_key_here"
    }
  }
}
```

This gives your AI applications access to:
- `jean_memory` tool: Retrieve relevant memories
- `store_document` tool: Save new information

### 5. Explore Your Memory

#### Memories Page (`/memories`)
- **List View**: See all your memories chronologically
- **Filter by Source**: View memories from specific apps
- **Search**: Find specific memories quickly
- **Sort Options**: By date, relevance, or source
- **Edit/Delete**: Manage your memory vault

#### Life Graph (`/life-graph`)
- **Visual Knowledge Graph**: See connections between memories
- **Entity Relationships**: Understand how concepts relate
- **Time-based Views**: See memory evolution
- **Interactive Exploration**: Click to dive deeper

## Key Features

### 🧠 Intelligent Memory System

Our tri-database architecture ensures powerful memory capabilities:

1. **Qdrant (Vector DB)**: Lightning-fast semantic search
2. **Neo4j (Graph DB)**: Rich relationship mapping
3. **PostgreSQL**: Reliable metadata storage

### 🔄 Automatic Synchronization

- **Real-time Updates**: Changes sync across all connected apps
- **Scheduled Imports**: Social media and content platforms sync weekly
- **Conflict Resolution**: Smart de-duplication prevents redundancy

### 🎯 Context Engineering

More than storage - we provide intelligent context:
- **Relevance Ranking**: Most important memories surface first
- **Relationship Discovery**: Find hidden connections
- **Temporal Awareness**: Understands recency and patterns
- **Self-Organization**: Memory optimization during idle time

### 🔐 Privacy & Control

- **You Own Your Data**: Export anytime
- **Granular Permissions**: Control what each app can access
- **Encryption**: Secure storage of all memories
- **GDPR Compliant**: Full privacy law compliance

## Use Cases

### 🎓 Continuous Learning
*Sarah is learning machine learning across multiple platforms*
- Takes courses on ChatGPT
- Codes examples in Cursor
- Debugs with Claude Desktop
- All tools know her learning progress and style

### 💼 Project Management
*Michael manages multiple client projects*
- Project details discussed in ChatGPT
- Code written in Windsurf
- Documentation in Notion
- Every tool has full project context

### ✍️ Content Creation
*Alice writes across multiple platforms*
- Brainstorms with Claude
- Writes drafts in Notion
- Posts on X and Substack
- AI assistants know her writing style and topics

### 🔬 Research
*Dr. Chen conducts academic research*
- Literature reviews in ChatGPT
- Data analysis in Cursor
- Paper writing with Claude
- Seamless knowledge transfer between tools

## Getting Started Guide

### Step 1: Create Account
1. Visit [jeanmemory.com](https://jeanmemory.com)
2. Click "Sign Up"
3. Choose your preferred method (Email, Google, GitHub)
4. Verify your account

### Step 2: Connect First App
1. Go to Dashboard
2. Find your preferred AI tool
3. Click "Connect"
4. Follow integration instructions

### Step 3: Start Using Memory
- Your AI tools now share context
- New conversations build on past ones
- Documents are accessible everywhere
- Memories grow automatically

## Pricing

### Free Tier
- 1,000 memories/month
- 3 app integrations
- Basic search and filtering
- 30-day memory retention

### Pro ($9.99/month)
- Unlimited memories
- Unlimited integrations
- Advanced Life Graph
- Permanent retention
- Priority support

### Team (Coming Soon)
- Shared team memories
- Collaboration features
- Admin controls
- SSO support

## For Developers

Jean Memory isn't just for end users - developers can build AI applications that tap into user memories through our SDK. When you grant permissions to developer applications, you're expanding the ecosystem of AI tools that understand you. Learn more about [Sign in with Jean for Developers](./SIGN_IN_WITH_JEAN_BUSINESS_CASE.md) | [View Full Ecosystem](./JEAN_MEMORY_ECOSYSTEM.md).

## The Future of AI Memory

We envision a world where:
- AI tools are truly personalized to each user
- Context flows seamlessly between applications
- Knowledge compounds over time
- AI becomes a true extension of human memory

Jean Memory is the infrastructure making this vision reality.

## FAQs

**Q: Is my data safe?**
A: Yes, we use industry-standard encryption and you maintain full control over your data.

**Q: Can I delete memories?**
A: Absolutely. You can delete individual memories or your entire account at any time.

**Q: Which AI tools are supported?**
A: We support any tool using MCP protocol, plus custom integrations for major platforms.

**Q: How is this different from browser history?**
A: We capture semantic meaning and relationships, not just a log of activities.

## Join the Memory Revolution

Stop repeating yourself to every AI tool. Create your Jean Memory account today and experience truly personalized AI across all your applications.

[Get Started](https://jeanmemory.com) | [View Dashboard](https://jeanmemory.com/dashboard) | [Documentation](https://docs.jeanmemory.com)