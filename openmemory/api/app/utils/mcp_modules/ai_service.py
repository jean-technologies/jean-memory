"""
AI service layer for MCP orchestration.
Handles AI-powered context planning and analysis using Gemini.
"""

import asyncio
import json
import logging
import re
from typing import Dict, List

logger = logging.getLogger(__name__)


class MCPAIService:
    """AI service for MCP orchestration using Gemini."""
    
    def __init__(self):
        self._gemini_service = None
    
    def _get_gemini(self):
        """Lazy load Gemini service"""
        if self._gemini_service is None:
            from app.utils.gemini import GeminiService
            self._gemini_service = GeminiService()
        return self._gemini_service
    
    async def create_context_plan(self, user_message: str) -> Dict:
        """
        Uses AI to create a comprehensive context engineering plan for continuing conversations.
        This is the core "brain" of the orchestrator - implementing top-down context theory.
        """
        gemini = self._get_gemini()
        
        # Let the AI determine the appropriate strategy based on the message content
        # Safely handle user message in JSON by escaping quotes
        safe_message = user_message.replace('"', '\\"').replace('\n', '\\n')
        
        prompt = f"""You are the intelligent context orchestrator for a personal memory system. A user has sent this message, and you've been called because there is likely relevant context about this user's life stored in their memory database.

USER MESSAGE: "{safe_message}"

Your role is to determine the appropriate depth of memory context retrieval needed for AI inference. Think about what level of personal context would be most helpful for understanding and responding to this user intelligently.

Choose the optimal context strategy:

"relevant_context" (Level 2) - Focused memory search
When the query can be answered with specific, targeted memories. Best for direct questions about known facts, recent events, or specific topics the user has mentioned before.

"deep_understanding" (Level 3) - Broader memory analysis with AI synthesis  
When the query requires understanding patterns, relationships, or broader context about the user's life, work, or preferences. Use when you need to synthesize multiple aspects of who they are.

"comprehensive_analysis" (Level 4) - Maximum depth with documents and extensive memory
When the query touches on fundamental aspects of the user's identity, values, beliefs, or requires research-level depth. Use for questions about who they are, what they believe, complex reasoning about their background, or comprehensive exploration of topics.

Consider:
- What does the user really want to know?
- How much personal context is needed to respond thoughtfully?
- Is this about surface facts or deeper understanding?

Also determine if this message contains content worth remembering for future context.

Respond with JSON only:
{{
  "context_strategy": "choose one strategy above",
  "search_queries": ["1-3 specific search terms for memory retrieval"],
  "should_save_memory": true/false,
  "memorable_content": "key content to remember for future context, or null"
}}"""

        try:
            # Increased timeout to 12 seconds to handle occasional slow responses
            response_text = await asyncio.wait_for(
                gemini.generate_response(prompt),
                timeout=12.0
            )
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                plan = json.loads(json_match.group())
                logger.info(f"✅ AI Context Plan: {plan}")
                return plan
            else:
                logger.warning("No JSON found in AI response, using fallback")
                return self._get_fallback_plan(user_message)
                
        except asyncio.TimeoutError:
            logger.warning(f"⏰ AI planner timed out after 12s, using fallback")
            return self._get_fallback_plan(user_message)
        except Exception as e:
            logger.error(f"❌ Error creating AI context plan: {e}. Defaulting to simple search.", exc_info=True)
            return self._get_fallback_plan(user_message)
    
    def _get_fallback_plan(self, user_message: str) -> Dict:
        """Fast fallback when AI planning fails or times out - for continuing conversations only"""
        
        # Simple heuristic-based fallback without keywords
        # Longer, more complex messages likely need deeper context
        message_length = len(user_message)
        question_complexity = '?' in user_message and len(user_message.split()) > 5
        
        if message_length > 100 or question_complexity:
            strategy = "deep_understanding"  # Default to medium depth for complex queries
        elif message_length > 20:
            strategy = "relevant_context"    # Basic search for simple queries
        else:
            strategy = "relevant_context"    # Short messages get basic search
            
        return {
            "context_strategy": strategy,
            "search_queries": [user_message[:50]],  # Simple search using first 50 chars
            "should_save_memory": len(user_message) > 30,  # Save substantial messages  
            "memorable_content": user_message if len(user_message) > 30 else None
        }
    
    async def analyze_memory_content(self, user_message: str) -> Dict:
        """Analyze user message for memory extraction and categorization"""
        gemini = self._get_gemini()
        
        prompt = f"""Analyze this message for memory extraction. Respond with JSON only:

Message: "{user_message}"

{{
  "should_save": true/false,
  "memorable_content": "extracted key content or null",
  "categories": ["category1", "category2"],
  "priority": "high/medium/low",
  "summary": "brief summary"
}}"""

        try:
            response_text = await asyncio.wait_for(
                gemini.generate_response(prompt),
                timeout=8.0
            )
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                analysis = json.loads(json_match.group())
                return analysis
            else:
                logger.warning("No JSON found in memory analysis response")
                return self._get_fallback_memory_analysis(user_message)
                
        except Exception as e:
            logger.error(f"❌ Error in memory analysis: {e}")
            return self._get_fallback_memory_analysis(user_message)
    
    def _get_fallback_memory_analysis(self, user_message: str) -> Dict:
        """Fallback memory analysis when AI fails"""
        # Simple heuristic-based analysis
        should_save = len(user_message) > 20 and any(
            keyword in user_message.lower() 
            for keyword in ['remember', 'important', 'note', 'save', 'learned']
        )
        
        return {
            "should_save": should_save,
            "memorable_content": user_message if should_save else None,
            "categories": ["general"],
            "priority": "medium",
            "summary": user_message[:100] + "..." if len(user_message) > 100 else user_message
        }
    
    async def extract_themes_from_memories(self, memories: List[Dict]) -> List[str]:
        """Extract themes from a list of memories using AI"""
        if not memories:
            return []
        
        gemini = self._get_gemini()
        
        # Prepare memory content for analysis
        memory_texts = []
        for mem in memories[:10]:  # Limit to 10 memories for performance
            content = mem.get('content', '') or mem.get('memory', '')
            if content:
                memory_texts.append(content[:200])  # Truncate for performance
        
        if not memory_texts:
            return []
        
        prompt = f"""Extract 3-5 main themes from these memories. Respond with JSON only:

Memories:
{chr(10).join(f"- {text}" for text in memory_texts)}

{{
  "themes": ["theme1", "theme2", "theme3"]
}}"""

        try:
            response_text = await asyncio.wait_for(
                gemini.generate_response(prompt),
                timeout=10.0
            )
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                return result.get('themes', [])
            else:
                logger.warning("No JSON found in theme extraction response")
                return ["general", "personal", "work"]
                
        except Exception as e:
            logger.error(f"❌ Error extracting themes: {e}")
            return ["general", "personal", "work"]
    
    async def create_memory_plan(self, user_message: str) -> Dict:
        """Create a plan for memory processing"""
        gemini = self._get_gemini()
        
        prompt = f"""Create a memory processing plan. Respond with JSON only:

Message: "{user_message}"

{{
  "action": "save/ignore/process",
  "priority": "high/medium/low",
  "categories": ["category1", "category2"],
  "extract_key_points": true/false,
  "reason": "brief explanation"
}}"""

        try:
            response_text = await asyncio.wait_for(
                gemini.generate_response(prompt),
                timeout=8.0
            )
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                plan = json.loads(json_match.group())
                return plan
            else:
                logger.warning("No JSON found in memory plan response")
                return self._get_fallback_memory_plan(user_message)
                
        except Exception as e:
            logger.error(f"❌ Error creating memory plan: {e}")
            return self._get_fallback_memory_plan(user_message)
    
    def _get_fallback_memory_plan(self, user_message: str) -> Dict:
        """Fallback memory plan when AI fails"""
        return {
            "action": "save" if len(user_message) > 20 else "ignore",
            "priority": "medium",
            "categories": ["general"],
            "extract_key_points": True,
            "reason": "fallback heuristic"
        }