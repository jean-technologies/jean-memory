# Jean Memory Architecture Overview

## Table of Contents
1. [Introduction](#introduction)
2. [High-Level Architecture](#high-level-architecture)
3. [Technology Stack](#technology-stack)
4. [Deployment Infrastructure](#deployment-infrastructure)
5. [Core Components](#core-components)
6. [Data Flow](#data-flow)
7. [Security & Authentication](#security--authentication)

## Introduction

Jean Memory is a full-stack personal memory management application that allows users to store, organize, and retrieve their digital memories across multiple AI applications. The system uses advanced memory techniques including vector search, graph databases, and AI-powered synthesis to provide intelligent memory retrieval and context management.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (Next.js)                      │
│  - React UI Components                                          │
│  - Redux State Management                                       │
│  - Supabase Auth Integration                                    │
│  - Real-time Memory Updates                                     │
└─────────────────┬───────────────────────────────────────────────┘
                  │ HTTPS (via API)
┌─────────────────▼───────────────────────────────────────────────┐
│                    Backend API (FastAPI)                        │
│  - RESTful API Endpoints                                        │
│  - MCP Server (Model Context Protocol)                          │
│  - Authentication & Authorization                               │
│  - Background Task Processing                                   │
└─────────────────┬───────────────────────────────────────────────┘
                  │
        ┌─────────┴──────────┬─────────────┬────────────────┐
        │                    │             │                │
┌───────▼──────┐  ┌─────────▼────┐ ┌──────▼─────┐  ┌──────▼──────┐
│   Postgres   │  │    Qdrant    │ │   Neo4j    │  │  Supabase   │
│  (Metadata)  │  │(Vector Store)│ │(Graph DB)  │  │    (Auth)   │
└──────────────┘  └──────────────┘ └────────────┘  └─────────────┘
```

## Technology Stack

### Frontend
- **Framework**: Next.js 15.2.4 (React 18)
- **UI Components**: Radix UI + shadcn/ui
- **State Management**: Redux Toolkit
- **Authentication**: Supabase Auth
- **Styling**: Tailwind CSS
- **Package Manager**: pnpm
- **Real-time**: WebSockets via Supabase
- **Analytics**: PostHog

### Backend
- **Framework**: FastAPI (Python)
- **Server**: Uvicorn ASGI
- **ORM**: SQLAlchemy
- **Task Queue**: Background tasks with asyncio
- **API Documentation**: OpenAPI/Swagger

### Databases
1. **PostgreSQL** (via Supabase)
   - User data
   - Memory metadata
   - App configurations
   - Document storage

2. **Qdrant** (Vector Database)
   - Memory embeddings
   - Semantic search
   - Vector similarity matching

3. **Neo4j** (Graph Database)
   - Memory relationships
   - Knowledge graphs
   - Entity connections

### AI/ML Services
- **OpenAI**: GPT-4 for text generation, embeddings
- **Google Gemini**: Alternative LLM for synthesis
- **Anthropic Claude**: Via MCP integration

### External Services
- **Stripe**: Payment processing
- **Twilio**: SMS integration
- **Resend**: Email delivery
- **Render.com**: Hosting platform

## Deployment Infrastructure

The application is deployed on Render.com with the following services:

### 1. Frontend Service (jean-memory-ui-virginia)
- **Region**: Virginia (US East)
- **URL**: https://jeanmemory.com
- **Build**: `pnpm install && pnpm build`
- **Auto-deploy**: On commit to main branch

### 2. Backend API Service (jean-memory-api-virginia)
- **Region**: Virginia (US East)
- **URL**: https://jean-memory-api-virginia.onrender.com
- **Build**: `pip install -r requirements.txt`
- **Pre-deploy**: Database migrations via Alembic
- **Health checks**: /health endpoint monitoring

### 3. Legacy Backend (jean-memory-api)
- **Region**: Oregon (US West)
- **Purpose**: Fallback/migration support
- **Configuration**: Mirrors Virginia service

### 4. Cron Jobs
- **Narrative Backfill**: Weekly user narrative generation
- **Schedule**: Sundays at 2 AM UTC

## Core Components

### 1. Memory Management System
- **Jean Memory Library** (`jean_memory/`)
  - Core memory operations
  - Vector search engine
  - Graph memory integration
  - AI-powered synthesis

### 2. Model Context Protocol (MCP)
- **MCP Server**: Enables AI assistants to interact with memories
- **Supported Clients**:
  - Claude Desktop
  - ChatGPT (via custom GPT)
  - VS Code
  - Cursor
  - Other MCP-compatible tools

### 3. Authentication System
- **Supabase Auth Integration**
  - JWT-based authentication
  - Social login (Google, GitHub)
  - API key authentication
  - Row-level security

### 4. Background Processing
- **Document Processing**: Chunk and embed documents
- **Memory Categorization**: Auto-categorize memories
- **Sync Operations**: Integration data sync
- **Narrative Generation**: AI-powered user narratives

## Data Flow

### Memory Creation Flow
1. User creates memory via UI or MCP tool
2. API validates and stores metadata in PostgreSQL
3. Background task generates embeddings (OpenAI)
4. Embeddings stored in Qdrant
5. Graph relationships updated in Neo4j
6. Categories auto-assigned via AI

### Memory Retrieval Flow
1. User queries memory (search/ask)
2. Query embedded using same model
3. Vector similarity search in Qdrant
4. Graph context fetched from Neo4j
5. Results ranked and filtered
6. AI synthesis for natural language response

### MCP Integration Flow
1. AI assistant connects via MCP endpoint
2. Authentication via user ID + client name
3. Tools exposed: add_memories, search_memory, ask_memory
4. Smart context orchestration for relevance
5. Responses formatted for specific client

## Security & Authentication

### Authentication Layers
1. **Supabase JWT**: Primary authentication
2. **API Keys**: Alternative for programmatic access
3. **Row-Level Security**: Database-level protection
4. **CORS**: Configured for allowed origins

### Security Features
- HTTPS everywhere
- Environment variable isolation
- API rate limiting
- Input validation and sanitization
- Secure password hashing
- Phone number verification (SMS)

### Data Privacy
- User data isolation
- Encrypted storage
- GDPR compliance features
- Data export capabilities
- Memory deletion support

## Next Steps

For detailed information about specific components, see:
- [Backend API Documentation](./JEAN_MEMORY_BACKEND_API.md)
- [Frontend Architecture](./JEAN_MEMORY_FRONTEND.md)
- [MCP Integration Guide](./JEAN_MEMORY_MCP_INTEGRATION.md)
- [Database Schema](./JEAN_MEMORY_DATABASE_SCHEMA.md)