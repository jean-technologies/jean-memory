# Jean Memory Context Orchestration Levels
**Version**: 1.0  
**Last Updated**: July 2025  
**Status**: Optimized for Gemini's 1M+ Token Capacity

## Overview

Jean Memory uses **6 distinct orchestration levels** that intelligently choose the right depth of context based on the user's query and conversation state. Each level is optimized for different use cases and leverages Gemini's massive token capacity.

## The 6 Orchestration Levels

### 1. **Fallback Simple Search** (Emergency Only)
**Trigger**: When all other methods fail  
**Model**: None (vector search only)  
**Memories**: 15 memories  
**Documents**: None  
**Display**: Top 3 memories  
**Speed**: < 1 second  
**Use Case**: System errors, emergency fallback  

```python
# Code location: _fallback_simple_search()
search_result = await self._get_tools()['search_memory'](query=user_message, limit=15)
```

---

### 2. **Relevant Context** (Standard Continuing Conversations)
**Trigger**: Continuing conversations with `needs_context=true`  
**Model**: Gemini 2.5 Flash (planning + context selection)  
**Memories**: 100 per search query × multiple queries = **200-400 memories analyzed**  
**Documents**: None  
**Display**: Up to 25 most relevant memories  
**Speed**: 5-15 seconds  
**Use Case**: Standard chat continuation, specific questions  

```python
# Code location: _execute_relevant_context_search()
# AI Planner determines search queries, then:
tasks = [self._get_tools()['search_memory'](query=q, limit=100) for q in search_queries]
```

**Example Triggers**: "What do you know about my work?", "Tell me about my preferences"

---

### 3. **Deep Understanding** (New Conversations)
**Trigger**: `is_new_conversation=true`  
**Model**: Gemini 2.5 Flash (planning + comprehensive synthesis)  
**Memories**: 100 per query × 4 broad queries = **400 memories analyzed**  
**Documents**: None  
**Display**: Up to 50 most relevant pieces, split into primary (25) + secondary (25)  
**Speed**: 10-20 seconds  
**Use Case**: First message in new conversation, user onboarding  

```python
# Code location: _get_deep_understanding_primer()
search_limit = 100  # Use Gemini's 1M+ token capacity
tasks = [self._get_tools()['search_memory'](query=query, limit=search_limit) for query in search_queries]
```

**Queries Used**:
- "personal background values personality traits"  
- "work projects technical expertise professional"
- "current goals interests preferences habits"
- "important experiences thoughts insights"

---

### 4. **Comprehensive Analysis** (Deep Queries)
**Trigger**: AI detects queries like "tell me everything", "comprehensive", "go deeper"  
**Model**: Gemini 2.5 Flash (analysis + categorization)  
**Memories**: 150 per query × multiple queries = **450-600 memories analyzed**  
**Documents**: None  
**Display**: Up to 75 memories, intelligently categorized:
- Professional Background: 25 memories
- Technical Expertise: 20 memories  
- Personal Preferences: 15 memories
- Additional Context: 15 memories  
**Speed**: 15-30 seconds  
**Use Case**: "Tell me everything about X", deep exploration queries  

```python
# Code location: _execute_comprehensive_analysis()
comprehensive_limit = 150  # Gemini can handle massive context
tasks = [self._get_tools()['search_memory'](query=query, limit=comprehensive_limit) for query in search_queries]
```

---

### 5. **Fast Deep Analysis** (Cache Miss Recovery)
**Trigger**: New conversation when narrative cache is empty  
**Model**: Gemini 2.5 Flash (multi-query synthesis)  
**Memories**: 50 per query × 4 queries = **200 memories analyzed**  
**Documents**: None  
**Display**: Rich synthesized narrative (not just raw memories)  
**Speed**: 10-15 seconds  
**Use Case**: Cold start for new users, cache recovery  

```python
# Code location: _fast_deep_analysis()
tasks = [self._get_tools()['search_memory'](query=query, limit=50) for query in search_queries]
# Then Gemini synthesizes into narrative
```

---

### 6. **Deep Memory Query** (Ultra Deep + Documents)
**Trigger**: Background deep analysis, explicit deep queries  
**Model**: Gemini 2.5 Flash (comprehensive analysis)  
**Memories**: **UP TO 500 memories** (default 200, configurable)  
**Documents**: **YES** - up to 100 document chunks  
**Display**: Comprehensive analysis with document integration  
**Speed**: 30-60 seconds  
**Use Case**: Research queries, document analysis, ultimate depth  

```python
# Code location: deep_memory_query() in documents.py
memory_limit = MEMORY_LIMITS.deep_memory_default  # 200 memories
memory_limit = min(max(1, memory_limit), MEMORY_LIMITS.deep_memory_max)  # Up to 500!
chunk_limit = MEMORY_LIMITS.deep_chunk_default    # 50 document chunks  
chunk_limit = min(max(1, chunk_limit), MEMORY_LIMITS.deep_chunk_max)     # Up to 100!
```

## Token Usage & Capacity

### Estimated Token Consumption

| Level | Memories | Docs | Est. Tokens | % of 1M Limit |
|-------|----------|------|-------------|---------------|
| Fallback | 15 | 0 | ~5K | 0.5% |
| Relevant | 200-400 | 0 | ~100-200K | 10-20% |
| Deep Understanding | 400 | 0 | ~200K | 20% |
| Comprehensive | 450-600 | 0 | ~300K | 30% |
| Fast Deep | 200 | 0 | ~150K | 15% |
| **Deep Memory Query** | **500** | **100 chunks** | **~800K** | **80%** |

### Why These Limits Work

- **Gemini 2.5 Flash**: 1M+ token context window
- **Average memory**: ~500 tokens  
- **Document chunk**: ~2K tokens
- **Even at maximum usage (800K tokens), we're still under Gemini's limit**

## Intelligent Selection Logic

The orchestrator chooses levels based on:

### 1. **Conversation State**
```python
if is_new_conversation:
    cached_narrative = await self._get_cached_narrative(user_id)
    if cached_narrative:
        return cached_narrative  # Instant response
    else:
        return await self._fast_deep_analysis()  # Level 5
else:
    return await self._standard_orchestration()  # Levels 2-4
```

### 2. **AI Planning Strategy**
```python
context_strategy = plan.get("context_strategy", "targeted_search")

if context_strategy == "comprehensive_analysis":    # Level 4
    context_task = self._execute_comprehensive_analysis()
elif context_strategy == "deep_understanding":     # Level 3  
    context_task = self._get_deep_understanding_primer()
elif context_strategy == "relevant_context":       # Level 2
    context_task = self._execute_relevant_context_search()
```

### 3. **Background Processing**
```python
# Level 6 triggered in background for deep analysis
background_tasks.add_task(
    orchestrator.run_deep_analysis_and_save_as_memory,
    user_message, user_id, client_name
)
```

## Performance Characteristics

### Response Time Distribution
- **80% of queries**: Levels 1-2 (< 15 seconds)
- **15% of queries**: Levels 3-4 (15-30 seconds)  
- **5% of queries**: Levels 5-6 (30-60 seconds)

### Memory Coverage
- **Level 1**: Minimal (emergency only)
- **Levels 2-3**: Good (200-400 memories)
- **Level 4**: Excellent (450-600 memories)
- **Levels 5-6**: Comprehensive (200-500 memories + documents)

## Configuration

All limits are defined in `app/config/memory_limits.py`:

```python
class MemoryLimits(BaseModel):
    # Deep memory query limits - MASSIVELY INCREASED
    deep_memory_default: int = 200  # Level 6 default
    deep_memory_max: int = 500      # Level 6 maximum
    deep_chunk_default: int = 50    # Document chunks
    deep_chunk_max: int = 100       # Maximum chunks
    
    # Regular search limits - SIGNIFICANTLY INCREASED  
    search_default: int = 50        # Levels 2-5 default
    search_max: int = 100           # Levels 2-5 maximum
```

## Troubleshooting

### "Not getting deep enough context"
- Check if query triggers comprehensive analysis
- Use explicit deep queries: "Tell me everything about X"
- Check if deep_memory_query is being triggered in background

### "Responses too slow"
- Most queries should use Levels 1-2 (< 15s)
- Level 6 (deep memory query) is intentionally slow but comprehensive
- Check narrative caching for new conversations

### "Context seems truncated"  
- Recent optimization increased all limits significantly
- Levels 2-4 now show 25-75 memories instead of 2-8
- Level 6 can access up to 500 memories + 100 document chunks

---

## Recent Optimizations (July 2025)

### Before
- Relevant Context: 12 memories → showed 2
- Deep Understanding: 32 memories → showed 12  
- Comprehensive: 45 memories → showed limited

### After  
- Relevant Context: **400 memories → shows 25**
- Deep Understanding: **400 memories → shows 50**
- Comprehensive: **600 memories → shows 75**
- Deep Memory Query: **500 memories + 100 docs**

**Result**: 10-25x more context while still staying well under Gemini's 1M token limit!