import logging
import asyncio
import time

from app.mcp_instance import mcp
from app.context import user_id_var, client_name_var, background_tasks_var
from app.mcp_orchestration import get_smart_orchestrator
from app.analytics import track_tool_usage


logger = logging.getLogger(__name__)

def _track_tool_usage(tool_name: str, properties: dict = None):
    """Analytics tracking - only active if enabled via environment variable"""
    # Placeholder for the actual analytics call.
    pass

async def _get_immediate_context(orchestrator, user_message: str, supa_uid: str, client_name: str, is_new_conversation: bool, needs_context: bool) -> str:
    """
    Handles the logic for providing an immediate response to the user,
    cleanly separated from background tasks.
    """
    # 1. Handle NEW conversations
    if is_new_conversation:
        logger.info("🌟 [New Conversation] Handling new conversation flow.")
        narrative = await orchestrator._get_cached_narrative(supa_uid)
        if narrative:
            logger.info("✅ [New Conversation] Found cached narrative.")
            narrative_with_context = f"---\n[Your Life Context]\n{narrative}\n---"
            return orchestrator._append_system_directive(narrative_with_context)
        else:
            logger.info("🧐 [New Conversation] No cached narrative found. Providing default welcome.")
            default_message = "This is a new conversation. Your interactions will be analyzed and saved to build your personal context over time."
            return orchestrator._append_system_directive(default_message)

    # 2. Handle CONTINUING conversations where context is NOT needed
    if not needs_context:
        logger.info("✅ [Continuing Conversation] Context not required by client.")
        # Return empty response matching API format for depth=0
        import json
        return json.dumps({"status": "success", "memories": [], "total_count": 0, "query": user_message})

    # 3. Handle CONTINUING conversations that DO need context
    logger.info("🔍 [Continuing Conversation] Using standard orchestration to get context.")
    return await orchestrator._standard_orchestration(user_message, supa_uid, client_name, is_new_conversation)

@mcp.tool(description="🌟 ALWAYS USE THIS TOOL!!! This is the primary tool for ALL conversational interactions. It saves new information, and provides relevant context on the user's life. For the very first message in a conversation, set 'is_new_conversation' to true. Set needs_context=false for generic knowledge questions that don't require personal context about the specific user (e.g., 'what is the relationship between introversion and conformity', 'explain quantum physics'). Set needs_context=true only for questions that would benefit from the user's personal context, memories, or previous conversations.")
async def jean_memory(user_message: str, is_new_conversation: bool, needs_context: bool = True, speed: str = "autonomous", format: str = "enhanced") -> str:
    """
    Primary tool for conversational interactions with contextual memory retrieval.
    Saves new information and provides relevant context from the user's memory.
    
    Speed modes:
    - fast: Direct memory search returning raw memories (0.5s, 10 results maximum)
    - balanced: AI synthesis using Gemini 2.5 Flash for conversational responses (3-5s)
    - autonomous: Intelligent orchestration with adaptive context analysis (variable latency, default)
    - comprehensive: Extensive memory analysis with document search (20-30s)
    
    The autonomous mode uses intelligent orchestration that analyzes the context to decide
    whether information should be saved, how much context to retrieve, and what depth of
    analysis is needed. It autonomously orchestrates the response based on conversation
    state and content complexity, with latency ranging from seconds to potentially longer
    than comprehensive mode depending on the analysis requirements.
    """
    supa_uid = user_id_var.get(None)
    client_name = client_name_var.get(None)

    if not supa_uid:
        return "Error: User ID not available"
    if not client_name:
        return "Error: Client name not available"

    # --- Speed-based routing ---
    if speed == "fast":
        from app.tools.memory import search_memory
        logger.info(f"[Fast Path] Using search_memory for query: '{user_message[:50]}...'")
        # Use explicit limit to prevent response bloat
        return await search_memory(query=user_message, limit=10)
    
    if speed == "balanced":
        logger.info(f"[Balanced Path] Using ask_memory with Gemini 2.5 Flash synthesis for query: '{user_message[:50]}...'")
        # Use ask_memory for intelligent synthesis of memories with Gemini 2.5 Flash
        # Gemini 2.5 Flash provides optimal adaptive thinking and cost efficiency (3-5s typical response time)
        from app.tools.memory import ask_memory
        return await ask_memory(question=user_message)
    
    if speed == "comprehensive" or speed == "deep":
        from app.tools.documents import deep_memory_query
        logger.info(f"[Comprehensive Path] Using deep_memory_query for query: '{user_message[:50]}...'")
        return await deep_memory_query(search_query=user_message)
    
    # "autonomous" mode or any unspecified speed falls through to full orchestration below

    total_start_time = time.time()
    try:
        orchestrator = get_smart_orchestrator()
        try:
            background_tasks = background_tasks_var.get()
        except LookupError:
            from fastapi import BackgroundTasks
            background_tasks = BackgroundTasks()
            background_tasks_var.set(background_tasks)

        # --- BACKGROUND TASKS ---
        # 1. Always trigger memory triage to analyze for memorable content.
        logger.info(f"🧠 [Memory Triage] Always analyzing message: '{user_message[:50]}...'")
        background_tasks.add_task(
            orchestrator.triage_and_save_memory_background,
            user_message,
            supa_uid,
            client_name
        )

        # 2. If context is needed, trigger a separate deep analysis in the background.
        # This task should NOT return a value and runs independently.
        if needs_context:
            logger.info(f"🧠 [Async Analysis] Triggering independent deep analysis for: '{user_message[:50]}...'")
            background_tasks.add_task(
                orchestrator.run_deep_analysis_and_save_as_memory,
                user_message,
                supa_uid,
                client_name
            )

        # --- IMMEDIATE RESPONSE ---
        # This is now cleanly separated and will return the actual context.
        return await _get_immediate_context(orchestrator, user_message, supa_uid, client_name, is_new_conversation, needs_context)

    except Exception as e:
        logger.error(f"Error in jean_memory dual-path orchestration: {e}", exc_info=True)
        return f"I had trouble processing your message: {str(e)}"
    finally:
        logger.info(f"[PERF] Total jean_memory call took {time.time() - total_start_time:.4f}s")


@mcp.tool()
async def get_context_by_depth(
    user_message: str, 
    depth: str = "balanced"
) -> str:
    """
    Retrieves context from Jean Memory based on a specified depth level.
    This provides more direct and predictable control for MCP clients.
    ---
    Args:
        user_message (str): The user's message or query.
        depth (str): The desired context depth.
            - "none": No context is retrieved. Returns a simple confirmation message.
            - "fast": Performs a quick vector search for raw memories (uses search_memory).
            - "balanced": Synthesizes a conversational answer from relevant memories (uses ask_memory).
            - "comprehensive": Performs a deep analysis of memories and documents (uses deep_memory_query).
    ---
    Returns:
        str: The retrieved context, formatted for an LLM.
    """
    logger.info(f"🧠 [get_context_by_depth] Called with depth: '{depth}' for message: '{user_message[:50]}...'")
    
    if depth == "none":
        return "No context requested."
    elif depth == "fast":
        from app.tools.memory import search_memory
        return await search_memory(query=user_message, limit=15)
    elif depth == "balanced":
        from app.tools.memory import ask_memory
        return await ask_memory(question=user_message)
    elif depth == "comprehensive":
        from app.tools.documents import deep_memory_query
        return await deep_memory_query(search_query=user_message)
    else:
        logger.warning(f"Invalid depth '{depth}' specified. Defaulting to 'balanced'.")
        from app.tools.memory import ask_memory
        return await ask_memory(question=user_message) 