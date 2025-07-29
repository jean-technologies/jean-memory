# Jean Memory Performance Testing & Optimization Plan

## Immediate Priority: Fix Memory Saving (CRITICAL)

### The Problem
```bash
❌ [BG Add Memory] Failed: cannot import name 'user_id_var' from 'app.mcp_server'
```

### The Fix Applied
```python
# Changed line 831 in mcp_orchestration.py:
from app.context import user_id_var, client_name_var  # was: app.mcp_server
```

**Deploy this fix immediately** - it's blocking all memory saving in production.

## Performance Analysis from Production Logs

### AI Planning Bottleneck (9+ seconds average)
From your logs:
- Call 1: `⏰ AI planner timed out after 12s, using fallback`
- Call 2: `AI Plan Creation took 6.7409s` 
- Call 3: `AI Plan Creation took 9.1965s`

**This is the real performance issue** - not the search operations.

### Search Performance (Actually Good)
- `Search completed in 2.99s, found 12 results`
- `Search completed in 2.48s, found 12 results`
- `Search completed in 2.27s, found 12 results`

**Search is fast** - average 2.6 seconds.

## Proposed Performance Testing Framework

### Test 1: LLM Performance Comparison (Data-Driven)

```python
#!/usr/bin/env python3
"""
LLM Performance Testing for Jean Memory AI Planning
Tests actual response times for context planning prompts
"""

import asyncio
import time
import statistics
from typing import List, Dict

async def test_ai_planning_performance():
    """Test actual LLM performance for context planning"""
    
    test_messages = [
        "can you remember that i have brown hair and brown eyes",
        "what's going on here - looking at Jean Memory API logs",
        "Help me plan my career transition",
        "Continue working on the Python API we discussed",
        "Debug this memory storage issue"
    ]
    
    results = {
        'gemini_flash': [],
        'claude_haiku': [],
        'openai_3.5_turbo': []
    }
    
    # Test each LLM with same prompts
    for message in test_messages:
        print(f"\n🧪 Testing: '{message[:50]}...'")
        
        # Test Gemini Flash (current)
        start_time = time.time()
        gemini_result = await test_gemini_flash_planning(message)
        gemini_time = time.time() - start_time
        results['gemini_flash'].append(gemini_time)
        print(f"  Gemini Flash: {gemini_time:.2f}s")
        
        # Test Claude Haiku
        start_time = time.time()
        claude_result = await test_claude_haiku_planning(message)
        claude_time = time.time() - start_time
        results['claude_haiku'].append(claude_time)
        print(f"  Claude Haiku: {claude_time:.2f}s")
        
        # Test OpenAI GPT-3.5-turbo
        start_time = time.time()
        openai_result = await test_openai_planning(message)
        openai_time = time.time() - start_time
        results['openai_3.5_turbo'].append(openai_time)
        print(f"  OpenAI 3.5-turbo: {openai_time:.2f}s")
        
        await asyncio.sleep(1)  # Rate limiting
    
    # Calculate statistics
    print("\n📊 PERFORMANCE RESULTS:")
    for model, times in results.items():
        avg_time = statistics.mean(times)
        median_time = statistics.median(times)
        min_time = min(times)
        max_time = max(times)
        
        print(f"\n{model.upper()}:")
        print(f"  Average: {avg_time:.2f}s")
        print(f"  Median:  {median_time:.2f}s") 
        print(f"  Range:   {min_time:.2f}s - {max_time:.2f}s")
        
        # Calculate improvement potential
        current_avg = statistics.mean(results['gemini_flash'])
        if model != 'gemini_flash':
            improvement = ((current_avg - avg_time) / current_avg) * 100
            if improvement > 0:
                print(f"  🚀 {improvement:.1f}% faster than Gemini Flash")
            else:
                print(f"  🐌 {abs(improvement):.1f}% slower than Gemini Flash")
    
    return results

async def test_gemini_flash_planning(message: str) -> dict:
    """Test Gemini Flash with actual context planning prompt"""
    from app.utils.gemini import gemini_generate_response
    
    prompt = f"""
    Analyze this user message for optimal context retrieval strategy:
    Message: "{message}"
    
    Create targeted search terms that will find the MOST RELEVANT memories.
    
    Return JSON:
    {{
        "context_strategy": "relevant_context|recent_context|comprehensive_context",
        "search_queries": ["term1", "term2", "term3"],
        "should_save_memory": true/false,
        "memorable_content": "extracted facts if should_save_memory is true"
    }}
    """
    
    return await gemini_generate_response(prompt, format_type="text")

async def test_claude_haiku_planning(message: str) -> dict:
    """Test Claude Haiku with same prompt"""
    import httpx
    
    prompt = f"""
    Analyze this user message for optimal context retrieval strategy:
    Message: "{message}"
    
    Create targeted search terms that will find the MOST RELEVANT memories.
    
    Return JSON:
    {{
        "context_strategy": "relevant_context|recent_context|comprehensive_context", 
        "search_queries": ["term1", "term2", "term3"],
        "should_save_memory": true/false,
        "memorable_content": "extracted facts if should_save_memory is true"
    }}
    """
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": os.getenv("ANTHROPIC_API_KEY"),
                "content-type": "application/json",
                "anthropic-version": "2023-06-01"
            },
            json={
                "model": "claude-3-haiku-20240307",
                "max_tokens": 500,
                "messages": [{"role": "user", "content": prompt}]
            }
        )
        return response.json()

async def test_openai_planning(message: str) -> dict:
    """Test OpenAI GPT-3.5-turbo with same prompt"""
    import openai
    
    prompt = f"""
    Analyze this user message for optimal context retrieval strategy:
    Message: "{message}"
    
    Create targeted search terms that will find the MOST RELEVANT memories.
    
    Return JSON:
    {{
        "context_strategy": "relevant_context|recent_context|comprehensive_context",
        "search_queries": ["term1", "term2", "term3"], 
        "should_save_memory": true/false,
        "memorable_content": "extracted facts if should_save_memory is true"
    }}
    """
    
    client = openai.AsyncOpenAI()
    response = await client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=500
    )
    return response.choices[0].message.content

if __name__ == "__main__":
    asyncio.run(test_ai_planning_performance())
```

### Test 2: End-to-End Performance Testing

```python
#!/usr/bin/env python3
"""
End-to-end performance testing for different optimization strategies
"""

import asyncio
import time
from typing import List, Tuple

async def test_optimization_strategies():
    """Test different optimization approaches"""
    
    test_cases = [
        ("Quick context", "What's the weather?", False),
        ("Personal context", "Help me with my Python project", True),
        ("Complex planning", "Help me plan my career transition", True)
    ]
    
    strategies = {
        'current': test_current_implementation,
        'parallel_search': test_parallel_search,  
        'cached_context': test_cached_context,
        'faster_llm': test_faster_llm
    }
    
    results = {}
    
    for strategy_name, strategy_func in strategies.items():
        print(f"\n🧪 Testing {strategy_name.upper()} strategy:")
        strategy_results = []
        
        for test_name, message, needs_context in test_cases:
            start_time = time.time()
            
            try:
                context = await strategy_func(message, needs_context)
                response_time = time.time() - start_time
                strategy_results.append((test_name, response_time, len(context)))
                print(f"  {test_name}: {response_time:.2f}s ({len(context)} chars)")
                
            except Exception as e:
                print(f"  {test_name}: FAILED - {e}")
                strategy_results.append((test_name, 999, 0))
        
        results[strategy_name] = strategy_results
    
    # Compare results
    print("\n📊 OPTIMIZATION COMPARISON:")
    for i, (test_name, _, _) in enumerate(test_cases):
        print(f"\n{test_name}:")
        baseline = results['current'][i][1]  # Current implementation time
        
        for strategy in strategies.keys():
            time_taken = results[strategy][i][1]
            if time_taken < 999:  # Not failed
                improvement = ((baseline - time_taken) / baseline) * 100
                if improvement > 0:
                    print(f"  {strategy:15}: {time_taken:.2f}s (🚀 {improvement:.1f}% faster)")
                else:
                    print(f"  {strategy:15}: {time_taken:.2f}s (🐌 {abs(improvement):.1f}% slower)")
            else:
                print(f"  {strategy:15}: FAILED")

async def test_current_implementation(message: str, needs_context: bool) -> str:
    """Test current jean_memory implementation"""
    # This would call the actual jean_memory function
    pass

async def test_parallel_search(message: str, needs_context: bool) -> str:
    """Test with parallel vector + graph search"""
    if not needs_context:
        return ""
    
    # Simulate parallel searches
    vector_task = asyncio.create_task(simulate_vector_search(message))
    graph_task = asyncio.create_task(simulate_graph_search(message))
    
    vector_results, graph_results = await asyncio.gather(vector_task, graph_task)
    return merge_search_results(vector_results, graph_results)

async def test_cached_context(message: str, needs_context: bool) -> str:
    """Test with context caching"""
    cache_key = f"context_{hash(message)}"
    
    # Simulate cache lookup
    cached = await get_cached_context(cache_key)
    if cached:
        return cached
    
    # Generate and cache
    context = await generate_context(message, needs_context)
    await cache_context(cache_key, context)
    return context

async def test_faster_llm(message: str, needs_context: bool) -> str:
    """Test with faster LLM for planning"""
    if not needs_context:
        return ""
    
    # Use faster LLM for planning (based on test results)
    plan = await fast_llm_planning(message)  # Claude Haiku or fastest from Test 1
    context = await execute_search_plan(plan)
    return context

# Helper functions
async def simulate_vector_search(query: str) -> List[str]:
    await asyncio.sleep(1.2)  # Simulate vector search time
    return ["vector result 1", "vector result 2"]

async def simulate_graph_search(query: str) -> List[str]:
    await asyncio.sleep(0.8)  # Simulate graph search time  
    return ["graph result 1", "graph result 2"]

def merge_search_results(vector: List[str], graph: List[str]) -> str:
    return " | ".join(vector + graph)

if __name__ == "__main__":
    asyncio.run(test_optimization_strategies())
```

## Immediate Action Plan

### 1. Deploy Import Fix (CRITICAL - 5 minutes)
```bash
# Deploy the context import fix immediately
git add openmemory/api/app/mcp_orchestration.py
git commit -m "fix: correct import path for context variables in background memory saving"
git push
```

### 2. Run Performance Tests (1-2 hours)
```bash
# Run the LLM comparison test
python performance_tests/test_llm_performance.py

# Run the optimization strategy test  
python performance_tests/test_optimization_strategies.py
```

### 3. Implement Based on Data (Data-driven decisions)
Only after we have real performance data should we make LLM changes.

## Documentation Strategy

Let's create a performance tracking system:

```python
# Add to your existing logging
class PerformanceTracker:
    def __init__(self):
        self.metrics = {}
    
    async def track_operation(self, operation: str, func, *args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            success = True
            error = None
        except Exception as e:
            result = None
            success = False
            error = str(e)
        
        duration = time.time() - start_time
        
        # Log structured performance data
        perf_data = {
            "operation": operation,
            "duration_ms": duration * 1000,
            "success": success, 
            "error": error,
            "timestamp": time.time()
        }
        
        logger.info(f"[PERF_METRIC] {json.dumps(perf_data)}")
        return result

# Usage in jean_memory:
perf_tracker = PerformanceTracker()

async def jean_memory_with_tracking(user_message, is_new_conversation, needs_context):
    # Track AI planning
    plan = await perf_tracker.track_operation(
        "ai_context_planning",
        ai_create_context_plan,
        user_message
    )
    
    # Track memory search  
    results = await perf_tracker.track_operation(
        "memory_search",
        execute_search_plan,
        plan
    )
    
    return format_context(results)
```

## Bottom Line

1. **Fix the import error immediately** - memory saving is completely broken
2. **Run actual performance tests** before making LLM changes 
3. **Document with real metrics** rather than assumptions
4. **Only optimize based on data** - don't guess at performance improvements

Your logs show the real bottleneck is AI planning (9+ seconds), not search (2.6 seconds). Let's measure different LLMs objectively before switching.