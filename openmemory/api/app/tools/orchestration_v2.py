"""
Simplified orchestration v2 - Clean architecture with predictable behavior
"""
import logging
import asyncio
import time
from typing import Optional, Dict, Any

from app.mcp_instance import mcp
from app.context import user_id_var, client_name_var, background_tasks_var

logger = logging.getLogger(__name__)


class MemoryModeHandler:
    """Clean handler for different memory retrieval modes"""
    
    def __init__(self):
        self.mode_configs = {
            "fast": {
                "timeout": 2,
                "memory_limit": 15,
                "use_synthesis": False
            },
            "balanced": {
                "timeout": 10,
                "memory_limit": 50,
                "use_synthesis": True,
                "parallel_searches": 3
            },
            "comprehensive": {
                "timeout": 30,
                "memory_limit": 100,
                "use_synthesis": True,
                "include_documents": True,
                "parallel_searches": 5
            }
        }
    
    async def get_context(
        self, 
        query: str, 
        mode: str = "balanced",
        user_id: str = None,
        client_name: str = None
    ) -> str:
        """
        Main entry point with guaranteed non-empty response
        """
        config = self.mode_configs.get(mode, self.mode_configs["balanced"])
        
        try:
            # Set timeout for the mode
            result = await asyncio.wait_for(
                self._execute_mode(query, mode, config, user_id, client_name),
                timeout=config["timeout"]
            )
            
            # Guarantee non-empty response
            if not result or (isinstance(result, str) and not result.strip()):
                logger.warning(f"Empty result from {mode} mode, using fallback")
                result = await self._fallback_search(query, user_id)
            
            return result
            
        except asyncio.TimeoutError:
            logger.error(f"Timeout in {mode} mode after {config['timeout']}s")
            return await self._fallback_search(query, user_id)
        except Exception as e:
            logger.error(f"Error in {mode} mode: {e}", exc_info=True)
            return f"Context temporarily unavailable (mode: {mode}). Please try again."
    
    async def _execute_mode(
        self, 
        query: str, 
        mode: str, 
        config: Dict[str, Any],
        user_id: str,
        client_name: str
    ) -> str:
        """Execute specific mode logic"""
        
        if mode == "fast":
            return await self._fast_mode(query, config, user_id)
        elif mode == "balanced":
            return await self._balanced_mode(query, config, user_id)
        elif mode == "comprehensive":
            return await self._comprehensive_mode(query, config, user_id, client_name)
        else:
            # Default to balanced
            return await self._balanced_mode(query, config, user_id)
    
    async def _fast_mode(self, query: str, config: Dict, user_id: str) -> str:
        """Fast mode - direct memory search without synthesis"""
        from app.tools.memory import search_memory
        
        result = await search_memory(
            query=query, 
            limit=config["memory_limit"]
        )
        return result or "No memories found for your query."
    
    async def _balanced_mode(self, query: str, config: Dict, user_id: str) -> str:
        """Balanced mode - parallel searches with AI synthesis"""
        from app.utils.memory import get_async_memory_client
        from mem0.llms.gemini import GeminiLLM
        from mem0.llms.base import BaseLlmConfig
        
        memory_client = await get_async_memory_client()
        
        # Parallel searches for rich context
        search_queries = [
            query,  # Direct query
            f"personality traits values preferences of user",  # Core identity
            f"recent activities conversations events"  # Recent context
        ]
        
        # Execute searches in parallel
        search_tasks = [
            memory_client.search(q, user_id=user_id, limit=20) 
            for q in search_queries
        ]
        
        try:
            results = await asyncio.gather(*search_tasks, return_exceptions=True)
        except Exception as e:
            logger.error(f"Parallel search failed: {e}")
            return await self._fallback_search(query, user_id)
        
        # Combine and deduplicate
        all_memories = []
        for result in results:
            if isinstance(result, Exception):
                logger.warning(f"Search failed: {result}")
                continue
            if isinstance(result, list):
                all_memories.extend(result)
        
        # Deduplicate by ID
        unique_memories = {}
        for mem in all_memories:
            if isinstance(mem, dict) and mem.get('id'):
                unique_memories[mem['id']] = mem
        
        if not unique_memories:
            return "No relevant memories found. Your interactions will help build context over time."
        
        # Synthesize with Gemini Flash
        if config.get("use_synthesis"):
            return await self._synthesize_with_gemini(
                query, 
                list(unique_memories.values()),
                config
            )
        
        # Return raw memories if synthesis disabled
        return self._format_raw_memories(list(unique_memories.values()))
    
    async def _comprehensive_mode(
        self, 
        query: str, 
        config: Dict, 
        user_id: str,
        client_name: str
    ) -> str:
        """Comprehensive mode - deep analysis with documents"""
        from app.tools.documents import deep_memory_query
        
        result = await deep_memory_query(search_query=query)
        return result or "No comprehensive analysis available."
    
    async def _synthesize_with_gemini(
        self, 
        query: str, 
        memories: list,
        config: Dict
    ) -> str:
        """Synthesize memories using Gemini Flash"""
        from mem0.llms.gemini import GeminiLLM
        from mem0.llms.base import BaseLlmConfig
        
        llm = GeminiLLM(config=BaseLlmConfig(model="gemini-2.5-flash"))
        
        # Prepare memory content
        memory_texts = []
        for mem in memories[:config["memory_limit"]]:
            content = mem.get('memory', mem.get('content', ''))
            if content and "SYSTEM DIRECTIVE" not in content:
                memory_texts.append(f"- {content}")
        
        if not memory_texts:
            return "No relevant memories to synthesize."
        
        prompt = f"""Based on these memories, answer: "{query}"

Relevant Context:
{chr(10).join(memory_texts[:30])}  # Limit to 30 memories for synthesis

Provide a helpful, conversational answer. If memories don't fully answer the question, acknowledge what's known and what's missing."""
        
        try:
            response = llm.generate_response([{"role": "user", "content": prompt}])
            return response
        except Exception as e:
            logger.error(f"Gemini synthesis failed: {e}")
            return self._format_raw_memories(memories[:10])
    
    async def _fallback_search(self, query: str, user_id: str) -> str:
        """Fallback for when primary mode fails"""
        try:
            from app.tools.memory import search_memory
            result = await search_memory(query=query, limit=5)
            if result:
                return f"[Fallback mode] {result}"
            return "No memories found. Start a conversation to build your context."
        except:
            return "Context retrieval temporarily unavailable. Please try again."
    
    def _format_raw_memories(self, memories: list) -> str:
        """Format raw memories for display"""
        if not memories:
            return "No memories found."
        
        formatted = ["Relevant memories:"]
        for i, mem in enumerate(memories[:10], 1):
            content = mem.get('memory', mem.get('content', ''))
            if content:
                formatted.append(f"{i}. {content[:200]}...")
        
        return "\n".join(formatted)


# Global handler instance
memory_handler = MemoryModeHandler()


@mcp.tool(description="Simplified memory tool with predictable modes and guaranteed responses")
async def jean_memory_v2(
    user_message: str,
    mode: str = "balanced",
    is_new_conversation: bool = False,
    save_memory: bool = True
) -> str:
    """
    Simplified jean_memory with clear, predictable behavior.
    
    Modes:
    - fast: Direct search, no synthesis (1-2s)
    - balanced: Parallel search with AI synthesis (3-5s) [DEFAULT]
    - comprehensive: Deep analysis with documents (20-30s)
    
    Features:
    - Guaranteed non-empty response
    - Automatic fallback on failure
    - Clean separation of concerns
    - Predictable timeout behavior
    """
    user_id = user_id_var.get(None)
    client_name = client_name_var.get(None)
    
    if not user_id:
        return "Error: User authentication required."
    
    # Handle new conversation
    if is_new_conversation:
        from app.mcp_orchestration import get_smart_orchestrator
        orchestrator = get_smart_orchestrator()
        narrative = await orchestrator._get_cached_narrative(user_id)
        if narrative:
            return f"---\n[Your Life Context]\n{narrative}\n---"
        return "Welcome! This is a new conversation. Your interactions will build your personal context over time."
    
    # Save memory in background (if enabled)
    if save_memory:
        try:
            background_tasks = background_tasks_var.get()
        except LookupError:
            from fastapi import BackgroundTasks
            background_tasks = BackgroundTasks()
            background_tasks_var.set(background_tasks)
        
        from app.mcp_orchestration import get_smart_orchestrator
        orchestrator = get_smart_orchestrator()
        background_tasks.add_task(
            orchestrator.triage_and_save_memory_background,
            user_message,
            user_id,
            client_name
        )
    
    # Get context with specified mode
    return await memory_handler.get_context(
        query=user_message,
        mode=mode,
        user_id=user_id,
        client_name=client_name
    )


@mcp.tool(description="Direct mode selection for testing and explicit control")
async def get_context_direct(
    query: str,
    mode: str = "balanced"
) -> str:
    """
    Direct access to context modes for testing.
    No background tasks, just pure context retrieval.
    """
    user_id = user_id_var.get(None)
    client_name = client_name_var.get(None)
    
    if not user_id:
        return "Error: User authentication required."
    
    return await memory_handler.get_context(
        query=query,
        mode=mode,
        user_id=user_id,
        client_name=client_name
    )