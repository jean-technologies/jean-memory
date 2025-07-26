# Jean Memory Tool - Current Implementation & Revamp Plan

## 🚨 CRITICAL ARCHITECTURAL SHIFT: Server-Side Orchestration

### Industry Direction: Agentic Memory Systems
The industry is moving toward **server-side agentic orchestration** where:
- **Client tools are thin**: Just send message, receive context
- **Server does the thinking**: All orchestration, memory operations, and intelligence happen server-side
- **Agentic memory**: The system autonomously decides what to remember, search, and return
- **Scalable processing**: Heavy lifting happens on optimized servers, not client machines

---

## FINAL MCP TOOL SIGNATURE

```python
async def jean_memory(
    user_message: str,
    is_new_conversation: bool = False,
    needs_context: bool = True       # Simple escape hatch: does Claude think context would help?
) -> str:
```

### Parameter Definitions

- **`user_message`**: The actual user message/query
- **`is_new_conversation`**: True if this is the start of a new conversation
- **`needs_context`**: Simple boolean - does Claude think context would be helpful for responding?
  - `True`: Server autonomously decides what type/depth of context to provide
  - `False`: Skip context retrieval entirely (but still save memories in background)

### Server-Side Autonomous Intelligence

When `needs_context=True`, the server autonomously decides:
- **Search strategy**: Recent, targeted, comprehensive, or deep analysis
- **Processing depth**: Progressive - start fast, go deeper if needed
- **AI model selection**: Right model for the complexity level
- **Context scope**: What memories and timeframes are relevant

### Specialized Tools Remain Separate

- **`store_document`**: Dedicated tool for document ingestion
- **`add_memory`**: Explicit memory addition
- **`search_memory`**: Direct memory search operations
- **`ask_memory`**: Q&A against existing memories

---

## DETAILED FLOW EXAMPLES

### Example 1: Simple Question (Claude Decides: No Context Needed)
```python
# Client Call
await jean_memory(
    user_message="What's the weather like?",
    is_new_conversation=False,
    needs_context=False  # Claude determined context won't help with weather question
)

# HTTP Request to Server
POST /api/agentic-memory
{
    "message": "What's the weather like?",
    "user_id": "user_123",
    "is_new_conversation": false,
    "needs_context": false
}

# Server Response (Fast Path)
{
    "context": "",
    "processing_time_ms": 45,
    "operations_performed": ["background_memory_save"],
    "memory_saved": true
}
```

### Example 2: Complex Query (Claude Decides: Context Helpful)
```python
# Client Call
await jean_memory(
    user_message="Help me plan my career transition",
    is_new_conversation=True,
    needs_context=True  # Claude determined context would help with career planning
)

# HTTP Request to Server
POST /api/agentic-memory
{
    "message": "Help me plan my career transition",
    "user_id": "user_123", 
    "is_new_conversation": true,
    "needs_context": true
}

# Server Autonomous Analysis
# "Career planning + new conversation + complex query = comprehensive context needed"

# Server Response
{
    "context": "Based on your background in software engineering and your interest in AI/ML that you mentioned 3 months ago, along with your recent completion of the Stanford ML course...",
    "processing_time_ms": 1200,
    "server_decision": "comprehensive_context",
    "reasoning": "Complex life planning query requiring full background synthesis",
    "operations_performed": ["life_narrative_retrieval", "career_context_search", "background_memory_save"],
    "memory_saved": true,
    "model_used": "comprehensive_analysis"
}
```

### Example 3: Contextual Reference (Claude Decides: Context Helpful)
```python
# Client Call
await jean_memory(
    user_message="Let's continue working on the API project we discussed",
    is_new_conversation=False,
    needs_context=True  # Claude determined context needed for "continue working"
)

# HTTP Request to Server
POST /api/agentic-memory
{
    "message": "Let's continue working on the API project we discussed",
    "user_id": "user_123",
    "is_new_conversation": false,
    "needs_context": true
}

# Server Autonomous Analysis  
# "Reference to previous discussion + specific project = targeted search optimal"

# Server Response
{
    "context": "From our discussion 2 days ago: You're building a REST API for user authentication with FastAPI, focusing on JWT implementation and rate limiting...",
    "processing_time_ms": 850,
    "server_decision": "targeted_search",
    "reasoning": "Reference to specific previous project discussion",
    "search_terms": ["API project", "FastAPI", "authentication"],
    "operations_performed": ["targeted_project_search", "recent_context_retrieval", "background_memory_save"],
    "memory_saved": true,
    "model_used": "targeted_search"
}
```

---

## SERVER-SIDE OPERATIONS FLOW

### 1. Request Reception & Simple Routing
```python
@router.post("/api/agentic-memory")
async def process_memory_request(request: MemoryRequest, background_tasks: BackgroundTasks):
    start_time = time.time()
    
    # Always start background memory analysis (non-blocking)
    background_tasks.add_task(analyze_and_save_memory, request.message, request.user_id)
    
    # Simple routing based on Claude's context hint
    if not request.needs_context:
        return MemoryResponse(
            context="", 
            processing_time_ms=(time.time() - start_time) * 1000,
            operations_performed=["background_memory_save"]
        )
    
    # Context needed - let server decide everything else
    return await autonomous_context_orchestration(request)
```

### 2. Autonomous Context Orchestration
```python
async def autonomous_context_orchestration(request: MemoryRequest) -> MemoryResponse:
    start_time = time.time()
    
    # Autonomous decision: what type of context processing is needed?
    context_strategy = await decide_context_strategy(request)
    
    # Execute the chosen strategy
    if context_strategy.type == "recent":
        context = await get_recent_conversation_context(request.user_id, request.message)
        model_used = "recent_lookup"
        
    elif context_strategy.type == "targeted":
        context = await targeted_search_with_terms(
            message=request.message, 
            user_id=request.user_id,
            search_terms=context_strategy.search_terms
        )
        model_used = "targeted_search"
        
    elif context_strategy.type == "comprehensive":
        if request.is_new_conversation:
            # New conversation = life narrative primer
            context = await get_life_narrative(request.user_id)
            model_used = "life_narrative"
        else:
            # Existing conversation = comprehensive synthesis
            context = await comprehensive_context_synthesis(request.message, request.user_id)
            model_used = "comprehensive_synthesis"
            
    elif context_strategy.type == "progressive":
        # Start targeted, go deeper if results insufficient
        context = await progressive_context_retrieval(request.message, request.user_id)
        model_used = "progressive_search"
    
    processing_time = (time.time() - start_time) * 1000
    
    return MemoryResponse(
        context=context,
        processing_time_ms=processing_time,
        server_decision=context_strategy.type,
        reasoning=context_strategy.reasoning,
        search_terms=getattr(context_strategy, 'search_terms', None),
        model_used=model_used,
        operations_performed=get_operations_log()
    )

async def decide_context_strategy(request: MemoryRequest) -> ContextStrategy:
    """Autonomous server-side decision about context strategy"""
    
    analysis_prompt = f"""
    Analyze this message and decide the optimal context retrieval strategy:
    
    Message: "{request.message}"
    New conversation: {request.is_new_conversation}
    
    Strategy options:
    - "recent": References to recent conversations ("we discussed", "earlier", "last time")
    - "targeted": Specific topics/projects (extract search terms)
    - "comprehensive": Complex planning/analysis requiring full background
    - "progressive": Uncertain - start targeted, go deeper if needed
    
    Consider:
    - Message complexity and scope
    - References to previous conversations or specific topics
    - Whether it requires synthesis vs simple lookup
    - New conversation patterns (planning, introductions, complex questions)
    
    Respond with JSON:
    {{
        "type": "recent|targeted|comprehensive|progressive",
        "reasoning": "brief explanation",
        "search_terms": ["optional", "list", "if", "targeted"]
    }}
    """
    
    decision = await claude_analyze(analysis_prompt)
    return ContextStrategy(**decision)
```

### 3. Background Memory Processing (Event-Driven)
```python
# No more 30-second polling! Event-driven processing
async def analyze_and_save_memory(message: str, user_id: str):
    """Autonomous memory analysis and saving - runs immediately"""
    
    # Multi-factor memory analysis
    memory_analysis = await autonomous_memory_analysis(message, user_id)
    
    if memory_analysis.should_save:
        # Save with appropriate categorization
        await save_to_memory_system(
            content=memory_analysis.memorable_content,
            user_id=user_id,
            categories=memory_analysis.categories,
            importance=memory_analysis.importance_score
        )
        
        # Update user profile/context if significant
        if memory_analysis.importance_score > 0.7:
            await update_user_context_profile(memory_analysis.memorable_content, user_id)
    
    # Log for performance tracking
    await log_memory_operation("autonomous_save", memory_analysis.processing_time)

async def autonomous_memory_analysis(message: str, user_id: str) -> MemoryAnalysis:
    """Intelligent analysis of what should be remembered"""
    
    analysis_prompt = f"""
    Analyze this message for memorable content about the user:
    
    Message: "{message}"
    
    Look for:
    - Personal facts (name, location, job, family, background)
    - Preferences, opinions, and values
    - Goals, projects, and aspirations
    - Important events or experiences
    - Skills, interests, and learning
    - Relationships and social context
    - Work context and professional details
    
    Be selective - avoid:
    - Casual remarks or temporary information
    - Simple questions without personal context
    - Generic statements without user-specific details
    
    Respond with JSON:
    {{
        "should_save": bool,
        "memorable_content": "extracted facts if any",
        "categories": ["personal", "professional", "interests", "goals", etc],
        "importance_score": 0.0-1.0,
        "reasoning": "why this should/shouldn't be saved"
    }}
    """
    
    result = await claude_analyze(analysis_prompt)
    return MemoryAnalysis(**result)
```

### 4. Latency Tracking & Optimization
```python
class LatencyTracker:
    def __init__(self):
        self.operation_times = {}
        
    async def track_operation(self, operation: str, func):
        start_time = time.time()
        result = await func()
        end_time = time.time()
        
        latency = (end_time - start_time) * 1000
        self.operation_times[operation] = latency
        
        # Log for analysis
        logger.info(f"⏱️ {operation}: {latency:.2f}ms")
        
        # Auto-optimize if too slow
        if latency > LATENCY_THRESHOLDS[operation]:
            await optimize_operation(operation, latency)
            
        return result
```

---

## IMPLEMENTATION BENEFITS

### ✅ Dramatic Simplification
- **Before**: 1,561 lines of complex client orchestration
- **After**: ~50 lines of thin HTTP client + clean server logic

### ✅ Better Performance
- **Event-driven**: No more 30-second polling waste
- **Smart model selection**: Right tool for the job
- **Background processing**: Non-blocking memory operations

### ✅ Easier Debugging
- **Clear parameters**: Explicit about what's needed
- **Latency tracking**: Built-in bottleneck identification
- **Simple routing**: Easy to trace execution

### ✅ Industry-Aligned Architecture
- **Server-side intelligence**: Where the industry is heading
- **Agentic memory**: System makes autonomous decisions
- **Scalable**: Heavy processing on optimized servers

---

## CAREFUL PHASED IMPLEMENTATION PLAN

⚠️ **CRITICAL**: We must avoid breaking changes. Build incrementally on stable foundation.

### 🔍 ANALYSIS: What We Currently Have Working
- **✅ Stable orchestration**: `app/mcp_orchestration.py` (1,561 lines but WORKS)
- **✅ Working tool**: `jean_memory` in `app/tools/orchestration.py` 
- **✅ Proven background processing**: 30-second polling system
- **✅ All memory tools functioning**: add_memories, search_memory, etc.
- **✅ Claude integration**: Already added to ai_service.py

### 🎯 WHAT WE WANT TO ACHIEVE
Based on the new agentic files, our goal is:
1. **Thinner client**: Simpler jean_memory tool with cleaner parameters
2. **Server-side intelligence**: Move orchestration decision-making to HTTP endpoint
3. **Event-driven processing**: Replace polling with immediate processing
4. **Better performance**: Context strategy decisions by Claude/AI

---

## PHASE 1: ADD ALONGSIDE (No Breaking Changes)
**Goal**: Add new agentic system in parallel, test thoroughly

### 1.1: Server-Side Orchestrator (NEW)
```bash
# ADD: app/routers/agentic_memory.py
```
- **Purpose**: HTTP endpoint `/api/agentic-memory` for server-side orchestration
- **No impact**: Doesn't touch existing jean_memory tool
- **Testing**: Can test via direct HTTP calls first

### 1.2: Event-Driven Memory Service (NEW)
```bash  
# ADD: app/services/event_driven_memory.py
```
- **Purpose**: Queue-based memory processing (replaces 30s polling eventually)
- **No impact**: Runs alongside existing background_processor
- **Testing**: Can verify via queue monitoring

### 1.3: Update Main.py Integration (MINIMAL)
```bash
# MODIFY: main.py (add router + start event service)
```
- **Purpose**: Wire up new `/api/agentic-memory` endpoint
- **Risk**: LOW - just adding new router, not changing existing

### 1.4: Commit Phase 1 & Test
- Verify `/api/agentic-memory` endpoint works
- Verify event-driven service starts without errors
- Existing jean_memory tool still works unchanged

---

## PHASE 2: CREATE ALTERNATIVE CLIENT (Side-by-Side)
**Goal**: New agentic client for testing, existing client untouched

### 2.1: Agentic Client Tool (NEW)
```bash
# ADD: app/tools/jean_memory_v2.py (not jean_memory_agentic.py)
```
- **Purpose**: New `jean_memory_v2` tool with thin HTTP client
- **No impact**: Original `jean_memory` tool remains unchanged
- **Testing**: Can test new tool specifically without affecting production

### 2.2: Add to Tool Registry (MINIMAL)
```bash
# MODIFY: app/tool_registry.py (ADD jean_memory_v2, keep jean_memory)
```
- **Purpose**: Make both tools available
- **Risk**: LOW - just adding, not replacing

### 2.3: Commit Phase 2 & A/B Test
- Both `jean_memory` (old) and `jean_memory_v2` (new) available
- Test new agentic flow thoroughly
- Compare performance and functionality

---

## PHASE 3: GRADUAL TRANSITION (Only After Testing)
**Goal**: Switch default tool only after thorough validation

### 3.1: Performance Validation
- [ ] Latency comparison: old vs new system
- [ ] Memory processing accuracy: ensure no regressions
- [ ] Context quality: verify new system provides equivalent context
- [ ] Error handling: test failure scenarios

### 3.2: Switch Default (ONLY IF Phase 2 succeeds)
```bash
# MODIFY: app/tool_registry.py (change default jean_memory to point to v2)
# KEEP: original as jean_memory_legacy for rollback
```

### 3.3: Deprecate Polling (ONLY IF Event-Driven Proven)
```bash
# MODIFY: main.py (disable 30s background_processor)
# KEEP: Code in place for easy rollback
```

---

## PHASE 4: CLEANUP (Much Later)
**Goal**: Remove old code only after new system proven in production

### 4.1: Archive Old Files (NOT DELETE)
- Move `app/mcp_orchestration.py` to `app/legacy/`
- Move `app/tools/orchestration.py` to `app/legacy/`
- Keep for rollback capability

### 4.2: Performance Monitoring
- Track latency improvements
- Monitor memory processing effectiveness
- User experience metrics

---

## ROLLBACK STRATEGY
At any phase, if issues arise:
1. **Phase 1**: Just disable new router in main.py
2. **Phase 2**: Remove jean_memory_v2 from tool registry
3. **Phase 3**: Switch tool registry back to original jean_memory
4. **Phase 4**: Restore files from legacy folder

---

## SUCCESS CRITERIA FOR EACH PHASE

### Phase 1 Success:
- [ ] `/api/agentic-memory` endpoint responds correctly
- [ ] Event-driven service starts without errors
- [ ] Original jean_memory tool works unchanged
- [ ] No performance degradation

### Phase 2 Success:
- [ ] `jean_memory_v2` provides equivalent context quality
- [ ] HTTP client handles errors gracefully
- [ ] Performance is equal or better than original
- [ ] Memory saving works correctly

### Phase 3 Success:
- [ ] New system handles production load
- [ ] Context strategies work as expected
- [ ] Event-driven processing outperforms polling
- [ ] No user-reported issues

### Phase 4 Success:
- [ ] System runs cleanly without legacy code
- [ ] Performance metrics show improvement
- [ ] Memory usage optimized
- [ ] Maintainability improved

---

## CURRENT STATUS: READY FOR PHASE 1

We have all the code needed for Phase 1. Let's implement server-side orchestrator first, test it thoroughly, then proceed carefully to Phase 2.

**Next Steps**:
1. Add agentic_memory.py router (no breaking changes)
2. Add event_driven_memory.py service (alongside existing)
3. Update main.py to include new router
4. Test `/api/agentic-memory` endpoint thoroughly
5. Only proceed to Phase 2 after validation
