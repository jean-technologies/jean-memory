import logging
import asyncio

from app.mcp_instance import mcp
from app.context import user_id_var, client_name_var, background_tasks_var
from app.mcp_orchestration import get_smart_orchestrator
from app.tools.memory import search_memory
from app.analytics import track_tool_usage


logger = logging.getLogger(__name__)

def _track_tool_usage(tool_name: str, properties: dict = None):
    """Analytics tracking - only active if enabled via environment variable"""
    # Placeholder for the actual analytics call.
    pass

@mcp.tool(description="🌟 ALWAYS USE THIS TOOL!!! This is the primary tool for ALL conversational interactions. It saves new information, and provides relevant context on the user's life. For the very first message in a conversation, set 'is_new_conversation' to true. Set needs_context=false for generic knowledge questions that don't require personal context about the specific user (e.g., 'what is the relationship between introversion and conformity', 'explain quantum physics'). Set needs_context=true only for questions that would benefit from the user's personal context, memories, or previous conversations.")
async def jean_memory(user_message: str, is_new_conversation: bool, needs_context: bool) -> str:
    """
    Asynchronous, dual-path orchestration. Provides a fast search result immediately
    while triggering intelligent, asynchronous memory analysis and saving in the background.
    """
    supa_uid = user_id_var.get(None)
    client_name = client_name_var.get(None)

    if not supa_uid:
        return "Error: User ID not available"
    if not client_name:
        return "Error: Client name not available"

    try:
        orchestrator = get_smart_orchestrator()
        try:
            background_tasks = background_tasks_var.get()
        except LookupError:
            from fastapi import BackgroundTasks
            background_tasks = BackgroundTasks()
            background_tasks_var.set(background_tasks)

        # --- ASYNCHRONOUS ACTIONS ---

        # 1. Trigger background task for intelligent triage and selective saving.
        # This happens for every message to ensure we capture all salient info.
        logger.info(f"🧠 [Async Triage] Triggering analysis to determine if message is memorable: '{user_message[:50]}...'")
        background_tasks.add_task(
            orchestrator.triage_and_save_memory_background,
            user_message,
            supa_uid,
            client_name
        )

        # 2. If context is needed, also trigger the separate deep analysis background task.
        if needs_context:
            logger.info(f"🧠 [Async Analysis] Triggering deep analysis for: '{user_message[:50]}...'")
            background_tasks.add_task(
                orchestrator.run_deep_analysis_and_save_as_memory,
                user_message,
                supa_uid,
                client_name
            )

        # --- IMMEDIATE RESPONSE ---

        # 3. If no context is needed by the client, we can return a standard message.
        if not needs_context:
            return "Context is not required for this query. The user's message will be analyzed for important information in the background."

        # 4. For context-aware requests, perform a fast, simple search for an immediate response.
        logger.info(f"⚡️ [Fast Path] Performing simple search for immediate response.")
        fast_context = await orchestrator._fallback_simple_search(user_message, supa_uid)
        
        # 5. Return the fast context to the user.
        return fast_context

    except Exception as e:
        logger.error(f"Error in jean_memory dual-path orchestration: {e}", exc_info=True)
        return f"I had trouble processing your message: {str(e)}" 