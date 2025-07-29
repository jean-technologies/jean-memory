# Jean Memory Flow Analysis

## Current State (Working Commit 1eb28fc0)

### Flow Analysis

#### When `needs_context=true` (Continuing conversations that need context):
1. **Main Tool Call**: `jean_memory()` in `orchestration.py`
2. **Background Task**: `run_deep_analysis_and_save_as_memory()` is triggered
3. **Memory Saving**: The background task calls `_standard_orchestration()` which handles memory saving through `_handle_background_memory_saving_from_plan()`
4. **Result**: Context is returned + memory is saved in background

#### When `needs_context=false` (Generic knowledge questions):
1. **Main Tool Call**: `jean_memory()` in `orchestration.py`  
2. **No Background Task**: No background task is triggered
3. **Memory Saving**: **NONE** - No memory saving happens at all
4. **Result**: Simple message returned, no memory saved

#### When `is_new_conversation=true`:
1. **Main Tool Call**: `jean_memory()` in `orchestration.py`
2. **Cached Narrative Check**: Attempts to get cached narrative
3. **Memory Saving**: **NONE** - No memory saving for new conversations
4. **Result**: Cached narrative or welcome message

## The Problem

**Root Issue**: Memory saving only happens when `needs_context=true` AND it's not a new conversation. This means:

- ❌ `needs_context=false` → No memory saved (messages like "I have a blue shirt")
- ❌ `is_new_conversation=true` → No memory saved (first messages with personal info)
- ✅ `needs_context=true` + continuing conversation → Memory saved

## The Previous "Fix" Problem

The deduplication logic I added was trying to solve the wrong problem. The issue wasn't duplicate saves - it was **missing saves**.

## The Real Solution

We need to **decouple memory saving from context retrieval**. Memory saving should happen for ALL messages that contain memorable content, regardless of whether context is needed.

### Proposed Architecture:

```
Every jean_memory() call:
├── ALWAYS: Check if message is memorable → Save if yes
├── IF is_new_conversation=true → Return cached narrative or welcome
├── IF needs_context=false → Return simple response  
└── IF needs_context=true → Run context orchestration + return context
```

### Implementation Plan:

1. **Add universal memory triage**: Every call to `jean_memory()` should trigger memory analysis
2. **Keep existing flows**: Don't break the context retrieval logic that's working
3. **Use proper deduplication**: Only prevent the same exact memory content from being saved multiple times
4. **Maintain performance**: Memory saving should be asynchronous/background

## Key Changes Needed:

1. **In `orchestration.py`**: Add memory triage to the "Always Triggered" section
2. **Memory triage function**: Should use AI to determine if content is memorable
3. **Deduplication**: Should be based on content hash, not interaction hash
4. **Background task management**: Ensure memory saving doesn't block responses

## Solution Implemented:

### ✅ Universal Memory Triage
- **Every call** to `jean_memory()` now triggers `triage_and_save_memory_background`
- Decouples memory saving from context retrieval completely
- Uses AI analysis to determine if content is memorable before saving

### ✅ Content-Based Deduplication  
- Replaced problematic interaction-based deduplication with content-based approach
- Generates hash of the **actual content that would be saved** (not the raw message)
- Prevents saving identical content multiple times while allowing different processed versions
- Shared deduplication tracking across all memory saving flows

### ✅ Preserved Existing Flows
- Context retrieval logic unchanged and still working
- Orchestration flows can still save memories (with deduplication)
- Background analysis still works
- Narrative caching still works

## Expected Behavior After Fix:

- ✅ "I have a blue shirt" (needs_context=false) → Memory saved via universal triage
- ✅ "Hi, I'm John" (is_new_conversation=true) → Memory saved via universal triage  
- ✅ "What's my eye color?" (needs_context=true) → Memory saved + context returned
- ✅ No duplicate memories from identical content
- ✅ All existing context retrieval continues to work
- ✅ Multiple flows can save different processed versions of the same message

## Key Files Changed:

1. **`orchestration.py`**: Added universal memory triage to "Always Triggered" section
2. **`mcp_orchestration.py`**: 
   - Replaced `_processed_interactions` with `_saved_content_hashes`
   - Updated `_add_memory_with_deduplication` → `_add_memory_with_content_deduplication`
   - Enhanced `triage_and_save_memory_background` with content deduplication
   - Updated all function calls to use new deduplication method