# Pure AI Orchestration Planning Document

## Context & Current State

After implementing a "pure AI" approach to replace hardcoded heuristics in the Jean Memory orchestration system, we experienced catastrophic performance failures (21+ seconds for simple greetings). This document plans a better approach.

## What Was Attempted (Reverted)

### Changes Made (Commit 46fcdc90)
- **Replaced heuristic-based context checks** with `_ai_context_relevance_check()` using Gemini Flash
- **Replaced keyword-based memory saving** with `_ai_should_save_memory()` using AI decisions  
- **Replaced keyword-based quality filtering** with `_ai_evaluate_context_quality()` using AI evaluation
- **Updated main orchestration flow** to use these AI methods throughout

### The "Bitter Lesson" Philosophy Applied
The approach was based on the "bitter lesson" - that leveraging general intelligence (AI) rather than hardcoded rules leads to better long-term performance. This is theoretically sound but had implementation issues.

## Catastrophic Failure Analysis

### What Went Wrong (From Logs)
```
2025-07-21 04:42:52,025 - app.mcp_orchestration - INFO - 🎯 [AI Filter] Context not relevant enough in 21.38s
```

**User Query:** "whats up" 
**Expected:** Fast rejection (< 2s) with no context
**Actual:** 21.38s processing with database failures

### Failure Chain Analysis
1. **AI Context Check FAILED** - Should have rejected "whats up" immediately, but incorrectly decided context was needed
2. **Vector Search Triggered** (3.36s) - Found 12 results with low confidence (max score: 0.41)  
3. **Deep Search Triggered** - Low confidence scores triggered expensive deep search
4. **PostgreSQL Failures** - `plainto_tsquery` function doesn't exist, causing transaction aborts
5. **AI Quality Filter Still Ran** - Even with no context found, AI still processed for more time
6. **Total Failure** - 21s with no useful output

## Root Cause Analysis

### Issue #1: AI Prompt Quality
The AI prompts for context relevance were not sufficiently aggressive about rejecting simple greetings:

```python
# FAILED PROMPT (too permissive):
"""You are an intelligent context engine. Decide if this user message would benefit from personal context...

Be intelligent about edge cases. "hey" might be a greeting OR the start of a deeper conversation."""
```

**Problem:** The "edge cases" instruction made AI too permissive for simple greetings.

### Issue #2: Infrastructure Dependencies  
The pure AI approach still depended on the same broken infrastructure:
- PostgreSQL full-text search (`plainto_tsquery` missing)
- Vector search with confidence thresholds triggering expensive deep search
- No circuit breakers or timeouts on AI calls

### Issue #3: Performance vs Intelligence Tradeoff
- **Heuristics:** < 1ms decision time, 95% accuracy for obvious cases
- **AI Calls:** 1-3s decision time, potentially higher accuracy for edge cases
- **Failure Mode:** AI calls can fail/timeout, heuristics cannot

## Lessons Learned

### The "Bitter Lesson" Reconsidered
While the bitter lesson advocates for general intelligence over hardcoded approaches, it doesn't mean we should:
1. **Abandon fast paths entirely** - Simple greetings should still have < 1ms rejection
2. **Replace all heuristics blindly** - Some patterns (like "hi", "thanks", "ok") are genuinely obvious
3. **Ignore performance constraints** - 21s response time for "whats up" is unacceptable

### Better Hybrid Architecture Principles
1. **Fast Path First** - Ultra-fast heuristics for obvious cases (greetings, simple acknowledgments)
2. **AI for Ambiguity** - Use AI intelligence only for genuinely ambiguous cases
3. **Circuit Breakers** - AI calls must have timeouts and fallbacks
4. **Infrastructure Independence** - Don't let AI improvements depend on broken database functions

## Proposed Solution: Hybrid Intelligence Architecture

### Stage 1: Lightning Fast Filter (< 1ms)
```python
def _lightning_fast_reject(user_message: str) -> tuple[bool, str]:
    """Ultra-fast rejection for obvious cases"""
    message = user_message.lower().strip()
    
    # Definite rejections (< 1ms)
    simple_greetings = {"hi", "hello", "hey", "yo", "sup", "whats up", "what's up"}
    simple_responses = {"ok", "thanks", "thank you", "got it", "cool", "nice"}
    
    if message in simple_greetings:
        return False, "greeting_fast_path"
    if message in simple_responses:
        return False, "response_fast_path"
    if len(message) < 3:
        return False, "too_short_fast_path"
    
    # Pass to AI for ambiguous cases
    return None, "needs_ai_evaluation"
```

### Stage 2: AI Intelligence Layer (1-3s)
```python
async def _ai_context_relevance_check(user_message: str) -> tuple[bool, str]:
    """AI evaluation for ambiguous cases only"""
    try:
        # More aggressive prompt for edge cases
        prompt = f"""STRICT EVALUATION: Does this message need personal context?

MESSAGE: "{user_message}"

CONTEXT NEEDED ONLY IF:
- Explicit reference to personal info, past conversations, or user's work/projects
- Questions that would benefit from knowing WHO the user is
- Requests for personalized advice

NO CONTEXT FOR:
- Generic questions about the world, definitions, facts
- Casual conversation that works without knowing the person
- ANY greeting or social pleasantry (be strict here)

Respond: CONTEXT or NO_CONTEXT"""
        
        response = await asyncio.wait_for(
            self._get_gemini().generate_response(prompt),
            timeout=2.0  # Hard timeout
        )
        return "CONTEXT" in response.upper(), "ai_evaluation"
    except:
        return False, "ai_failed_default_no_context"
```

### Stage 3: Integrated Flow
```python
async def orchestrate_smart_context(self, user_message: str, ...) -> str:
    # Stage 1: Lightning fast rejection
    fast_result, reason = self._lightning_fast_reject(user_message)
    if fast_result is not None:
        if not fast_result:
            logger.info(f"⚡ [FAST REJECT] {reason} in < 1ms")
            return ""
        # If fast_result is True, continue to full orchestration
    
    # Stage 2: AI evaluation for ambiguous cases
    needs_context, ai_reason = await self._ai_context_relevance_check(user_message)
    if not needs_context:
        logger.info(f"🤖 [AI REJECT] {ai_reason} in 1-3s")  
        return ""
    
    # Stage 3: Full orchestration (only for messages that truly need context)
    return await self._full_orchestration(user_message, ...)
```

## Implementation Plan

### Phase 1: Fix Infrastructure (Immediate)
1. **Fix PostgreSQL Issues** - Either fix `plainto_tsquery` or disable deep search
2. **Add Circuit Breakers** - Timeout all AI calls at 3s max
3. **Add Graceful Fallbacks** - Use vector results when deep search fails

### Phase 2: Implement Hybrid Architecture (1-2 days)
1. **Add Lightning Fast Filter** - Handle obvious cases in < 1ms
2. **Refine AI Prompts** - More aggressive rejection of simple cases
3. **Add Comprehensive Logging** - Track performance at each stage

### Phase 3: Optimize & Monitor (Ongoing)
1. **Performance Monitoring** - Track fast path vs AI path usage
2. **Continuous Prompt Tuning** - Based on production patterns
3. **Expand Fast Path** - Add more obvious patterns as they're discovered

## Success Metrics

### Performance Targets
- **Simple Greetings:** < 100ms total response time
- **Ambiguous Cases:** < 3s with AI evaluation  
- **Complex Context:** < 15s with full orchestration
- **Error Rate:** < 1% AI call failures

### Quality Targets
- **Fast Path Accuracy:** 99%+ for obvious cases
- **AI Path Accuracy:** 95%+ for ambiguous cases
- **User Experience:** No more 20s+ responses for simple queries

## Files to Modify

### Primary Changes
- `app/mcp_orchestration.py` - Implement hybrid architecture
- `app/tools/orchestration.py` - Update jean_memory tool calls
- `app/utils/gemini.py` - Add timeout handling

### Infrastructure Fixes  
- Database migration scripts - Fix `plainto_tsquery` issues
- `app/tools/memory_modules/chunk_search.py` - Add fallbacks
- Performance monitoring and logging enhancements

## Testing Strategy

### Unit Tests
- Fast path accuracy for common greetings
- AI prompt effectiveness on ambiguous cases
- Circuit breaker and timeout behavior

### Integration Tests  
- End-to-end response times for different message types
- Fallback behavior when AI calls fail
- Database error handling

### Production Monitoring
- Response time distributions by message type
- Fast path vs AI path usage ratios  
- Error rates and fallback usage

## Risk Mitigation

### Rollback Plan
- Current working version is now at commit `476189c3`
- Can revert any hybrid changes quickly if needed
- Keep performance monitoring to detect regressions

### Performance Safety
- Hard timeouts on all AI calls (3s max)
- Fast path handles 80%+ of simple cases
- Graceful degradation when services fail

## Conclusion

The pure AI approach taught us valuable lessons about the limits of replacing all heuristics with intelligence. The hybrid architecture proposed here combines the best of both:
- **Lightning fast heuristics** for obvious cases (bitter lesson doesn't apply here)
- **AI intelligence** for genuinely ambiguous situations (bitter lesson applies here)
- **Robust infrastructure** that doesn't depend on perfect AI performance

This approach should deliver the intelligent behavior we want while maintaining the performance users expect.

## Addendum: Revised "Pure AI" Plan for Ongoing Conversations

After further review, and to adhere more strictly to the "bitter lesson" philosophy, the hybrid approach's hard-coded `_lightning_fast_reject` filter will be abandoned. Instead, we will use a multi-stage AI process that leverages the speed of Gemini Flash to create an intelligent, purely AI-driven filtering and planning system for ongoing conversations.

This revised architecture replaces the "Standard Orchestration" path.

### Guiding Principle: No Hard-Coded Filters

We will not maintain a list of keywords like "hi" or "thanks". Instead, we trust a well-prompted AI to make a better, more context-aware decision about whether a message is simple conversational filler or the start of a meaningful query.

### Proposed Architecture: Two-Stage AI Gateway

#### Stage 1: AI Relevance Gate (Target: <2s)

The first step for any ongoing conversation message is a fast, cheap call to Gemini Flash with a very strict prompt.

-   **Purpose:** Answer one question: "Is personal context helpful for this message?"
-   **Input:** User's message.
-   **Output:** A simple `YES` or `NO`.
-   **Logic:** If `NO`, the process stops, and an empty context is returned immediately. This efficiently handles generic questions ("what's the weather?") and conversational filler ("lol," "cool") without engaging deeper systems.

```python
# Prompt for AI Relevance Gate
prompt = f"""You are an ultra-efficient AI assistant. Your only job is to decide if retrieving personal context would be helpful for responding to the user's message.

USER MESSAGE: "{user_message}"

Answer only with YES or NO.

- Answer NO for simple greetings, acknowledgments, or generic questions where user identity is irrelevant (e.g., "what is 2+2?", "thanks!", "got it").
- Answer YES if the message implies a need for personal memory, asks a question that could be personalized, or references past events.

Your Answer (YES or NO):"""
```

#### Stage 2: AI Planner & Strategist (Target: <2s)

This stage only runs if the AI Relevance Gate returns `YES`. A second, more detailed Gemini Flash call creates a complete execution plan.

-   **Purpose:** Decide *how* to act on the message.
-   **Input:** User's message.
-   **Output:** A structured JSON object containing the execution plan.

```json
{
  "should_save_memory": true,
  "memorable_content": "User is starting a new project focused on Rust.",
  "retrieval_strategy": "shallow_search",
  "search_queries": [
    "user's experience with Rust programming",
    "user's recent side projects"
  ]
}
```

-   `should_save_memory`: Determines if the message contains new, lasting information.
-   `memorable_content`: The distilled information to be saved.
-   `retrieval_strategy`: The right tool for the job. Can be `shallow_search` (for `search_memory`) or `deep_analysis` (for `deep_memory_query`).
-   `search_queries`: A list of precise, targeted queries to be fed into the retrieval tools.

#### Stage 3: Parallel Execution

With the plan from the AI Planner, the system executes two tasks concurrently:

1.  **Save Memory (Background Task):** If `should_save_memory` is true, the `memorable_content` is passed to a background task using `add_memories`. This ensures that saving new information never blocks the user from getting a fast response.
2.  **Retrieve Context (Foreground Task):** The system uses the `retrieval_strategy` and `search_queries` to fetch the relevant context using either `search_memory` or `deep_memory_query`.

### Implementation Plan Update

The implementation will focus on `app/mcp_orchestration.py` and `app/utils/mcp_modules/ai_service.py`.

1.  **Modify `_standard_orchestration`:** This function will be rewritten to implement the two-stage AI gate and planner logic.
2.  **Create `_ai_context_relevance_gate`:** A new method in `ai_service.py` to handle the first YES/NO check.
3.  **Refactor `_ai_create_context_plan`:** Update this method in `ai_service.py` to become the AI Planner, returning the structured JSON plan.
4.  **Remove Fast Filter:** Ensure no hard-coded keyword filtering remains in the orchestration path.
5.  **Update Execution Logic:** The orchestrator will use the plan's output to dynamically call the correct memory-saving and context-retrieval functions.