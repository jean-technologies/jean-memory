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

@mcp.tool(description="🌟 ALWAYS USE THIS TOOL FIRST - NEVER use ask_memory, search_memory, or other tools directly. This is the primary tool for ALL conversational interactions. It intelligently engineers context, saves new information, and provides relevant background. For the very first message in a conversation, set 'is_new_conversation' to true. Set needs_context=false for generic knowledge questions that don't require personal context about the specific user (e.g., 'what is the relationship between introversion and conformity', 'explain quantum physics'). Set needs_context=true only for questions that would benefit from the user's personal context, memories, or previous conversations.")
async def jean_memory(user_message: str, is_new_conversation: bool, needs_context: bool) -> str:
    """
    Smart context orchestration combining single-tool simplicity with session-based caching.
    
    This tool:
    1. Uses the 'is_new_conversation' flag from the client to determine conversation state.
    2. Provides a context primer for new chats.
    3. Uses an AI planner for targeted context on continuing chats.
    4. Adds new memorable information in the background.
    
    Args:
        user_message: The user's message or question.
        is_new_conversation: Flag set by the client indicating if this is the first turn.
    
    Returns:
        Enhanced context string with relevant background information.
    """
    supa_uid = user_id_var.get(None)
    client_name = client_name_var.get(None)
    
    if not supa_uid:
        return "Error: User ID not available"
    if not client_name:
        return "Error: Client name not available"
    
    try:
        # Track usage
        track_tool_usage('jean_memory', {
            'message_length': len(user_message),
            'is_new_conversation': is_new_conversation,
            'needs_context': needs_context
        })
        
        # Fast path for requests that don't need context.
        if not needs_context:
            logger.info("⚡️ [Fast Path] needs_context=false, skipping context retrieval.")
            try:
                background_tasks = background_tasks_var.get()
            except LookupError:
                from fastapi import BackgroundTasks
                background_tasks = BackgroundTasks()
                background_tasks_var.set(background_tasks)

            # Still perform intelligent save in the background
            orchestrator = get_smart_orchestrator()
            analysis = await orchestrator._ai_memory_analysis(user_message)
            if analysis.get("should_remember"):
                logger.info(f"💾 [Fast Path] Memorable content found, saving to memory: {analysis.get('content')}")
                background_tasks.add_task(
                    orchestrator._add_memory_background,
                    analysis.get('content'),
                    supa_uid,
                    client_name
                )
            
            return ""
        
        # CRITICAL FIX: Set up background tasks context for orchestration
        try:
            background_tasks = background_tasks_var.get()
        except LookupError:
            # Create a simple background tasks processor if not available
            from fastapi import BackgroundTasks
            background_tasks = BackgroundTasks()
            background_tasks_var.set(background_tasks)
        
        # Try Python 3.11+ asyncio.timeout first, fall back to wait_for for older versions
        try:
            # Python 3.11+ approach (working version)
            async with asyncio.timeout(25): # Increased to 25 seconds for Fast Deep Analysis
                # Get enhanced orchestrator and process
                orchestrator = get_smart_orchestrator()
                enhanced_context = await orchestrator.orchestrate_smart_context(
                    user_message=user_message,
                    user_id=supa_uid,
                    client_name=client_name,
                    is_new_conversation=is_new_conversation,
                    background_tasks=background_tasks
                )
                return enhanced_context
        except AttributeError:
            # Python < 3.11 fallback
            logger.info("Using asyncio.wait_for fallback for Python < 3.11")
            async def _orchestrate():
                orchestrator = get_smart_orchestrator()
                return await orchestrator.orchestrate_smart_context(
                    user_message=user_message,
                    user_id=supa_uid,
                    client_name=client_name,
                    is_new_conversation=is_new_conversation,
                    background_tasks=background_tasks
                )
            
            result = await asyncio.wait_for(_orchestrate(), timeout=25.0)
            return result

    except asyncio.TimeoutError:
        logger.warning(f"Jean Memory context timed out for user {supa_uid}. Falling back to simple search.")
        try:
            # Fallback to a simple, reliable search
            fallback_result = await search_memory(query=user_message, limit=5)
            return f"I had trouble with my advanced context analysis, but here are some relevant memories I found:\n{fallback_result}"
        except Exception as fallback_e:
            logger.error(f"Error in jean_memory fallback search: {fallback_e}", exc_info=True)
            return "My apologies, I had trouble processing your request and the fallback search also failed."

    except Exception as e:
        logger.error(f"Error in jean_memory: {e}", exc_info=True)
        return f"I had trouble processing your message: {str(e)}" 