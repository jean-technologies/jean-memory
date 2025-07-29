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
    
    async def create_context_plan(self, user_message: str, is_new_conversation: bool) -> Dict:
        """
        Uses AI to create a comprehensive context engineering plan.
        This is the core "brain" of the orchestrator - implementing top-down context theory.
        """
        gemini = self._get_gemini()
        
        # Let the AI determine the appropriate strategy based on the message content
        # Safely handle user message in JSON by escaping quotes
        safe_message = user_message.replace('"', '\\"').replace('\n', '\\n')
        
        prompt = f"""Analyze this message for context engineering. Choose the appropriate strategy:

Message: "{safe_message}"
New conversation: {is_new_conversation}

Context strategies:
- "relevant_context": For continuing conversations, focused search
- "deep_understanding": For new conversations needing broad context  
- "comprehensive_analysis": For requests asking for deep analysis, beliefs, philosophy, "what would I say", etc.

Respond with JSON only:
{{
  "context_strategy": "choose one of the three strategies above",
  "search_queries": ["1-3 specific search terms"],
  "should_save_memory": true/false,
  "memorable_content": "key content to remember or null"
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
                return self._get_fallback_plan(user_message, is_new_conversation)
                
        except asyncio.TimeoutError:
            logger.warning(f"⏰ AI planner timed out after 12s, using fallback")
            return self._get_fallback_plan(user_message, is_new_conversation)
        except Exception as e:
            logger.error(f"❌ Error creating AI context plan: {e}. Defaulting to simple search.", exc_info=True)
            return self._get_fallback_plan(user_message, is_new_conversation)
    
    def _get_fallback_plan(self, user_message: str, is_new_conversation: bool) -> Dict:
        """Fast fallback when AI planning fails or times out"""
        
        # Detect if user wants deeper analysis
        deep_keywords = [
            'analyze', 'explain', 'understand', 'learn', 'insights', 'patterns',
            'deep', 'deeper', 'comprehensive', 'extensive', 'detailed', 'thorough',
            'beliefs', 'philosophy', 'values', 'what would i say', 'given my',
            'based on my', 'use deep memory', 'use deeper memory', 'what do you know about'
        ]
        wants_deep_analysis = any(keyword in user_message.lower() for keyword in deep_keywords)
        
        # Use same strategy logic as main AI planner
        if is_new_conversation:
            strategy = "deep_understanding"
        elif wants_deep_analysis:
            strategy = "comprehensive_analysis"
        else:
            strategy = "relevant_context"
            
        return {
            "context_strategy": strategy,
            "search_queries": [user_message[:50]],  # Simple search using first 50 chars
            "should_save_memory": is_new_conversation or 'remember' in user_message.lower(),
            "memorable_content": user_message if is_new_conversation or 'remember' in user_message.lower() else None
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