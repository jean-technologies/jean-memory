import logging
import asyncio
import time

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

    total_start_time = time.time()
    try:
        orchestrator = get_smart_orchestrator()
        try:
            background_tasks = background_tasks_var.get()
        except LookupError:
            from fastapi import BackgroundTasks
            background_tasks = BackgroundTasks()
            background_tasks_var.set(background_tasks)

        # --- ASYNCHRONOUS ACTIONS (Always Triggered) ---

        # 1. ALWAYS trigger memory triage - decouple from context retrieval
        logger.info(f"🧠 [Memory Triage] Always analyzing message for memorable content: '{user_message[:50]}...'")
        triage_start_time = time.time()
        background_tasks.add_task(
            orchestrator.triage_and_save_memory_background,
            user_message,
            supa_uid,
            client_name
        )
        logger.info(f"[PERF] Memory Triage triggered in {time.time() - triage_start_time:.4f}s")

        # 2. If context is needed, also trigger the separate deep analysis background task.
        if needs_context:
            logger.info(f"🧠 [Async Analysis] Triggering deep analysis for: '{user_message[:50]}...'")
            analysis_task_start_time = time.time()
            background_tasks.add_task(
                orchestrator.run_deep_analysis_and_save_as_memory,
                user_message,
                supa_uid,
                client_name
            )
            logger.info(f"[PERF] Deep Analysis Task triggered in {time.time() - analysis_task_start_time:.4f}s")


        # --- IMMEDIATE RESPONSE (Logic Flow) ---

        # 1. Handle NEW conversations FIRST, regardless of the 'needs_context' flag.
        if is_new_conversation:
            logger.info("🌟 [New Conversation] Handling new conversation flow.")
            narrative_start_time = time.time()
            # Use the orchestrator's method to get the cached narrative
            narrative = await orchestrator._get_cached_narrative(supa_uid)
            logger.info(f"[PERF] Narrative Cache Check took {time.time() - narrative_start_time:.4f}s")
            
            if narrative:
                logger.info("✅ [New Conversation] Found cached narrative.")
                narrative_with_context = f"---\n[Your Life Context]\n{narrative}\n---"
                return orchestrator._append_system_directive(narrative_with_context)
            else:
                logger.info("🧐 [New Conversation] No cached narrative found. Providing default welcome.")
                # The background task will generate the narrative for the next time.
                default_message = "This is a new conversation. Your interactions will be analyzed and saved to build your personal context over time."
                return orchestrator._append_system_directive(default_message)

        # 2. Handle CONTINUING conversations where the client does NOT need context.
        if not needs_context:
            logger.info("✅ [Continuing Conversation] Context not required by client.")
            no_context_message = "Context is not required for this query. The user's message will be analyzed for important information in the background."
            return orchestrator._append_system_directive(no_context_message)

        # 3. Handle CONTINUING conversations that DO need context.
        logger.info("🔍 [Continuing Conversation] Using standard orchestration to get context.")
        orchestration_start_time = time.time()
        context = await orchestrator._standard_orchestration(user_message, supa_uid, client_name, is_new_conversation)
        logger.info(f"[PERF] Standard Orchestration took {time.time() - orchestration_start_time:.4f}s")
        return context

    except Exception as e:
        logger.error(f"Error in jean_memory dual-path orchestration: {e}", exc_info=True)
        return f"I had trouble processing your message: {str(e)}"
    finally:
        logger.info(f"[PERF] Total jean_memory call took {time.time() - total_start_time:.4f}s") 