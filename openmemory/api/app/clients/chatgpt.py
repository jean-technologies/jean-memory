import json
from typing import Dict, Any, List
import logging
import datetime

from .base import BaseClient, BaseClientProfile
from app.config.tool_config import get_tools_for_client

logger = logging.getLogger(__name__)

# Simple in-memory cache for deep analyses
deep_analysis_cache: Dict[str, Dict] = {}
DEEP_CACHE_TTL = 1800  # 30 minutes

# New: Session-based deep analysis cache for ChatGPT hybrid approach
chatgpt_deep_analysis_cache: Dict[str, Dict] = {}


async def handle_chatgpt_search(user_id: str, query: str):
    """
    DIRECT DEEP MEMORY APPROACH for ChatGPT search.
    
    Based on testing, ChatGPT can handle responses up to 47+ seconds, so we can 
    directly return comprehensive deep memory analysis instead of the hybrid approach.
    
    This gives ChatGPT immediate access to the full deep analysis without complexity.
    """
    try:
        # Track ChatGPT search usage (only if private analytics available)
        try:
            from app.utils.private_analytics import track_tool_usage
            track_tool_usage(
                user_id=user_id,
                tool_name='chatgpt_search',
                properties={
                    'client_name': 'chatgpt',
                    'query_length': len(query),
                    'is_chatgpt': True
                }
            )
        except (ImportError, Exception):
            pass
        
        # 🚀 DIRECT DEEP MEMORY TEST: Call deep analysis directly (testing timeout limits)
        logger.info(f"🧠 DIRECT: Starting deep memory analysis for ChatGPT query: '{query}' (user: {user_id})")
        
        deep_analysis_result = await _deep_memory_query_impl(
            search_query=query, 
            supa_uid=user_id, 
            client_name="chatgpt",
            memory_limit=10,  # Reasonable limit for comprehensive results
            chunk_limit=8,    # Good balance of speed vs depth
            include_full_docs=True
        )
        
        # 🎯 SCHEMA COMPLIANT: Return deep analysis as single article (fits required schema)
        citation_url = "https://jeanmemory.com"
        
        article = {
            "id": "1",  # Single comprehensive result
            "title": f"Deep Analysis: {query[:50]}{'...' if len(query) > 50 else ''}",
            "text": deep_analysis_result,  # 🧠 Full comprehensive deep analysis
            "url": citation_url
        }
        
        # sobannon's exact working response format
        search_response = {"results": [article]}
        
        logger.info(f"🧠 DIRECT: Deep memory analysis completed for query: '{query}' (user: {user_id})")
        
        # Return sobannon's exact format: structuredContent + content
        return {
            "structuredContent": search_response,  # For programmatic access
            "content": [
                {
                    "type": "text", 
                    "text": json.dumps(search_response)  # For display
                }
            ]
        }

    except Exception as e:
        logger.error(f"ChatGPT search error: {e}", exc_info=True)
        # Return empty results in the same format
        empty_response = {"results": []}
        return {
            "structuredContent": empty_response,
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(empty_response)
                }
            ]
        }

async def handle_chatgpt_fetch(user_id: str, memory_id: str):
    """
    DIRECT DEEP MEMORY: Simple fetch for single comprehensive analysis result
    """
    try:
        # Track ChatGPT fetch usage (only if private analytics available)
        try:
            from app.utils.private_analytics import track_tool_usage
            track_tool_usage(
                user_id=user_id,
                tool_name='chatgpt_fetch',
                properties={
                    'client_name': 'chatgpt',
                    'memory_id': memory_id,
                    'is_chatgpt': True
                }
            )
        except (ImportError, Exception):
            pass
        
        # With direct approach, we only have one result with ID "1" containing the full analysis
        if memory_id == "1":
            citation_url = "https://jeanmemory.com"
            
            article = {
                "id": "1",
                "title": "Deep Memory Analysis - Full Context",
                "text": "The comprehensive deep memory analysis was provided in the search results. This fetch confirms the analysis covers all available memories, documents, and insights about the query.",
                "url": citation_url,
                "metadata": {"type": "deep_analysis_confirmation"}
            }
            
            logger.info(f"🧠 DIRECT FETCH: Returning deep analysis confirmation for user {user_id}")
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(article)
                    }
                ],
                "structuredContent": article
            }
        else:
            # No other IDs exist in direct approach
            raise ValueError("unknown id")
            
    except Exception as e:
        logger.error(f"ChatGPT direct fetch error: {e}", exc_info=True)
        raise ValueError("unknown id")

class ChatGPTClient(BaseClient):
    """Client for handling requests from ChatGPT, which uses a 'function' calling format."""
    
    def get_tools(self) -> list:
        """
        Returns a list of tools specifically curated for the ChatGPT client,
        fetching them from the centralized tool configuration and formatting
        them into the JSON schema that ChatGPT expects.
        """
        tool_defs = get_tools_for_client(self.get_client_name())
        
        # ChatGPT expects a 'functions' key with a list of schemas.
        # The tool definitions from our config are already in the correct schema format.
        return tool_defs

    def get_client_name(self) -> str:
        return "chatgpt"

    def get_client_profile(self) -> BaseClientProfile:
        return ChatGPTProfile()

class ChatGPTProfile(BaseClientProfile):
    """
    Handles the specific prompt and response formatting required by the
    ChatGPT function-calling API.
    """
    def get_tool_prompt(self, tools: List[Dict[str, Any]]) -> str:
        """Formats the tools into the JSON structure expected by ChatGPT's API."""
        if not tools:
            return "You have no tools available."
        
        # ChatGPT expects a JSON string representation of the functions.
        return json.dumps(tools, indent=2)

    async def handle_tool_call(
        self, tool_name: str, tool_args: dict, user_id: str
    ) -> Any:
        """Handles a tool call from ChatGPT."""
        # The base handler is sufficient as no special argument handling is needed.
        return await super().handle_tool_call(tool_name, tool_args, user_id) 