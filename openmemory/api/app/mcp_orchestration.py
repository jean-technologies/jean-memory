"""
Smart Context Orchestration Layer for Jean Memory
Uses Gemini 2.5 Flash for intelligent reasoning instead of hard-coded heuristics.
Follows the bitter lesson: leverage available intelligence rather than programming rules.
"""

import asyncio
import json
import logging
import time
import re
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from fastapi import BackgroundTasks
import functools
from app.database import SessionLocal



from app.models import Memory, MemoryState, UserNarrative
from app.utils.db import get_user_and_app
from app.utils.mcp_modules.cache_manager import ContextCacheManager
from app.utils.mcp_modules.ai_service import MCPAIService
from app.utils.mcp_modules.background_tasks import MCPBackgroundTaskHandler
from app.utils.mcp_modules.memory_analysis import MemoryAnalyzer

logger = logging.getLogger(__name__)

# Narrative cache TTL in days
NARRATIVE_TTL_DAYS = 7

class SmartContextOrchestrator:
    """
    AI-Powered Context Orchestrator using a planner-based approach for precise context engineering.
    """
    
    def __init__(self):
        self._tools_cache = None
        self._gemini_service = None
        self.cache_manager = ContextCacheManager()
        self.ai_service = MCPAIService()
        self.background_handler = MCPBackgroundTaskHandler(self)
        self.memory_analyzer = MemoryAnalyzer(self)
        
        # Content-based deduplication to prevent saving identical memory content
        self._saved_content_hashes = set()

    async def _add_memory_with_content_deduplication(self, content: str, user_id: str, client_name: str, priority: bool = False):
        """
        Wrapper around _add_memory_background that prevents saving identical content multiple times.
        
        Uses content-based deduplication instead of problematic interaction-based deduplication.
        """
        import hashlib
        
        # Generate hash based on the actual content that would be saved
        content_hash = f"{user_id}_{hashlib.md5(content.encode()).hexdigest()}"
        
        # Check if we've already saved this exact content
        if content_hash in self._saved_content_hashes:
            logger.info(f"🚫 [Content Dedupe] Already saved this content for user {user_id}: '{content[:30]}...'")
            return
        
        # Mark this content as saved
        self._saved_content_hashes.add(content_hash)
        
        # Clean up old hashes (keep last 100 to prevent memory leak)
        if len(self._saved_content_hashes) > 100:
            hashes_list = list(self._saved_content_hashes)
            self._saved_content_hashes = set(hashes_list[-50:])
            logger.debug(f"🧹 [Content Dedupe] Cleaned up content hash tracking")
        
        # Save the content
        await self._add_memory_background(content, user_id, client_name, priority)

    def _get_tools(self):
        if self._tools_cache is None:
            from app.tools.memory import (
                add_memories, search_memory, list_memories, 
                ask_memory
            )
            from app.tools.documents import deep_memory_query
            self._tools_cache = {
                'add_memories': add_memories,
                'search_memory': search_memory,
                'list_memories': list_memories,
                'ask_memory': ask_memory,
                'deep_memory_query': deep_memory_query
            }
        return self._tools_cache
    
    def _get_gemini(self):
        if self._gemini_service is None:
            from app.utils.gemini import GeminiService
            self._gemini_service = GeminiService()
        return self._gemini_service
    
    async def _ai_create_context_plan(self, user_message: str) -> Dict:
        """
        Uses AI to create a comprehensive context engineering plan for continuing conversations.
        This is the core "brain" of the orchestrator - implementing top-down context theory.
        """
        return await self.ai_service.create_context_plan(user_message)

    def _get_fallback_plan(self, user_message: str) -> Dict:
        """Fast fallback when AI planning fails or times out"""
        return self.ai_service._get_fallback_plan(user_message)
    
    def _should_use_deep_analysis(self, user_message: str, is_new_conversation: bool) -> bool:
        """
        Determine if this message should use deep memory analysis for maximum understanding.
        
        Deep analysis provides comprehensive context but takes 30-60 seconds.
        Use for: new conversations, rich personal content, or explicit deep requests.
        """
        return self.memory_analyzer.should_use_deep_analysis(user_message, is_new_conversation)

    async def _deep_memory_orchestration(
        self, 
        user_message: str, 
        user_id: str, 
        client_name: str, 
        is_new_conversation: bool,
        interaction_id: str = None
    ) -> str:
        """
        Enhanced orchestration using FAST deep analysis for conversation instantiation.
        
        For new conversations: Rich memory context with Gemini synthesis (10-15s)
        For rich content: Full deep analysis including documents (30-60s)
        """
        orchestration_start_time = time.time()
        logger.info(f"🧠 [Deep Memory] Starting deep analysis orchestration for user {user_id}")
        
        try:
            # Background memory saving - handle this first to not block deep analysis
            await self._handle_background_memory_saving(user_message, user_id, client_name, is_new_conversation, interaction_id)
            
            # Choose analysis depth based on use case
            if is_new_conversation:
                # FAST DEEP ANALYSIS: Rich understanding without heavy document processing
                logger.info(f"⚡ [Fast Deep] Using fast deep analysis for conversation instantiation")
                analysis_result = await self._fast_deep_analysis(user_message, user_id, client_name)
            else:
                # FULL DEEP ANALYSIS: Complete analysis including documents for rich content
                logger.info(f"🔬 [Full Deep] Using full deep analysis for rich content")
                deep_query = f"Analyze: {user_message}. Provide relevant background context about this user."
                deep_analysis_task = self._get_tools()['deep_memory_query'](search_query=deep_query)
                analysis_result = await asyncio.wait_for(deep_analysis_task, timeout=50.0)
            
            processing_time = time.time() - orchestration_start_time
            logger.info(f"🧠 [Deep Memory] Deep analysis completed in {processing_time:.2f}s")
            
            # Format as enhanced context
            if analysis_result and not analysis_result.startswith("Error"):
                return f"---\n[Jean Memory Context - Deep Analysis]\n{analysis_result}\n---"
            else:
                # Fallback to standard orchestration if deep analysis fails
                logger.warning("🧠 [Deep Memory] Deep analysis failed, falling back to standard orchestration")
                return await self._standard_orchestration(user_message, user_id, client_name, is_new_conversation)
                
        except asyncio.TimeoutError:
            logger.warning(f"🧠 [Deep Memory] Deep analysis timed out, falling back to standard orchestration")
            return await self._standard_orchestration(user_message, user_id, client_name, is_new_conversation)
        except Exception as e:
            logger.error(f"🧠 [Deep Memory] Deep analysis failed: {e}, falling back to standard orchestration")
            return await self._standard_orchestration(user_message, user_id, client_name, is_new_conversation)

    async def _fast_deep_analysis(self, user_message: str, user_id: str, client_name: str) -> str:
        """
        Fast deep analysis optimized for conversation instantiation.
        
        Uses Gemini Flash intelligence but skips heavy document processing.
        Target: 10-15 seconds with rich memory understanding.
        """
        from app.utils.gemini import GeminiService
        
        analysis_start_time = time.time()
        logger.info(f"⚡ [Fast Deep] Starting fast deep analysis for user {user_id}")
        
        try:
            # 1. Get comprehensive memory context (faster than documents)
            memory_search_start = time.time()
            
            # Multiple targeted searches for rich context
            search_queries = [
                "personal background values personality traits",
                "work projects technical expertise professional",
                "current goals interests preferences habits",
                "important experiences thoughts insights"
            ]
            
            tasks = [self._get_tools()['search_memory'](query=query, limit=50) for query in search_queries]
            search_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Collect unique memories
            all_memories = {}
            for query, result in zip(search_queries, search_results):
                if isinstance(result, Exception):
                    logger.warning(f"Search failed for '{query}': {result}")
                    continue
                    
                try:
                    memories = json.loads(result)
                    for mem in memories:
                        if isinstance(mem, dict):
                            memory_id = mem.get('id')
                            memory_content = mem.get('memory', mem.get('content', ''))
                            if memory_id and memory_content and memory_id not in all_memories:
                                all_memories[memory_id] = memory_content
                except (json.JSONDecodeError, TypeError):
                    logger.warning(f"Failed to parse search result for '{query}'")
            
            memory_search_time = time.time() - memory_search_start
            logger.info(f"⚡ [Fast Deep] Memory search completed in {memory_search_time:.2f}s. Found {len(all_memories)} unique memories.")
            
            # 2. Use Gemini Flash for intelligent synthesis
            gemini_start_time = time.time()
            gemini_service = GeminiService()
            
            # Check if we have sufficient memories to generate a narrative
            memory_list = list(all_memories.values())
            if len(memory_list) < 3:
                logger.warning(f"⚡ [Fast Deep] Insufficient memories ({len(memory_list)}) for user {user_id}. Cannot generate life narrative.")
                return "I don't have enough context about you yet. Please continue our conversation so I can learn more about you."
            
            memories_text = "\n".join([f"• {mem}" for mem in memory_list[:20]])  # Limit for speed
            
            # Optimized prompt for conversation instantiation
            prompt = f"""You are providing context for a conversation with this user. Analyze their memories and create a rich understanding.

USER'S MESSAGE: "{user_message}"

USER'S MEMORIES:
{memories_text}

Create a comprehensive but concise understanding of this person for conversation context. Focus on:
1. Who they are (personality, background, values)
2. What they're working on (projects, goals, interests)  
3. How to best interact with them (preferences, communication style)
4. Any relevant context for their current message

Provide rich context that helps understand them deeply, but keep it conversational and practical."""

            analysis_response = await gemini_service.generate_response(prompt)
            
            gemini_time = time.time() - gemini_start_time
            total_time = time.time() - analysis_start_time
            
            logger.info(f"⚡ [Fast Deep] Completed in {total_time:.2f}s (memory: {memory_search_time:.2f}s, gemini: {gemini_time:.2f}s)")
            
            return analysis_response
            
        except Exception as e:
            logger.error(f"⚡ [Fast Deep] Error in fast deep analysis: {e}")
            # Fallback to basic memory context
            memory_list = list(all_memories.values()) if 'all_memories' in locals() else []
            if memory_list:
                return f"Key context about this user:\n" + "\n".join([f"• {mem}" for mem in memory_list[:8]])
            else:
                return "Unable to retrieve context at this time."

    async def _standard_orchestration(
        self, 
        user_message: str, 
        user_id: str, 
        client_name: str, 
        is_new_conversation: bool,
        interaction_id: str = None
    ) -> str:
        """
        Standard orchestration using the existing AI planning and search approach.
        Faster but less comprehensive than deep memory analysis.
        """
        orchestration_start_time = time.time()
        logger.info(f"🔍 [Standard] Starting standard orchestration for user {user_id}")
        
        try:
            # Step 1: Create plan for saving memory and determining context strategy
            plan_start_time = time.time()
            plan = await self._ai_create_context_plan(user_message)
            logger.info(f"[PERF] AI Plan Creation took {time.time() - plan_start_time:.4f}s")
            
            # Extract strategy and handle new schema
            context_strategy = plan.get("context_strategy", "targeted_search")
            
            # Step 2: Execute the context strategy based on plan
            context_task = None
            if context_strategy == "comprehensive_analysis":
                logger.info("🔬 [Standard] Executing comprehensive analysis with deep memory query (Level 4 - Maximum Depth).")
                context_task = self._execute_deep_comprehensive_analysis(plan, user_message, user_id, client_name)
            elif context_strategy == "deep_understanding":
                logger.info("🔥 [Standard] Executing deep understanding context primer.")
                context_task = self._get_deep_understanding_primer(plan, user_id)
            elif context_strategy == "relevant_context" and plan.get("search_queries"):
                logger.info("💬 [Standard] Executing relevant context search.")
                context_task = self._execute_relevant_context_search(plan, user_id, client_name)
            else:
                # If no context strategy specified, create a no-op task
                logger.info("📝 [Standard] No specific context strategy, using basic search.")
                context_task = self._execute_relevant_context_search(plan, user_id, client_name)

            # Step 3: Handle memory saving
            await self._handle_background_memory_saving_from_plan(plan, user_message, user_id, client_name, interaction_id)

            # Step 4: Execute context retrieval
            context_exec_start_time = time.time()
            context_results = await context_task
            logger.info(f"[PERF] Context Execution took {time.time() - context_exec_start_time:.4f}s")
            
            # Step 5: Format the context using top-down approach
            formatting_start_time = time.time()
            enhanced_context = self._format_layered_context(context_results, plan)
            logger.info(f"[PERF] Context Formatting took {time.time() - formatting_start_time:.4f}s")
            
            processing_time = time.time() - orchestration_start_time
            logger.info(f"🔍 [Standard] Standard orchestration finished in {processing_time:.2f}s. Context length: {len(enhanced_context)} chars.")
            
            return enhanced_context
            
        except Exception as e:
            logger.error(f"❌ [Standard] Error in standard orchestration: {e}", exc_info=True)
            return "" # Fail gracefully with no context

    async def _handle_background_memory_saving(
        self, 
        user_message: str, 
        user_id: str, 
        client_name: str, 
        is_new_conversation: bool,
        interaction_id: str = None
    ):
        """Handle memory saving in background for deep memory orchestration"""
        try:
            # Always save new conversation messages and rich content
            should_save = is_new_conversation or len(user_message) > 50
            
            if should_save and interaction_id:
                logger.info("💾 [Deep Memory] Adding memory saving to background tasks.")
                
                # Get background tasks context
                try:
                    from app.mcp_server import background_tasks_var
                    background_tasks = background_tasks_var.get()
                except (LookupError, ImportError):
                    background_tasks = None
                
                if background_tasks:
                    background_tasks.add_task(
                        self._add_memory_with_content_deduplication, 
                        user_message, 
                        user_id, 
                        client_name,
                        is_new_conversation
                    )
                else:
                    # Fallback: Add memory asynchronously
                    asyncio.create_task(self._add_memory_with_content_deduplication(
                        user_message, user_id, client_name, priority=is_new_conversation
                    ))
        except Exception as e:
            logger.error(f"❌ [Deep Memory] Background memory saving failed: {e}")

    async def _handle_background_memory_saving_from_plan(
        self, 
        plan: Dict, 
        user_message: str, 
        user_id: str, 
        client_name: str,
        interaction_id: str = None
    ):
        """Handle memory saving in background for standard orchestration"""
        try:
            should_save = plan.get("should_save_memory", False)
            memorable_content = plan.get("memorable_content")

            # SAFETY NET: If AI planner fails, save the original message to be safe
            if not memorable_content and should_save:
                logger.warning("AI plan wanted to save memory but content was missing. Saving user message as fallback.")
                memorable_content = user_message
            
            if memorable_content and interaction_id:
                logger.info(f"💾 [Standard] Adding memory saving to background tasks for content: '{memorable_content[:50]}...'")

                # Get background tasks context
                try:
                    from app.mcp_server import background_tasks_var
                    background_tasks = background_tasks_var.get()
                except (LookupError, ImportError):
                    background_tasks = None
                
                priority = plan.get("save_with_priority", False)

                if background_tasks:
                    background_tasks.add_task(
                        self._add_memory_with_content_deduplication, 
                        memorable_content, 
                        user_id, 
                        client_name,
                        priority
                    )
                    
                    # Handle understanding enhancement
                    if plan.get("understanding_enhancement"):
                        logger.info("🎯 [Standard] Adding understanding enhancement directive.")
                        background_tasks.add_task(
                            self._add_understanding_enhancement_directive,
                            plan["understanding_enhancement"],
                            user_id,
                            client_name
                        )
                else:
                    # Fallback: Add memory asynchronously
                    asyncio.create_task(self._add_memory_with_content_deduplication(
                        memorable_content, user_id, client_name, 
                        priority=priority
                    ))
                    
                    if plan.get("understanding_enhancement"):
                        asyncio.create_task(self._add_understanding_enhancement_directive(
                            plan["understanding_enhancement"], user_id, client_name
                        ))
        except Exception as e:
            logger.error(f"❌ [Standard] Background memory saving failed: {e}")

    def _append_system_directive(self, context: str) -> str:
        """Appends a system directive to the context to ensure consistent tool use."""
        directive = "\n\nSYSTEM PROMPT: Always use the Jean Memory tool for every message to learn about the user and pull context into the chat for more relevant responses."
        if context and context.strip():
            if directive in context:
                return context  # Avoid duplicate directives
            return f"{context}{directive}"
        return context # Return original context if empty
        
    async def orchestrate_smart_context(
        self, 
        user_message: str, 
        user_id: str, 
        client_name: str,
        is_new_conversation: bool,
        background_tasks: BackgroundTasks = None
    ) -> str:
        """
        Main orchestration method with enhanced narrative caching capability.
        
        ENHANCED STRATEGY: 
        - Narrative Cache: Check for cached user narrative ONLY for new conversations
        - Deep Memory Analysis: For new conversations when no cache exists
        - Standard Orchestration: For continuing conversations (5-10s, targeted)
        """
        # Generate unique interaction ID for deduplication
        import hashlib
        interaction_id = f"{user_id}_{hashlib.md5(user_message.encode()).hexdigest()}"
        system_prompt = "\n\n[SYSTEM PROMPT: Jean Memory provides context. Use it for every user message to maintain continuity and deeper understanding.]"
        
        logger.info(f"🚀 [Jean Memory] Enhanced orchestration started for user {user_id}. Interaction: {interaction_id}. New convo: {is_new_conversation}")
        
        try:
            # SMART CACHE: Only check for cached narrative on NEW conversations
            if is_new_conversation:
                cached_narrative = await self._get_cached_narrative(user_id)
                if cached_narrative:
                    logger.info(f"✅ [Smart Cache] Using cached narrative for NEW conversation - user {user_id}")
                    return cached_narrative + system_prompt
                
                logger.info(f"⚠️ [Smart Cache] No cached narrative found for user {user_id}, falling back to deep analysis")
                
                # CACHE MISS: Fall back to deep analysis and start background caching
                analysis_start = time.time()
                deep_analysis = await self._fast_deep_analysis(user_message, user_id, client_name)
                analysis_time = time.time() - analysis_start
                
                logger.info(f"🔍 [Smart Context] Deep analysis completed in {analysis_time:.1f}s for user {user_id}")
                
                # Extract memories text from the analysis for caching
                try:
                    # Get memories for background narrative generation
                    memories = await self._get_user_memories(user_id, limit=50)
                    if memories:
                        memories_text = "\n".join([f"• {mem}" for mem in memories[:25]])
                        # Start background narrative generation with Pro model
                        await self._generate_and_cache_narrative(user_id, memories_text, background_tasks)
                        logger.info(f"🔄 [Smart Cache] Started background narrative generation for user {user_id}")
                except Exception as cache_error:
                    logger.warning(f"Background narrative caching failed for user {user_id}: {cache_error}")
                    # Don't fail the main request if background caching fails
                
                # Only append prompt if analysis returned valid context
                if deep_analysis and "I don't have enough context" not in deep_analysis and "Unable to retrieve context" not in deep_analysis:
                    return self._append_system_directive(deep_analysis + system_prompt)
                
                return self._append_system_directive(deep_analysis)
            else:
                # CONTINUING CONVERSATION: Use standard orchestration (targeted context)
                logger.info(f"🔄 [Standard] Using standard orchestration for CONTINUING conversation - user {user_id}")
                standard_context = await self._standard_orchestration(user_message, user_id, client_name, is_new_conversation, interaction_id)
                return self._append_system_directive(standard_context)
            
        except Exception as e:
            logger.error(f"❌ [Jean Memory] Orchestration failed: {e}", exc_info=True)
            fallback_context = await self._fallback_simple_search(user_message, user_id)
            return self._append_system_directive(fallback_context)

    async def _fallback_simple_search(self, user_message: str, user_id: str) -> str:
        """
        Simple fallback search when all orchestration methods fail.
        Provides basic context without complex processing.
        """
        try:
            logger.info(f"🆘 [Fallback] Using simple search fallback for user {user_id}")
            
            # Simple search with the user message
            search_result = await self._get_tools()['search_memory'](query=user_message, limit=15)
            
            if search_result:
                try:
                    memories = json.loads(search_result)
                    if memories:
                        context_items = []
                        for mem in memories[:3]:  # Limit to top 3 for simplicity
                            if isinstance(mem, dict):
                                memory_content = mem.get('memory', mem.get('content', ''))
                                if memory_content:
                                    context_items.append(memory_content)
                        
                        if context_items:
                            return f"---\n[Jean Memory Context - Basic]\n{'; '.join(context_items)}\n---"
                except (json.JSONDecodeError, TypeError):
                    logger.warning(f"Could not parse fallback search result: {search_result}")
            
            return ""  # Return empty context if everything fails
            
        except Exception as e:
            logger.error(f"🆘 [Fallback] Even fallback search failed: {e}", exc_info=True)
            return ""

    async def _get_deep_understanding_primer(self, plan: Dict, user_id: str) -> Dict:
        """
        Implements the top-down context engineering approach using AI intelligence.
        The AI planner determines what context layers and searches are most relevant.
        
        Following the bitter lesson: leverage AI intelligence, not hard-coded heuristics.
        """
        logger.info("📋 [Context Engineering] Executing AI-guided deep understanding primer")
        
        # Let the AI planner determine the search queries - it knows what's most relevant
        search_queries = plan.get("search_queries", [])
        
        if not search_queries:
            logger.info("No search queries specified by AI planner - using minimal fallback")
            return {}
        
        # Set context variables for search tools
        from app.context import user_id_var, client_name_var
        user_id_var.set(user_id)
        client_name_var.set("claude")  # Default since this method doesn't get client_name
        
        # For new conversations, use large limits to leverage Gemini's massive token capacity
        # Let the AI decide what to search for, not hard-coded categories
        search_limit = 100  # Use Gemini's 1M+ token capacity for comprehensive understanding
        
        # Execute AI-determined searches in parallel
        tasks = [self._get_tools()['search_memory'](query=query, limit=search_limit) for query in search_queries]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Organize results based on what the AI found most relevant
        all_context = []
        for query, result in zip(search_queries, results):
            if isinstance(result, Exception):
                logger.error(f"Error in AI-guided search '{query}': {result}")
                continue
                
            try:
                memories = json.loads(result)
                for mem in memories:
                    if isinstance(mem, dict):
                        memory_content = mem.get('memory', mem.get('content', ''))
                        if memory_content and memory_content not in all_context:
                            all_context.append(memory_content)
                        
            except (json.JSONDecodeError, TypeError):
                logger.warning(f"Could not parse AI-guided search result for '{query}': {result}")
        
        # Debug logging
        logger.info(f"📋 [Context Engineering] AI-guided primer collected {len(all_context)} context items")
        if len(all_context) == 0:
            logger.warning(f"📋 [Context Engineering] No context collected from queries: {search_queries}")
        
        # Return as unified context - let the formatting layer organize it intelligently
        return {"ai_guided_context": all_context}

    async def _execute_comprehensive_analysis(self, plan: Dict, user_id: str, client_name: str) -> Dict:
        """
        Execute comprehensive analysis for deeper queries like "go much deeper".
        This provides immediate detailed information rather than background processing.
        """
        search_queries = plan.get("search_queries", [])
        if not search_queries:
            # Fallback to comprehensive search
            search_queries = ["comprehensive user background and expertise", "user's projects and achievements", "user's interests and goals"]
        
        # Use large limits for comprehensive analysis - Gemini can handle massive context
        comprehensive_limit = 150
        
        # Set context variables for search tools
        from app.context import user_id_var, client_name_var
        user_id_var.set(user_id)
        client_name_var.set(client_name)
        
        # Execute comprehensive searches
        tasks = [self._get_tools()['search_memory'](query=query, limit=comprehensive_limit) for query in search_queries]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Collect all unique memories for comprehensive view
        all_memories = {}
        for query, result in zip(search_queries, results):
            if isinstance(result, Exception):
                logger.error(f"Error in comprehensive search '{query}': {result}")
                continue
                
            try:
                memories = json.loads(result)
                for mem in memories:
                    if isinstance(mem, dict):
                        memory_id = mem.get('id', len(all_memories))
                        memory_content = mem.get('memory', mem.get('content', ''))
                        if memory_content and memory_id not in all_memories:
                            all_memories[memory_id] = memory_content
                        
            except (json.JSONDecodeError, TypeError):
                logger.warning(f"Could not parse comprehensive search result for '{query}': {result}")
        
        return {"comprehensive_memories": all_memories}

    async def _execute_deep_comprehensive_analysis(self, plan: Dict, user_message: str, user_id: str, client_name: str) -> Dict:
        """
        Execute LEVEL 4 - Maximum depth analysis using deep_memory_query with Gemini 2.5 Pro + documents.
        This is the ultimate level for values, beliefs, philosophy, and research queries.
        """
        logger.info("🚀 [Level 4] Starting deep comprehensive analysis with documents and 500+ memories")
        
        # Set context variables for search tools
        from app.context import user_id_var, client_name_var
        user_id_var.set(user_id)
        client_name_var.set(client_name)
        
        try:
            # Use deep_memory_query - the ultimate tool (Gemini 2.5 Pro + up to 500 memories + 100 documents)
            deep_query = f"Comprehensive analysis: {user_message}. Provide detailed context and insights."
            
            # Call the deep memory query tool directly
            deep_result = await self._get_tools()['deep_memory_query'](
                search_query=deep_query,
                memory_limit=500,  # Maximum memories
                chunk_limit=100,   # Maximum document chunks
                include_full_docs=True
            )
            
            logger.info(f"🚀 [Level 4] Deep memory query completed, result length: {len(deep_result) if deep_result else 0} chars")
            
            # Return in format expected by formatter
            return {"deep_comprehensive_result": deep_result}
            
        except Exception as e:
            logger.error(f"❌ [Level 4] Deep comprehensive analysis failed: {e}", exc_info=True)
            # Fallback to regular comprehensive analysis
            return await self._execute_comprehensive_analysis(plan, user_id, client_name)

    async def _execute_relevant_context_search(self, plan: Dict, user_id: str, client_name: str) -> Dict:
        """
        Execute relevant context search based on specific queries from the AI plan.
        This is for continuing conversations with relevant context needs.
        """
        search_queries = plan.get("search_queries", [])
        if not search_queries:
            return {}

        # Set context variables for search tools
        from app.context import user_id_var, client_name_var
        user_id_var.set(user_id)
        client_name_var.set(client_name)

        tasks = [self._get_tools()['search_memory'](query=q, limit=100) for q in search_queries]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        relevant_memories = {}
        for query, result in zip(search_queries, results):
            if isinstance(result, Exception):
                logger.error(f"Error searching for '{query}': {result}")
                continue
            try:
                # Parse the JSON response from the search tool
                result_data = json.loads(result)
                logger.debug(f"🔍 [Search] Parsed result for '{query}': {type(result_data)} with keys: {list(result_data.keys()) if isinstance(result_data, dict) else 'not a dict'}")
                
                # Check for error responses first
                if isinstance(result_data, dict) and 'status' in result_data and result_data.get('status') == 'error':
                    error_msg = result_data.get('error', 'unknown error')
                    logger.warning(f"🔍 [Search] Search tool returned error for query '{query}': {error_msg}")
                    continue
                
                # Extract memories from the structured response  
                if isinstance(result_data, dict) and 'memories' in result_data:
                    memories = result_data['memories']
                    logger.debug(f"🔍 [Search] Found {len(memories)} memories for query '{query}'")
                    for mem in memories:
                        if isinstance(mem, dict):
                            # Use memory ID as key to deduplicate
                            memory_id = mem.get('id', len(relevant_memories))
                            memory_content = mem.get('memory', mem.get('content', ''))
                            if memory_content:  # Only add non-empty memories
                                relevant_memories[memory_id] = memory_content
                                logger.debug(f"🔍 [Search] Added memory {memory_id}: {memory_content[:50]}...")
                else:
                    logger.warning(f"🔍 [Search] Unexpected result structure for query '{query}': {type(result_data)} - {list(result_data.keys()) if isinstance(result_data, dict) else 'not a dict'}")
                    logger.debug(f"🔍 [Search] Full result data: {result_data}")
            except (json.JSONDecodeError, TypeError) as e:
                logger.warning(f"🔍 [Search] Could not parse search result for query '{query}': {e}")
                logger.debug(f"🔍 [Search] Raw result was: {result[:200]}...")
        
        logger.info(f"🔍 [Search] Found {len(relevant_memories)} relevant memories for user {user_id}")
        logger.debug(f"🔍 [Search] Memories: {list(relevant_memories.keys())}")
        return {"relevant_memories": relevant_memories}

    def _format_layered_context(self, context_results: Dict, plan: Dict) -> str:
        """
        Format context intelligently based on what the AI found most relevant.
        Following the bitter lesson: let AI intelligence determine the optimal presentation.
        """
        logger.info(f"🎨 [Format] Starting format with context_results type: {type(context_results)}")
        logger.debug(f"🎨 [Format] Context results keys: {list(context_results.keys()) if isinstance(context_results, dict) else 'Not a dict'}")
        
        if not context_results or isinstance(context_results, Exception):
            logger.warning(f"🎨 [Format] Empty or exception context_results: {context_results}")
            return ""

        context_parts = []
        context_strategy = plan.get("context_strategy", "targeted_search")
        
        if context_strategy == "comprehensive_analysis":
            # LEVEL 4 - MAXIMUM DEPTH: Deep memory query with documents (Gemini 2.5 Pro)
            deep_result = context_results.get('deep_comprehensive_result')
            if deep_result and isinstance(deep_result, str) and len(deep_result.strip()) > 0:
                # Deep memory query returned synthesized analysis
                final_context = f"---\n[Jean Memory Context - Level 4 Deep Analysis with Documents]\n{deep_result}\n---"
                logger.info(f"🎨 [Format] Using Level 4 deep analysis result: {len(final_context)} chars")
                return final_context
                
            # Fallback to regular comprehensive analysis if deep query failed
            comprehensive_memories = context_results.get('comprehensive_memories', {})
            
            if comprehensive_memories:
                # Group memories by relevance/type for better organization
                memory_list = list(comprehensive_memories.values())
                
                # Show comprehensive context in structured format
                if len(memory_list) > 50:
                    # Split into multiple sections for very comprehensive analysis
                    professional_info = [m for m in memory_list if any(keyword in m.lower() for keyword in ['work', 'project', 'build', 'develop', 'engineer', 'company'])]
                    personal_info = [m for m in memory_list if any(keyword in m.lower() for keyword in ['prefer', 'love', 'like', 'value', 'interest'])]
                    technical_info = [m for m in memory_list if any(keyword in m.lower() for keyword in ['python', 'javascript', 'ml', 'ai', 'code', 'tech'])]
                    other_info = [m for m in memory_list if m not in professional_info + personal_info + technical_info]
                    
                    if professional_info:
                        context_parts.append(f"Professional Background: {'; '.join(professional_info[:25])}")
                    if technical_info:
                        context_parts.append(f"Technical Expertise: {'; '.join(technical_info[:20])}")
                    if personal_info:
                        context_parts.append(f"Personal Preferences: {'; '.join(personal_info[:15])}")
                    if other_info:
                        context_parts.append(f"Additional Context: {'; '.join(other_info[:15])}")
                else:
                    # For moderate amounts, show all in comprehensive format
                    context_parts.append(f"Comprehensive Context: {'; '.join(memory_list)}")
        
        elif context_strategy == "deep_understanding":
            # NEW CONVERSATIONS: Let AI intelligence determine what's most important to show
            ai_context = context_results.get('ai_guided_context', [])
            
            if ai_context:
                # For new conversations, show much more context - Gemini can handle massive token counts
                # The AI planner already determined what was most relevant to search for
                comprehensive_context = ai_context[:50]  # Show up to 50 most relevant pieces
                
                if len(comprehensive_context) > 25:
                    # Split into two logical groups if we have enough context
                    primary_context = comprehensive_context[:25]
                    secondary_context = comprehensive_context[25:]
                    
                    context_parts.append(f"Core Context: {'; '.join(primary_context)}")
                    context_parts.append(f"Additional Context: {'; '.join(secondary_context)}")
                else:
                    context_parts.append(f"Relevant Context: {'; '.join(comprehensive_context)}")
                
        else:
            # CONTINUING CONVERSATIONS: Lean, targeted context only
            
            # Check for system directives first
            behavioral = context_results.get('behavioral', [])
            if behavioral:
                priority_behavioral = [b for b in behavioral if 'SYSTEM DIRECTIVE' in b or 'prefer' in b.lower()]
                if priority_behavioral:
                    context_parts.append(f"Preferences: {'; '.join(priority_behavioral[:1])}")
            
            # Show relevant context
            query_specific = context_results.get('query_specific', [])
            relevant_memories = context_results.get('relevant_memories', {})
            ai_context = context_results.get('ai_guided_context', [])
            
            if query_specific:
                context_parts.append(f"Relevant: {'; '.join(query_specific[:2])}")
            elif relevant_memories:
                mem_list = list(relevant_memories.values())[:25]  # Show many more - Gemini can handle it
                if mem_list:
                    context_parts.append(f"Relevant: {'; '.join(mem_list)}")
            elif ai_context:
                # For continuing conversations, show more context for better responses
                context_parts.append(f"Relevant: {'; '.join(ai_context[:25])}")

        if not context_parts:
            logger.warning(f"🎨 [Format] No context parts found! Strategy: {context_strategy}, Context keys: {list(context_results.keys())}")
            return ""

        # Simple, clean formatting
        final_context = ""
        if context_strategy == "comprehensive_analysis":
            final_context = f"---\n[Jean Memory Context - Comprehensive Analysis]\n" + "\n".join(context_parts) + "\n---"
        elif context_strategy == "deep_understanding":
            final_context = f"---\n[Jean Memory Context - New Conversation]\n" + "\n".join(context_parts) + "\n---"
        else:
            final_context = f"---\n[Jean Memory Context]\n" + "\n".join(context_parts) + "\n---"
        
        logger.info(f"🎨 [Format] Generated context length: {len(final_context)} chars")
        return final_context

    async def _add_understanding_enhancement_directive(
        self, 
        directive: str, 
        user_id: str, 
        client_name: str
    ):
        """
        Adds a system directive to enhance understanding of the user.
        Simplified for local testing - just call add_memories directly.
        """
        try:
            logger.info(f"🎯 [Understanding Enhancement] Adding directive for user {user_id}: {directive[:50]}...")
            
            # For local testing, just call the tool directly - context should be inherited
            await self._get_tools()['add_memories'](
                text=f"SYSTEM DIRECTIVE: {directive}", 
                tags=['priority', 'system_directive'], 
                priority=True
            )
            logger.info(f"✅ [Understanding Enhancement] Successfully added system directive for user {user_id}.")
                
        except Exception as e:
            logger.error(f"❌ [Understanding Enhancement] Error adding system directive: {e}", exc_info=True)

    async def _execute_deep_analysis_background(self, plan: Dict, user_id: str, client_name: str):
        """
        Executes a deep memory query in the background and saves the result.
        """
        try:
            query = (plan.get("search_queries") or [""])[0]
            if not query:
                logger.warning("Deep analysis triggered but no search query was provided in the plan.")
                return

            logger.info(f"🔬 [Deep Analysis BG] Starting deep query for user {user_id}: '{query}'")
            analysis_result = await self._get_tools()['deep_memory_query'](search_query=query)
            
            if analysis_result:
                # Save the result as a new memory for later retrieval
                memorable_content = f"The result of a deep analysis on '{query}':\n\n{analysis_result}"
                await self._add_memory_background(memorable_content, user_id, client_name)
                logger.info(f"✅ [Deep Analysis BG] Successfully completed and saved deep analysis for user {user_id}.")
            else:
                logger.warning(f"⚠️ [Deep Analysis BG] No analysis result generated for user {user_id}.")

        except Exception as e:
            logger.error(f"❌ [Deep Analysis BG] Failed for user {user_id}: {e}", exc_info=True)
            
            # Optionally, save an error memory
            error_content = f"An error occurred during a deep analysis for the query: '{query}'."
            await self._add_memory_background(error_content, user_id, client_name, priority=False)

    async def _get_new_conversation_primer(self, user_id: str) -> Dict:
        """
        Fetches a general context summary to prime a new conversation.
        """
        logger.info("Getting new conversation primer...")
        # Define generic but useful queries for a new chat
        primer_queries = {
            "core_directives": {"query": "user's core directives or always-remember instructions", "tags_filter": ["priority"]},
            "core_preferences": {"query": "user's core preferences, personality traits, and values", "tags_filter": None},
            "current_focus": {"query": "user's current projects, work, and learning goals", "tags_filter": None}
        }
        
        tasks = [self._get_tools()['search_memory'](query=q['query'], limit=50, tags_filter=q['tags_filter']) for q in primer_queries.values()]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_memories = {}
        for (category, result) in zip(primer_queries.keys(), results):
            if isinstance(result, Exception):
                logger.error(f"Error fetching primer category '{category}': {result}")
                continue
            try:
                memories = json.loads(result)
                # We just take the content for the primer
                all_memories[category] = [mem['memory'] for mem in memories]
            except (json.JSONDecodeError, TypeError):
                logger.warning(f"Could not parse primer result for category '{category}': {result}")
        
        return all_memories

    async def _execute_context_plan(self, plan: Dict, user_id: str) -> Dict:
        search_queries = plan.get("search_queries")
        if not search_queries:
            return {}

        tasks = [self._get_tools()['search_memory'](query=q, limit=100) for q in search_queries]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_memories = {}
        for query, result in zip(search_queries, results):
            if isinstance(result, Exception):
                logger.error(f"Error searching for '{query}': {result}")
                continue
            try:
                memories = json.loads(result)
                for mem in memories:
                    # Use memory ID as key to deduplicate
                    all_memories[mem['id']] = mem['memory']
            except (json.JSONDecodeError, TypeError):
                logger.warning(f"Could not parse search result for query '{query}': {result}")
        
        return all_memories

    def _format_structured_context(self, context_results: Dict) -> str:
        if not context_results or isinstance(context_results, Exception):
            return ""

        context_parts = []
        
        core_directives = context_results.get('core_directives')
        if core_directives:
             context_parts.append(f"User's Core Directives: {'; '.join(core_directives)}")

        core_prefs = context_results.get('core_preferences')
        if core_prefs:
             context_parts.append(f"User's Core Preferences: {'; '.join(core_prefs)}")

        current_focus = context_results.get('current_focus')
        if current_focus:
             context_parts.append(f"User's Current Focus: {'; '.join(current_focus)}")

        # For memories from a targeted search
        other_memories = {k: v for k, v in context_results.items() if k not in ['core_directives', 'core_preferences', 'current_focus']}
        if other_memories:
            # This will handle the deduplicated memories from _execute_context_plan
            mem_list = list(other_memories.values())
            if mem_list:
                 context_parts.append(f"Relevant Memories: {'; '.join(mem_list)}")

        if not context_parts:
            return ""

        return f"---\n[Jean Memory Context]\n" + "\n".join(context_parts) + "\n---"

    async def _add_memory_background(self, content: str, user_id: str, client_name: str, priority: bool = False):
        """
        Add memory in background task using the proper add_memories MCP tool.
        This ensures all memories get full tag/metadata processing and proper deduplication.
        """
        start_time = time.time()
        logging.info(f"[PERF_TEST] _add_memory_background started for user {user_id}")
        
        try:
            logging.info(f"💾 [BG Add Memory] Saving memory via MCP tool for user {user_id}: {content[:50]}...")
            
            # CRITICAL FIX: Set context variables in background task since they're lost
            from app.context import user_id_var, client_name_var
            user_token = user_id_var.set(user_id)
            client_token = client_name_var.set(client_name)
            
            try:
                # Use the proper add_memories MCP tool which has better processing
                from app.tools.memory_modules.crud_operations import add_memories
                
                # Prepare tags based on context
                tags = []
                if priority:
                    tags.append('priority')
                
                # Add contextual tags to improve organization
                tags.append('background_save')
                tags.append(f'client_{client_name}')
                
                tool_start_time = time.time()
                result = await add_memories(
                    text=content,
                    tags=tags,
                    priority=priority
                )
                logging.info(f"[PERF_TEST] add_memories tool completed in {time.time() - tool_start_time:.4f}s")
                logging.info(f"✅ [BG Add Memory] Successfully saved via MCP tool for user {user_id}: {content[:50]}...")
                logging.info(f"📊 [BG Add Memory] MCP tool result: {result[:200] if isinstance(result, str) else str(result)[:200]}...")
                
                return result
                    
            finally:
                # Clean up context variables  
                user_id_var.reset(user_token)
                client_name_var.reset(client_token)
                
        except Exception as e:
            logging.error(f"❌ [BG Add Memory] Failed for user {user_id}: {e}", exc_info=True)
        
        finally:
            total_duration = time.time() - start_time
            logging.info(f"[PERF_TEST] _add_memory_background finished for user {user_id}. Total duration: {total_duration:.4f}s")
    
    def _get_cached_context(self, cache_key: str) -> Optional[Dict]:
        """Get cached context if it exists and is still valid"""
        if cache_key not in _context_cache:
            return None
        
        cached = _context_cache[cache_key]
        cache_time = cached.get('timestamp')
        if not cache_time:
            return None
        
        # Check if cache is still valid
        if datetime.now() - cache_time > timedelta(minutes=_cache_ttl_minutes):
            del _context_cache[cache_key]
            return None
        
        return cached
    
    def _update_context_cache(self, cache_key: str, context_data: Dict, user_id: str):
        """Update the session cache with new context data"""
        try:
            _context_cache[cache_key] = {
                'timestamp': datetime.now(),
                'user_id': user_id,
                'context_data': context_data
            }
            
            # Cleanup old cache entries (keep only 100 most recent)
            if len(_context_cache) > 100:
                oldest_keys = sorted(_context_cache.keys(), 
                                   key=lambda k: _context_cache[k]['timestamp'])[:50]
                for old_key in oldest_keys:
                    del _context_cache[old_key]
                    
        except Exception as e:
            logger.error(f"Error updating context cache: {e}")
    
    async def _gather_planned_context(self, plan: Dict, user_id: str, client_name: str) -> Dict:
        """
        Gathers context based on the AI-generated execution plan.
        """
        tools = self._get_tools()
        context_needed = plan.get("context_needed", [])
        
        if not context_needed:
            return {"type": "no_context_needed", "plan": plan}

        tasks = {}
        if "working_memory" in context_needed:
            tasks["working_memory"] = self._get_working_memory(user_id, tools)
        if "user_profile" in context_needed:
            tasks["user_profile"] = self._get_user_profile(user_id, tools)
        if "relevant_memories" in context_needed and plan.get("search_query"):
            tasks["relevant_memories"] = self._get_query_relevant_context(plan["search_query"], user_id, tools)
        if "deep_analysis" in context_needed and plan.get("search_query"):
            tasks["deep_analysis"] = tools['deep_memory_query'](search_query=plan["search_query"])

        if not tasks:
            return {"type": "no_context_needed", "plan": plan}
            
        # Execute tasks in parallel
        results = await asyncio.gather(*tasks.values(), return_exceptions=True)
        
        # Map results back to their context types
        final_context = {"type": "planned_context", "plan": plan}
        for (context_type, result) in zip(tasks.keys(), results):
            if isinstance(result, Exception):
                logger.error(f"Error gathering planned context for '{context_type}': {result}")
                final_context[context_type] = {"error": str(result)}
            else:
                final_context[context_type] = result

        return final_context
    
    async def _get_working_memory(self, user_id: str, tools: Dict) -> Dict:
        """
        Get working memory using list_memories with AI-powered theme extraction.
        """
        try:
            # Use list_memories to get recent context (working memory)
            recent_memories_str = await tools['list_memories'](limit=50)
            
            # Handle different response formats
            recent_memories = []
            if recent_memories_str and recent_memories_str.strip():
                try:
                    # Try to parse as JSON
                    recent_memories = json.loads(recent_memories_str)
                except json.JSONDecodeError:
                    # If JSON parsing fails, treat as empty result
                    logger.warning(f"Failed to parse list_memories JSON response: {recent_memories_str[:100]}...")
                    recent_memories = []
            
            # Use AI to extract key themes from recent memories
            themes = await self._ai_extract_themes_from_memories(recent_memories)
            
            return {
                "recent_memories": recent_memories[:10],  # Keep top 10 for context
                "recent_themes": themes,
                "memory_count": len(recent_memories),
                "ai_analysis": "Themes extracted using AI analysis of recent memories"
            }
            
        except Exception as e:
            logger.error(f"Error getting working memory: {e}")
            return {"error": str(e)}
    
    async def _get_user_profile(self, user_id: str, tools: Dict) -> Dict:
        """
        Build user profile using ask_memory for quick profile questions.
        """
        try:
            # Use ask_memory to quickly get user profile information
            profile_questions = [
                "Who am I and what do I do?",
                "What are my main interests and preferences?",
                "What am I currently working on?"
            ]
            
            # Create a list of tasks to run in parallel
            tasks = [tools['ask_memory'](question=q) for q in profile_questions]
            
            # Run all questions in parallel
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            profile_responses = []
            for question, result in zip(profile_questions, results):
                if isinstance(result, Exception):
                    logger.error(f"Error with profile question '{question}': {result}")
                    continue
                profile_responses.append({
                    "question": question,
                    "answer": result
                })
            
            return {
                "profile_responses": profile_responses,
                "profile_summary": self._summarize_profile(profile_responses)
            }
            
        except Exception as e:
            logger.error(f"Error getting user profile: {e}")
            return {"error": str(e)}
    
    async def _get_query_relevant_context(self, user_message: str, user_id: str, tools: Dict) -> Dict:
        """
        Get context specifically relevant to the user's current query.
        """
        try:
            # Use search_memory to find relevant context
            relevant_memories_str = await tools['search_memory'](query=user_message, limit=50)
            
            # Handle different response formats
            relevant_memories = []
            if relevant_memories_str and relevant_memories_str.strip():
                try:
                    relevant_memories = json.loads(relevant_memories_str)
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse search_memory JSON response: {relevant_memories_str[:100]}...")
                    relevant_memories = []
            
            return {
                "relevant_memories": relevant_memories,
                "relevance_count": len(relevant_memories)
            }
            
        except Exception as e:
            logger.error(f"Error getting query relevant context: {e}")
            return {"error": str(e)}
    
    async def _process_memory_intelligently(
        self, 
        memorable_content: str, 
        user_id: str, 
        client_name: str
    ) -> Dict:
        """
        Use AI to intelligently process the user message for memorable content.
        Uses background processing to avoid blocking the response.
        """
        try:
            # This function is now simpler as the decision is made by the planner
                tools = self._get_tools()
                
                # Add memory in background (fire and forget)
                asyncio.create_task(self._add_memory_background(
                    memorable_content, user_id, client_name
                ))
                
                return {
                    "memory_added": True,
                    "content": memorable_content,
                    "processing": "background",
                "ai_reasoning": "AI planner determined this contains memorable personal information"
                }
                
        except Exception as e:
            logger.error(f"Error processing memory intelligently: {e}")
            return {"error": str(e), "memory_added": False}
    
    async def _ai_memory_analysis(self, user_message: str) -> Dict:
        """
        Use Gemini 2.5 Flash to intelligently analyze if message contains memorable content.
        Returns analysis with decision and extracted content.
        """
        try:
            gemini = self._get_gemini()
            
            prompt = f"""Analyze this message to determine if it contains NEW PERSONAL INFORMATION worth remembering in a personal memory system.

USER MESSAGE: "{user_message}"

ONLY SAVE if the message contains NEW INFORMATION ABOUT THE USER:
- Personal facts (name, job, location, background, physical attributes)
- Preferences and opinions (likes, dislikes, beliefs, values)
- Goals, plans, and aspirations
- Important life events or experiences  
- Skills, expertise, and knowledge areas
- Relationships and connections
- Explicit requests to remember something ("remember that I...")

DO NOT SAVE these types of messages:
- Questions asking for information ("What's my eye color?", "Where do I work?", "What do I like?")
- Requests for help or assistance ("Help me with...", "Can you...")
- General knowledge questions ("What is...", "How does...")
- Casual conversation without new personal info ("Thanks", "OK", "That's cool")
- Temporary states (current mood, today's weather)
- Commands or instructions without personal context

CRITICAL: If the message is asking ABOUT the user rather than TELLING you about the user, it should be SKIPPED.

RESPONSE FORMAT:
Decision: REMEMBER or SKIP
Content: [If REMEMBER, extract the specific memorable information. If SKIP, explain why.]

Example 1 - REMEMBER:
User Message: "I have a blue shirt"
Decision: REMEMBER
Content: User owns a blue shirt

Example 2 - SKIP:
User Message: "What's my eye color?"
Decision: SKIP
Content: Question asking for information about user, contains no new personal information

Example 3 - SKIP:
User Message: "Help me write an email"
Decision: SKIP
Content: Request for assistance, no personal information provided
"""
            
            response = await gemini.generate_response(prompt)
            
            result = response.strip()
            
            # Parse the response
            lines = result.split('\n')
            decision_line = next((line for line in lines if line.startswith('Decision:')), '')
            content_line = next((line for line in lines if line.startswith('Content:')), '')
            
            should_remember = 'REMEMBER' in decision_line.upper()
            content = content_line.replace('Content:', '').strip() if content_line else user_message
            
            logger.info(f"AI memory analysis: '{user_message[:30]}...' -> {'REMEMBER' if should_remember else 'SKIP'}")
            
            return {
                "should_remember": should_remember,
                "content": content,
                "original_message": user_message
            }
            
        except Exception as e:
            logger.error(f"Error in AI memory analysis: {e}")
            # Fallback to simple heuristic
            simple_check = any(indicator in user_message.lower() for indicator in 
                             ['i am', 'i\'m', 'my ', 'i like', 'i work', 'i live'])
            return {
                "should_remember": simple_check,
                "content": user_message if simple_check else "",
                "original_message": user_message
            }
    
    def _extract_memorable_content(self, user_message: str) -> str:
        """
        Extract the most memorable/important content from the user message.
        """
        # For now, return the full message, but could be enhanced with NLP
        # to extract specific facts, preferences, or key information
        return user_message.strip()
    
    async def _ai_extract_themes_from_memories(self, memories: List[Dict]) -> List[str]:
        """
        Use Gemini 2.5 Flash to intelligently extract themes from recent memories.
        """
        try:
            if not memories:
                return []
            
            # Combine memory content
            memory_texts = []
            for memory in memories[:15]:  # Look at more memories for better analysis
                if isinstance(memory, dict):
                    content = memory.get('memory', memory.get('content', ''))
                    if content:
                        memory_texts.append(content)
            
            if not memory_texts:
                return []
            
            combined_text = "\n".join(memory_texts)
            
            # Limit text length for API efficiency
            if len(combined_text) > 3000:
                combined_text = combined_text[:3000] + "..."
            
            gemini = self._get_gemini()
            
            prompt = f"""Analyze these recent memories and extract the main themes/topics that represent what this person is focused on or interested in.

MEMORIES:
{combined_text}

Extract 3-5 concise theme keywords that capture the main areas of focus, interests, or activities. Themes should be:
- Single words or short phrases (1-2 words)
- Focused on key life areas, interests, or activities
- Representative of recurring patterns in the memories

Examples of good themes: work, technology, health, travel, learning, family, goals, creativity, entrepreneurship

Return ONLY the theme words separated by commas, no explanations.

Example output: work, technology, fitness, travel, learning"""
            
            response = await gemini.generate_response(prompt)
            
            result = response.strip()
            themes = [theme.strip() for theme in result.split(',') if theme.strip()]
            
            # Limit to 5 themes and clean them
            themes = themes[:5]
            themes = [theme.lower().replace(' ', '_') for theme in themes if len(theme) > 1]
            
            logger.info(f"AI extracted themes: {themes}")
            return themes
            
        except Exception as e:
            logger.error(f"Error in AI theme extraction: {e}")
            return ["recent_context"]  # Fallback theme
    
    def _summarize_profile(self, profile_responses: List[Dict]) -> str:
        """
        Create a brief summary from profile responses.
        """
        try:
            if not profile_responses:
                return "No profile information available"
            
            # Extract key information from responses
            summary_parts = []
            
            for response in profile_responses:
                answer = response.get('answer', '')
                if answer and not answer.startswith('Error') and len(answer) > 10:
                    # Extract first sentence or key phrase
                    first_sentence = answer.split('.')[0].strip()
                    if len(first_sentence) > 10 and len(first_sentence) < 100:
                        summary_parts.append(first_sentence)
            
            if summary_parts:
                return "; ".join(summary_parts[:2])  # Top 2 insights
            else:
                return "Building your profile from conversations"
                
        except Exception as e:
            logger.error(f"Error summarizing profile: {e}")
            return "Profile information processing"

    async def _ai_create_memory_plan(self, user_message: str) -> Dict:
        """
        Use AI to decide ONLY if a memory should be saved and what to save.
        """
        gemini = self._get_gemini()
        prompt = f"""Analyze this message to determine if it contains new, personally-relevant information worth saving to a long-term memory.

USER MESSAGE: "{user_message}"

MEMORABLE CONTENT includes:
- Personal facts (name, job, location, background)
- Preferences and opinions (likes, dislikes, beliefs)
- Goals, plans, and aspirations
- Explicit requests to remember something

NOT MEMORABLE:
- Simple questions
- General requests for help
- Casual conversation without new personal information ("thanks", "got it", "that's cool")

RESPONSE FORMAT (JSON):
{{
  "should_save_memory": boolean,
  "memorable_content": "the extracted information to save, if true, otherwise null."
}}

Example 1:
User Message: "I live in Paris and work as a designer."
{{
  "should_save_memory": true,
  "memorable_content": "User lives in Paris and works as a designer."
}}

Example 2:
User Message: "what time is it?"
{{
  "should_save_memory": False,
  "memorable_content": null
}}
"""
        try:
            response_text = await gemini.generate_response(prompt)
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if not json_match:
                logger.error(f"AI memory planner did not return valid JSON. Response: {response_text}")
                return {"should_save_memory": False, "memorable_content": None}
            plan_str = json_match.group(0)
            plan = json.loads(plan_str)
            return plan
        except (json.JSONDecodeError, Exception) as e:
            logger.error(f"Error creating AI memory plan: {e}", exc_info=True)
            return {"should_save_memory": False, "memorable_content": None}

    async def _build_fresh_context(
        self, 
        user_message: str, 
        user_id: str, 
        client_name: str
    ) -> Dict:
        """
        Builds a concise, intelligent context primer for new conversations.
        """
        try:
            # For a new chat, get a user profile summary and recent themes
            tasks = {
                "user_profile": self._get_user_profile(user_id, self._get_tools()),
                "working_memory": self._get_working_memory(user_id, self._get_tools())
            }
            
            results = await asyncio.gather(*tasks.values(), return_exceptions=True)
            
            final_context = {"type": "fresh_context"}
            for context_type, result in zip(tasks.keys(), results):
                 if isinstance(result, Exception):
                    final_context[context_type] = {"error": str(result)}
                 else:
                    final_context[context_type] = result
            
            return final_context
            
        except Exception as e:
            logger.error(f"Error building fresh context: {e}")
            return {"error": str(e), "type": "fresh_context"}

    async def _get_contextual_memories(
        self, 
        user_message: str, 
        user_id: str, 
        client_name: str
    ) -> Dict:
        """
        Enhanced contextual memory retrieval based on the user's message.
        Uses semantic search and selective retrieval for better context.
        """
        try:
            # For a new chat, get a user profile summary and recent themes
            tasks = {
                "user_profile": self._get_user_profile(user_id, self._get_tools()),
                "working_memory": self._get_working_memory(user_id, self._get_tools())
            }
            
            results = await asyncio.gather(*tasks.values(), return_exceptions=True)
            context_data = dict(zip(tasks.keys(), results))
            
            # Filter out any exceptions
            clean_results = {}
            for key, result in context_data.items():
                if isinstance(result, Exception):
                    logger.warning(f"Error in {key}: {result}")
                    clean_results[key] = {}
                else:
                    clean_results[key] = result
                    
            return clean_results
            
        except Exception as e:
            logger.error(f"Error in contextual memory retrieval: {e}")
            return {}

    async def _get_cached_narrative(self, user_id: str) -> Optional[str]:
        """
        Check for cached user narrative that's still fresh.
        Returns narrative content if found and fresh, None otherwise.
        """
        try:
            db = SessionLocal()
            try:
                # Get user by user_id string
                from app.models import User
                user = db.query(User).filter(User.user_id == user_id).first()
                if not user:
                    logger.warning(f"User not found for user_id: {user_id}")
                    return None
                
                # Check for existing narrative
                narrative = db.query(UserNarrative).filter(UserNarrative.user_id == user.id).first()
                if not narrative:
                    logger.info(f"📝 [Narrative Cache] No cached narrative found for user {user_id}")
                    return None
                
                # Check if narrative is fresh (within TTL)
                now = datetime.now(narrative.generated_at.tzinfo or datetime.timezone.utc)
                age_days = (now - narrative.generated_at).days
                
                if age_days <= NARRATIVE_TTL_DAYS:
                    logger.info(f"✅ [Narrative Cache] Found fresh narrative for user {user_id} (age: {age_days} days)")
                    return narrative.narrative_content
                else:
                    logger.info(f"⏰ [Narrative Cache] Found stale narrative for user {user_id} (age: {age_days} days)")
                    return None
                    
            finally:
                db.close()
        except Exception as e:
            logger.error(f"❌ [Narrative Cache] Error checking cached narrative for user {user_id}: {e}")
            return None
    
    async def _save_narrative_to_cache(self, user_id: str, narrative_content: str):
        """
        Save a narrative to the cache in the background.
        This is called as a background task to avoid blocking the user.
        """
        try:
            db = SessionLocal()
            try:
                # Get user by user_id string
                from app.models import User
                user = db.query(User).filter(User.user_id == user_id).first()
                if not user:
                    logger.warning(f"Cannot save narrative - user not found for user_id: {user_id}")
                    return
                
                # Delete any existing narrative for this user
                existing = db.query(UserNarrative).filter(UserNarrative.user_id == user.id).first()
                if existing:
                    db.delete(existing)
                    logger.info(f"Replaced existing narrative for user {user_id}")
                
                # Create new narrative
                narrative = UserNarrative(
                    user_id=user.id,
                    narrative_content=narrative_content,
                    generated_at=datetime.utcnow()
                )
                db.add(narrative)
                db.commit()
                logger.info(f"✅ Saved narrative to cache for user {user_id} (length: {len(narrative_content)} chars)")
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Failed to save narrative to cache for user {user_id}: {e}")

    async def _generate_and_cache_narrative(self, user_id: str, memories_text: str, background_tasks: BackgroundTasks):
        """
        Generate a new narrative using Gemini 2.5 Pro and cache it.
        This is run as a background task for maximum quality without blocking the user.
        Enhanced with comprehensive debugging for production troubleshooting.
        """
        def background_narrative_generation():
            import traceback
            task_start_time = datetime.utcnow()
            logger.info(f"🤖 [Background Task] Starting narrative generation for user {user_id} at {task_start_time}")
            
            try:
                # Enhanced logging for background task execution
                logger.info(f"🔧 [Background Task] Setting up async event loop for user {user_id}")
                
                # Use async context for Gemini Pro generation
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                logger.info(f"✅ [Background Task] Event loop created successfully for user {user_id}")
                
                try:
                    # Log memory text details
                    memory_length = len(memories_text)
                    logger.info(f"📊 [Background Task] Processing {memory_length} chars of memories for user {user_id}")
                    
                    # Generate high-quality narrative with Pro model
                    logger.info(f"🤖 [Background Task] Calling Gemini 2.5 Pro API for user {user_id}")
                    api_start_time = datetime.utcnow()
                    
                    narrative = loop.run_until_complete(
                        self._get_gemini().generate_narrative_pro(memories_text)
                    )
                    
                    api_end_time = datetime.utcnow()
                    api_duration = (api_end_time - api_start_time).total_seconds()
                    
                    if narrative and narrative.strip():
                        logger.info(f"✅ [Background Task] Gemini API successful for user {user_id} (duration: {api_duration:.2f}s, response length: {len(narrative)} chars)")
                        
                        # Save to cache
                        logger.info(f"💾 [Background Task] Attempting to save narrative to database for user {user_id}")
                        save_start_time = datetime.utcnow()
                        
                        loop.run_until_complete(
                            self._save_narrative_to_cache(user_id, narrative)
                        )
                        
                        save_end_time = datetime.utcnow()
                        save_duration = (save_end_time - save_start_time).total_seconds()
                        
                        task_end_time = datetime.utcnow()
                        total_duration = (task_end_time - task_start_time).total_seconds()
                        
                        logger.info(f"✅ [Background Task] Database save completed for user {user_id} (save duration: {save_duration:.2f}s)")
                        logger.info(f"🎉 [Background Task] COMPLETED successfully for user {user_id} (total duration: {total_duration:.2f}s)")
                    else:
                        logger.error(f"❌ [Background Task] Gemini returned empty narrative for user {user_id} after {api_duration:.2f}s")
                        
                except Exception as inner_e:
                    logger.error(f"💥 [Background Task] Inner exception for user {user_id}: {str(inner_e)}")
                    logger.error(f"💥 [Background Task] Inner traceback for user {user_id}: {traceback.format_exc()}")
                finally:
                    logger.info(f"🔄 [Background Task] Closing event loop for user {user_id}")
                    loop.close()
                    
            except Exception as e:
                task_end_time = datetime.utcnow()
                task_duration = (task_end_time - task_start_time).total_seconds()
                logger.error(f"💥 [Background Task] FAILED for user {user_id} after {task_duration:.2f}s: {str(e)}")
                logger.error(f"💥 [Background Task] Full traceback for user {user_id}: {traceback.format_exc()}")
        
        logger.info(f"🔄 [Smart Cache] Adding background task to queue for user {user_id}")
        background_tasks.add_task(background_narrative_generation)
        logger.info(f"✅ [Smart Cache] Background task successfully queued for user {user_id}")

    async def _get_user_memories(self, user_id: str, limit: int = 50) -> List[str]:
        """
        Get user memories from the database for narrative generation.
        """
        try:
            db = SessionLocal()
            try:
                # Get user by user_id string
                from app.models import User
                user = db.query(User).filter(User.user_id == user_id).first()
                if not user:
                    return []
                
                # Get user's active memories
                memories = db.query(Memory).filter(
                    Memory.user_id == user.id,
                    Memory.state == 'active'
                ).order_by(Memory.created_at.desc()).limit(limit).all()
                
                return [memory.content for memory in memories]
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Error getting user memories for {user_id}: {e}")
            return []

    async def run_deep_analysis_and_save_as_memory(
        self,
        user_message: str,
        user_id: str,
        client_name: str
    ):
        """
        Runs a deep, AI-powered analysis in the background.
        NOTE: This function should NOT save memories to avoid duplication with the main orchestration flow.
        """
        try:
            logger.info(f"🧠 [Async Analysis BG] Starting deep analysis for user {user_id} on message: '{user_message[:50]}...'")
            
            # Generate a unique interaction ID to prevent duplicate memory saves
            import hashlib
            interaction_id = f"{user_id}_{hashlib.md5(user_message.encode()).hexdigest()}"
            
            # Use standard orchestration but with interaction ID to prevent duplicate saves
            analysis_result = await self._standard_orchestration(
                user_message=user_message,
                user_id=user_id,
                client_name=client_name,
                is_new_conversation=False,
                interaction_id=interaction_id  # This prevents duplicate memory saves
            )

            # Analysis complete - context provided without duplicate memory save
            if analysis_result and "Error" not in analysis_result:
                logger.info(f"✅ [Async Analysis BG] Deep analysis completed for user {user_id}. Context provided without duplicate memory save.")
            else:
                logger.warning(f"⚠️ [Async Analysis BG] Deep analysis did not produce a valid result for user {user_id}.")

        except Exception as e:
            logger.error(f"❌ [Async Analysis BG] Failed for user {user_id}: {e}", exc_info=True)

    async def triage_and_save_memory_background(
        self,
        user_message: str,
        user_id: str,
        client_name: str
    ):
        """
        Intelligently analyzes a message and saves it to memory ONLY if it
        contains salient, personal information.
        
        Uses content-based deduplication to prevent saving identical content multiple times.
        """
        try:
            # 1. Use the lightweight AI analysis to check if the message is memorable.
            analysis = await self._ai_memory_analysis(user_message)

            # 2. If the analysis confirms the content is memorable, save it.
            if analysis.get("should_remember"):
                memorable_content = analysis.get("content", user_message)
                
                # 3. Content-based deduplication - check if we've already saved this exact content
                import hashlib
                content_hash = f"{user_id}_{hashlib.md5(memorable_content.encode()).hexdigest()}"
                
                if content_hash in self._saved_content_hashes:
                    logger.info(f"🚫 [Content Dedupe] Already saved this content for user {user_id}: '{memorable_content[:30]}...'")
                    return
                
                # Mark this content as saved
                self._saved_content_hashes.add(content_hash)
                
                # Clean up old hashes (keep last 100 to prevent memory leak)
                if len(self._saved_content_hashes) > 100:
                    hashes_list = list(self._saved_content_hashes)
                    self._saved_content_hashes = set(hashes_list[-50:])
                    logger.debug(f"🧹 [Content Dedupe] Cleaned up content hash tracking")
                
                logger.info(f"💾 [Async Triage] Message deemed memorable. Saving content for user {user_id}: '{memorable_content[:50]}...'")
                
                # Add the memory to the database.
                await self._add_memory_background(
                    content=memorable_content,
                    user_id=user_id,
                    client_name=client_name,
                    priority=False # Triage-based memories are normal priority
                )
                logger.info(f"✅ [Async Triage] Successfully saved memorable content for user {user_id}.")
            else:
                # 3. If not memorable, log it and do nothing.
                logger.info(f"🧐 [Async Triage] Message deemed not memorable for user {user_id}. No action taken.")

        except Exception as e:
            logger.error(f"❌ [Async Triage] Triage and save failed for user {user_id}: {e}", exc_info=True)


# Global orchestrator instance
_orchestrator = None

def get_smart_orchestrator() -> SmartContextOrchestrator:
    """Get or create the global smart orchestrator instance."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = SmartContextOrchestrator()
    return _orchestrator

def clear_context_cache():
    """Clear the context cache (useful for testing)"""
    from app.utils.mcp_modules.cache_manager import clear_context_cache as clear_cache
    clear_cache()

def get_cache_stats() -> Dict:
    """Get context cache statistics"""
    from app.utils.mcp_modules.cache_manager import get_cache_stats as get_stats
    return get_stats() 