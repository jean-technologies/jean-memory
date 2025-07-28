# Claude Code Multi-Agent System - Master Design Document

## Executive Summary

This document defines the architecture for a Claude Code multi-agent coordination system that solves performance and precision issues with the current Jean Memory system. The design uses **ephemeral sessions with selective persistence** - ultra-fast coordination during active sessions (1-50ms operations) with intelligent migration of valuable insights to long-term memory.

### Key Performance Improvements
- **File locking**: 1-5ms (vs current 2-4s) - **400-4000x faster**
- **Change broadcasting**: 1-10ms (vs current 2-4s) - **200-4000x faster**
- **Agent messaging**: 1-5ms (vs current 2-4s) - **400-4000x faster**
- **Session sync**: 5-50ms (vs current 2-6s) - **40-1200x faster**

---

## Core Architecture: Ephemeral Sessions with Selective Persistence

### Memory Flow Design

```
┌─────────────────────────────────────────────────────────────────┐
│                    Session Lifecycle                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. Session Start                                               │
│     ├─ Create ADK Session (empty state)                        │
│     ├─ Initialize agent coordination                            │
│     └─ Start ephemeral memory tracking                         │
│                                                                 │
│  2. Active Session (Fast Operations - ADK Only)                │
│     ├─ File locking: 1-5ms                                     │
│     ├─ Change coordination: 1-10ms                             │
│     ├─ Agent messaging: 1-5ms                                  │
│     ├─ Status sync: 5-50ms                                     │
│     └─ NO writes to Jean Memory                                │
│                                                                 │
│  3. Explicit Long-term Access (When Requested)                 │
│     ├─ User asks: "What did I implement last month?"           │
│     ├─ Agent uses: @ask_jean_memory tool                       │
│     ├─ Searches: Full Jean Memory (2-6s)                       │
│     └─ Returns: Long-term context                              │
│                                                                 │
│  4. Session End (Selective Persistence)                        │
│     ├─ Analyze session content                                 │
│     ├─ Extract valuable insights                               │
│     ├─ Write summary to Jean Memory                            │
│     ├─ Discard ephemeral coordination data                     │
│     └─ Delete ADK session                                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Dual Memory System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                 Claude Code Multi-Agent Session             │
├─────────────────────────────────────────────────────────────────┤
│                                                             │
│  Fast Coordination Layer (Google ADK)                      │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Session State (1-50ms operations)                  │   │
│  │  ├─ File locks                                      │   │
│  │  ├─ Recent changes                                  │   │
│  │  ├─ Agent messages                                  │   │
│  │  └─ Coordination metadata                           │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Context Layer (Jean Memory)                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  User's Long-term Memory (2-6s operations)          │   │
│  │  ├─ Project history                                 │   │
│  │  ├─ Code documentation                              │   │
│  │  ├─ User preferences                                │   │
│  │  └─ Domain knowledge                                │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────────┘
```

---

## 1. Session-to-Long-Term Memory Migration System

### Session Content Analysis Engine

```python
# app/services/session_analyzer.py
from typing import Dict, List, Optional
import json
from datetime import datetime
from dataclasses import dataclass

@dataclass
class SessionSummary:
    """Structured summary of a completed session"""
    session_id: str
    session_name: str
    duration_minutes: int
    participating_agents: List[str]
    
    # Technical outcomes
    files_modified: List[str]
    major_changes: List[str]
    code_artifacts: List[str]
    
    # Coordination insights
    collaboration_patterns: List[str]
    conflict_resolutions: List[str]
    
    # Learnings and decisions
    key_decisions: List[str]
    technical_learnings: List[str]
    process_insights: List[str]
    
    # Metadata
    success_level: str  # "completed", "partial", "failed"
    next_steps: List[str]

class SessionAnalyzer:
    """Analyzes session content to extract valuable insights"""
    
    def __init__(self, gemini_client):
        self.gemini_client = gemini_client
    
    async def analyze_session(self, session) -> SessionSummary:
        """
        Analyze completed session and extract valuable insights
        
        Why this approach:
        1. Preserves valuable technical decisions and learnings
        2. Filters out ephemeral coordination noise
        3. Creates searchable context for future sessions
        4. Maintains project history and patterns
        """
        
        # Extract session data
        session_data = self._extract_session_data(session)
        
        # AI-powered analysis to identify valuable content
        analysis = await self._ai_analyze_content(session_data)
        
        # Structure the findings
        summary = self._create_structured_summary(session_data, analysis)
        
        return summary
    
    async def _ai_analyze_content(self, session_data: Dict) -> Dict:
        """
        Use Gemini to intelligently analyze session content
        
        Why AI analysis:
        1. Identifies semantic patterns humans might miss
        2. Distinguishes valuable insights from coordination noise
        3. Extracts implicit learnings and decisions
        4. Standardizes format for searchability
        """
        
        analysis_prompt = f"""
        Analyze this multi-agent coding session and extract valuable insights:
        
        Session Data: {json.dumps(session_data, indent=2)}
        
        Extract and categorize:
        1. KEY TECHNICAL DECISIONS: Important architectural or implementation choices
        2. LEARNINGS: New knowledge gained or problems solved
        3. COLLABORATION INSIGHTS: Effective agent coordination patterns
        4. PROJECT PROGRESS: Concrete deliverables and next steps
        5. PROBLEMS RESOLVED: Issues encountered and how they were solved
        
        Focus on content that would be valuable for:
        - Future sessions on this project
        - Learning from coordination patterns
        - Understanding technical evolution
        - Avoiding repeated mistakes
        
        Ignore ephemeral coordination like:
        - Temporary file locks
        - Simple status updates
        - Basic task assignments
        
        Format as structured JSON.
        """
        
        try:
            response = await self.gemini_client.generate_content_async(analysis_prompt)
            return json.loads(response.text)
        except Exception as e:
            logger.warning(f"AI analysis failed, using fallback: {e}")
            return self._fallback_analysis(session_data)
```

### Selective Persistence Engine

```python
# app/services/persistence_engine.py
class SelectivePersistenceEngine:
    """Handles writing session summaries to long-term memory"""
    
    def __init__(self, jean_memory_service, session_analyzer):
        self.jean_memory = jean_memory_service
        self.analyzer = session_analyzer
    
    async def persist_session_insights(self, session, base_user_id: str) -> Dict:
        """
        Convert session to long-term memories
        
        Why selective persistence:
        1. Preserves valuable project context
        2. Avoids polluting long-term memory with coordination noise
        3. Creates searchable project history
        4. Maintains agent collaboration learnings
        """
        
        # Analyze session for valuable content
        summary = await self.analyzer.analyze_session(session)
        
        # Convert to structured memories
        memories = self._create_memories_from_summary(summary)
        
        # Write to Jean Memory using original user ID (not virtual session ID)
        results = await self._write_to_jean_memory(memories, base_user_id)
        
        # Clean up session data
        await self._cleanup_session_data(session)
        
        return {
            "session_id": session.id,
            "memories_created": len(memories),
            "summary": summary,
            "jean_memory_results": results
        }
    
    def _create_memories_from_summary(self, summary: SessionSummary) -> List[str]:
        """
        Convert session summary to well-structured memories
        
        Why this format:
        1. Each memory is self-contained and searchable
        2. Tagged with session metadata for filtering
        3. Focused on learnings and decisions, not coordination
        4. Structured for future retrieval
        """
        
        memories = []
        
        # Project progress memory
        if summary.files_modified or summary.major_changes:
            memories.append(
                f"[PROJECT: {summary.session_name}] "
                f"Collaborative coding session completed. "
                f"Modified files: {', '.join(summary.files_modified)}. "
                f"Major changes: {'. '.join(summary.major_changes)}. "
                f"Duration: {summary.duration_minutes} minutes. "
                f"Agents: {', '.join(summary.participating_agents)}."
            )
        
        # Technical decisions memory
        if summary.key_decisions:
            memories.append(
                f"[DECISIONS: {summary.session_name}] "
                f"Key technical decisions made: {'. '.join(summary.key_decisions)}. "
                f"These decisions will impact future development."
            )
        
        # Learnings memory
        if summary.technical_learnings:
            memories.append(
                f"[LEARNINGS: {summary.session_name}] "
                f"Technical insights gained: {'. '.join(summary.technical_learnings)}. "
                f"These learnings can be applied to similar problems."
            )
        
        # Collaboration insights
        if summary.collaboration_patterns:
            memories.append(
                f"[COLLABORATION: {summary.session_name}] "
                f"Effective multi-agent patterns: {'. '.join(summary.collaboration_patterns)}. "
                f"These patterns improved coordination efficiency."
            )
        
        # Next steps
        if summary.next_steps:
            memories.append(
                f"[TODO: {summary.session_name}] "
                f"Next steps identified: {'. '.join(summary.next_steps)}. "
                f"These should be prioritized in future sessions."
            )
        
        return memories
```

---

## 2. Selective Long-Term Memory Access System

### Context-Aware Memory Router

```python
# app/tools/memory_router.py
class MemoryRouter:
    """Routes memory requests to appropriate system based on intent"""
    
    def __init__(self, adk_service, jean_memory_service):
        self.adk = adk_service
        self.jean_memory = jean_memory_service
    
    async def route_memory_request(self, query: str, context: Dict) -> Dict:
        """
        Intelligently route memory requests
        
        Why routing logic:
        1. Fast coordination queries go to ADK (1-50ms)
        2. Context queries go to Jean Memory when explicitly requested
        3. Prevents accidental expensive operations
        4. Maintains performance while preserving access to context
        """
        
        intent = self._analyze_query_intent(query, context)
        
        if intent == "coordination":
            return await self._handle_coordination_query(query, context)
        elif intent == "explicit_context":
            return await self._handle_context_query(query, context)
        elif intent == "auto_coordination":
            return await self._handle_auto_coordination(query, context)
        else:
            return await self._handle_fallback_query(query, context)
    
    def _analyze_query_intent(self, query: str, context: Dict) -> str:
        """
        Analyze query to determine appropriate memory system
        
        Categories:
        1. coordination: Current session file locks, changes, messages
        2. explicit_context: User explicitly asks for project history/context
        3. auto_coordination: Simple status/sync requests
        4. fallback: Unclear intent, use safe default
        """
        
        query_lower = query.lower()
        
        # Explicit context requests
        context_indicators = [
            "what did we build", "project history", "previous sessions",
            "how did we implement", "what have we done", "past decisions",
            "remember when", "last time", "before this session"
        ]
        if any(indicator in query_lower for indicator in context_indicators):
            return "explicit_context"
        
        # Coordination requests
        coordination_indicators = [
            "who has locked", "recent changes", "agent status", "current locks",
            "what files are", "sync status", "latest updates", "agent messages"
        ]
        if any(indicator in query_lower for indicator in coordination_indicators):
            return "coordination"
        
        # Auto-coordination (simple status)
        auto_indicators = ["status", "sync", "update", "check", "current"]
        if any(indicator in query_lower for indicator in auto_indicators):
            return "auto_coordination"
        
        return "fallback"
```

### Explicit Long-Term Memory Tools

```python
# app/tools/explicit_memory_access.py

@mcp.tool(description="🧠 [Long-term] Access your project history and past decisions from Jean Memory")
async def ask_jean_memory(
    question: str,
    include_session_context: bool = True
) -> Dict:
    """
    Explicitly access long-term Jean Memory for project context
    
    Why this tool:
    1. Provides access to full project history when needed
    2. Explicitly slower operation (2-6s) - user expects this
    3. Combines long-term context with current session if requested
    4. Clear separation from fast coordination tools
    """
    
    # Get base user ID (not virtual session ID)
    session_info = get_current_session_info()
    base_user_id = session_info.get('base_user_id')
    
    if not base_user_id:
        return {"error": "Long-term memory access requires valid user context"}
    
    # Search Jean Memory for context
    start_time = time.time()
    context_results = await jean_memory.search(question, base_user_id)
    search_time = time.time() - start_time
    
    response = {
        "query": question,
        "context_from_jean_memory": context_results.synthesis,
        "search_time_seconds": round(search_time, 2),
        "total_results": context_results.total_results,
        "confidence": context_results.confidence_score
    }
    
    # Optionally include current session context
    if include_session_context:
        session_context = await get_current_session_summary()
        response["current_session_context"] = session_context
    
    return response

@mcp.tool(description="📚 [Long-term] Search project documentation and past implementations")
async def search_project_history(
    query: str,
    project_filter: Optional[str] = None,
    time_range: Optional[str] = None
) -> Dict:
    """
    Search through project history and documentation
    
    Why separate tool:
    1. Focused on project-specific searches
    2. Can filter by project/timeframe
    3. Optimized for development context
    4. Clear that this is a slower, comprehensive operation
    """
    
    base_user_id = get_base_user_id()
    
    # Enhance query with project context
    enhanced_query = query
    if project_filter:
        enhanced_query += f" project:{project_filter}"
    if time_range:
        enhanced_query += f" timeframe:{time_range}"
    
    # Use deep memory query for comprehensive search
    results = await jean_memory.deep_search(enhanced_query, base_user_id)
    
    return {
        "query": query,
        "enhanced_query": enhanced_query,
        "findings": results.synthesis,
        "relevant_documents": results.mem0_results[:5],  # Top 5 docs
        "search_method": "deep_project_search"
    }
```

---

## 3. MCP Tool Architecture

### Tool Categories and Design Philosophy

**Three Tool Categories:**

1. **🔒 Fast Coordination Tools** (1-50ms) - Always available in session mode
2. **🧠 Explicit Context Tools** (2-6s) - Clearly marked as SLOW operations  
3. **🤖 Hybrid Intelligence Tools** - Smart routing based on intent

### Fast Coordination Tools (ADK-powered, 1-50ms)

```python
@mcp.tool(description="🔒 [Fast] Claim files to prevent agent conflicts")
async def session_claim_files(
    file_paths: List[str],
    operation: str = "write",
    duration_minutes: int = 30,
    force: bool = False
) -> Dict:
    """
    Why this tool:
    1. Essential for preventing agent conflicts
    2. Fast operation prevents workflow interruption
    3. Clear parameters enforce good coordination practices
    4. Force flag for emergency override
    """

@mcp.tool(description="🔓 [Fast] Release files and broadcast changes")
async def session_release_files(
    file_paths: List[str],
    changes_summary: str,
    breaking_changes: bool = False,
    next_agent_suggestions: Optional[List[str]] = None
) -> Dict:
    """
    Why structured parameters:
    1. changes_summary: Forces documentation of what was done
    2. breaking_changes: Alerts other agents to potential issues
    3. next_agent_suggestions: Guides collaboration workflow
    """

@mcp.tool(description="📢 [Fast] Send coordination message to agents")
async def session_message(
    message: str,
    message_type: str = "info",
    target_agents: Optional[List[str]] = None,
    requires_response: bool = False
) -> Dict:
    """
    Why message types:
    1. "info": General updates
    2. "warning": Potential issues
    3. "question": Needs response
    4. "request": Action needed
    5. "blocking": Prevents other agents from proceeding
    """

@mcp.tool(description="🔄 [Fast] Get session sync status and recent activities")
async def session_sync(
    minutes: int = 30,
    include_file_locks: bool = True,
    include_messages: bool = True,
    include_changes: bool = True
) -> Dict:
    """
    Why granular options:
    1. Customizable information level
    2. Faster responses when less info needed
    3. Reduces cognitive load on agents
    """
```

### Explicit Context Tools (Jean Memory, 2-6s)

```python
@mcp.tool(description="🧠 [SLOW] Access long-term project memory and history")
async def ask_jean_memory(
    question: str,
    include_session_context: bool = True,
    deep_search: bool = False
) -> Dict:
    """
    Why explicit "SLOW" marking:
    1. Sets agent expectations for response time
    2. Encourages thoughtful usage
    3. Prevents accidental expensive operations
    4. Clear distinction from fast tools
    """

@mcp.tool(description="📚 [SLOW] Search project documentation and implementations") 
async def search_project_docs(
    query: str,
    document_types: Optional[List[str]] = None,
    time_range_days: Optional[int] = None
) -> Dict:
    """
    Why document filtering:
    1. Reduces search scope for better results
    2. Faster than full-corpus search
    3. More relevant results
    """
```

### Hybrid Intelligence Tools

```python
@mcp.tool(description="🤖 [Smart] Intelligent memory search with automatic routing")
async def smart_search(
    query: str,
    prefer_speed: bool = True,
    include_context_if_needed: bool = True
) -> Dict:
    """
    Intelligent routing based on query analysis
    
    Why automatic routing:
    1. Reduces cognitive load on agents
    2. Optimizes for speed when possible
    3. Falls back to context when needed
    4. Learns from usage patterns
    """

@mcp.tool(description="🔧 [Adaptive] Context-aware agent guidance")
async def get_agent_guidance(
    current_task: str,
    stuck_on: Optional[str] = None,
    need_coordination: bool = False
) -> Dict:
    """
    Provides intelligent guidance based on current context
    
    Why this tool:
    1. Helps agents make coordination decisions
    2. Suggests appropriate tools to use
    3. Provides workflow guidance
    4. Adapts to current session context
    """
```

---

## 4. Session Lifecycle Management

### Session Initialization

```python
# app/services/session_manager.py
class SessionManager:
    """Manages complete session lifecycle"""
    
    async def initialize_session(self, session_info: Dict) -> Dict:
        """
        Initialize new multi-agent session
        
        Why this initialization:
        1. Sets up clean ADK session state
        2. Establishes agent coordination channels
        3. Initializes performance tracking
        4. Creates session-specific tooling context
        """
        
        # Create ADK session
        session = await self.adk_session_service.create_session(
            app_name=f"claude_code_{session_info['session_name']}",
            user_id=session_info['base_user_id'],
            session_id=session_info['session_name'],
            state={
                # File coordination
                'file_locks': {},
                'pending_releases': {},
                
                # Agent communication
                'agent_messages': [],
                'agent_status': {},
                'active_agents': [],
                
                # Change tracking
                'recent_changes': [],
                'session_artifacts': [],
                
                # Performance tracking
                'session_start_time': datetime.utcnow().isoformat(),
                'coordination_metrics': {
                    'lock_operations': 0,
                    'message_exchanges': 0,
                    'sync_operations': 0
                },
                
                # Context flags
                'jean_memory_accessed': False,
                'context_access_count': 0
            }
        )
        
        return {
            "session_id": session.id,
            "adk_session_ready": True,
            "coordination_tools_active": True,
            "performance_mode": "fast_coordination"
        }
```

### File Lock Management

```python
# app/coordination/file_locks.py
class FileLockManager:
    """Manages distributed file locking across agents"""
    
    async def acquire_locks(self, file_paths: List[str], agent_id: str, 
                          session: Any, operation: str = "write") -> Dict:
        """
        Acquire file locks with conflict detection
        
        Why sophisticated locking:
        1. Prevents agent conflicts and overwrites
        2. Supports read/write lock types
        3. Automatic expiration prevents deadlocks
        4. Conflict resolution guidance
        """
        
        current_locks = session.state.get('file_locks', {})
        conflicts = []
        
        # Check for conflicts
        for file_path in file_paths:
            if file_path in current_locks:
                lock = current_locks[file_path]
                if not self._is_lock_expired(lock):
                    if lock['agent_id'] != agent_id:
                        # Check if operations are compatible
                        if not self._are_operations_compatible(
                            lock['operation'], operation
                        ):
                            conflicts.append({
                                'file': file_path,
                                'locked_by': lock['agent_id'],
                                'lock_operation': lock['operation'],
                                'requested_operation': operation,
                                'expires_in_seconds': self._get_expiry_seconds(lock),
                                'resolution_suggestions': self._get_resolution_suggestions(
                                    lock, operation, agent_id
                                )
                            })
        
        if conflicts:
            return {
                "success": False,
                "conflicts": conflicts,
                "suggested_actions": self._generate_conflict_actions(conflicts)
            }
        
        # Acquire locks
        lock_time = datetime.utcnow()
        for file_path in file_paths:
            current_locks[file_path] = {
                'agent_id': agent_id,
                'operation': operation,
                'acquired_at': lock_time.isoformat(),
                'expires_at': (lock_time + timedelta(minutes=30)).isoformat(),
                'lock_id': f"{agent_id}_{uuid.uuid4().hex[:8]}"
            }
        
        return {
            "success": True,
            "locks_acquired": len(file_paths),
            "files": file_paths,
            "operation": operation,
            "expires_in_minutes": 30
        }
    
    def _are_operations_compatible(self, existing_op: str, requested_op: str) -> bool:
        """
        Determine if lock operations are compatible
        
        Compatibility matrix:
        - read + read: Compatible
        - read + write: Incompatible
        - write + read: Incompatible  
        - write + write: Incompatible
        """
        return existing_op == "read" and requested_op == "read"
```

---

## 5. Performance Optimization

### Session State Optimization

```python
# app/optimization/state_optimizer.py
class SessionStateOptimizer:
    """Optimizes session state for fast operations"""
    
    def __init__(self):
        self.max_messages = 100
        self.max_changes = 100
        self.max_artifacts = 200
        self.cleanup_interval_minutes = 60
    
    async def optimize_session_state(self, session) -> Dict:
        """
        Optimize session state to maintain performance
        
        Why state optimization:
        1. Prevents session state from growing unbounded
        2. Maintains fast read/write operations
        3. Keeps only relevant recent data
        4. Archives older data for session summary
        """
        
        original_size = self._calculate_state_size(session.state)
        
        # Archive and trim message history
        messages = session.state.get('agent_messages', [])
        if len(messages) > self.max_messages:
            archived_messages = messages[:-self.max_messages]
            session.state['agent_messages'] = messages[-self.max_messages:]
            await self._archive_messages(session.id, archived_messages)
        
        # Clean expired locks
        current_locks = session.state.get('file_locks', {})
        active_locks = {}
        expired_count = 0
        
        for file_path, lock in current_locks.items():
            if not self._is_lock_expired(lock):
                active_locks[file_path] = lock
            else:
                expired_count += 1
        
        session.state['file_locks'] = active_locks
        
        return {
            "optimization_complete": True,
            "expired_locks_cleaned": expired_count,
            "size_reduction_bytes": original_size - self._calculate_state_size(session.state)
        }
```

---

## 6. Implementation Timeline

### Week 1: Core Implementation
- **Day 1-2**: ADK setup and basic integration
- **Day 3**: Enhanced MCP routing with session detection
- **Day 4-5**: Fast coordination tools implementation

### Week 2: Enhancement and Testing
- **Day 1-2**: Intelligent context routing
- **Day 3**: Dashboard integration for session management
- **Day 4-5**: Testing with multiple agents and performance benchmarking

### Week 3: Production Readiness
- **Day 1-2**: Express Mode → Vertex AI migration planning
- **Day 3-4**: Error handling and edge case testing
- **Day 5**: Documentation and deployment preparation

---

## 7. Expected Outcomes

### Performance Improvements
- **40-800x faster** coordination operations
- **Sub-second** file locking and sync
- **Real-time** agent communication
- **Reduced latency** for all session operations

### Precision Improvements
- **Session-scoped** memory prevents pollution
- **Context-aware** searches within project scope
- **Relevant results** for coding tasks
- **Cleaner agent interactions**

### User Experience Benefits
- **Responsive** multi-agent coordination
- **Conflict-free** file editing
- **Synchronized** agent workflows
- **Seamless** collaboration experience
- **Intelligent** long-term knowledge preservation

---

## 8. Next Steps

1. **Set up ADK Express Mode account** (5 minutes)
2. **Create test Agent Engine** (10 minutes)  
3. **Implement basic session coordination** (1-2 hours)
4. **Test with 2 Claude Code agents** (30 minutes)
5. **Benchmark performance improvements** (1 hour)
6. **Plan production migration strategy** (planning session)

---

*This document is designed for iterative refinement. Each section can be independently modified and enhanced as the implementation progresses.*