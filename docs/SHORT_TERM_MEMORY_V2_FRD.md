# Short-term Memory V2 - Functional Requirements Document

**Version**: 2.0  
**Date**: January 2025  
**Status**: Ready for Implementation

## Executive Summary
Add server-side semantic search capabilities to Jean Memory's existing context engineering system to provide faster, more accurate memory retrieval for all MCP-compatible clients.

## Goals
1. Enable semantic similarity search for memory retrieval (vs keyword matching)
2. Improve response time for context retrieval by 5x
3. Support all MCP clients (Claude Desktop, ChatGPT, mobile/SMS, React apps)
4. Maintain backward compatibility with existing system

## Scope

### In Scope
- Server-side FAISS semantic search implementation
- Per-user session isolation with automatic cleanup
- Integration with existing `jean_memory` MCP tool
- Memory management for Render deployment constraints
- Reuse of existing OpenAI embeddings from mem0

### Out of Scope
- Client-side implementations
- Changes to core memory storage (Qdrant)
- Modifications to existing mem0 functionality
- Long-term memory modifications
- Authentication/authorization changes

## User Flows

### Flow 1: New Conversation Start
1. User initiates new conversation via MCP client
2. System pre-loads last 50 memories with semantic indexing
3. FAISS index created for user session
4. User queries are matched semantically against cached memories
5. Relevant context returned in <20ms

### Flow 2: Ongoing Conversation
1. User sends message through MCP client
2. System generates embedding for query
3. FAISS performs semantic search in user's index
4. Top 5 most relevant memories returned
5. Context appended to response

### Flow 3: Session Cleanup
1. System monitors active sessions every 10 minutes
2. Sessions older than 30 minutes are expired
3. Sessions exceeding 50 concurrent users trigger cleanup
4. Oldest sessions removed to maintain memory limits

## Success Criteria
- Semantic search hit rate >60% for simple queries
- Response time <20ms for cached searches
- Support for 50 concurrent users on Render
- Zero breaking changes to existing functionality
- All MCP clients fully supported

## Dependencies
- `faiss-cpu` library (v1.7.4)
- Existing mem0 embedding service
- Render hosting environment (512MB memory limit)
- Existing `ContextCacheManager` infrastructure