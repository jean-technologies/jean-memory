"""
Comprehensive Memory Analysis - Unified memory decision logic
"""
import hashlib
import time
import logging
from typing import Dict, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class MemoryAnalysisResult:
    """Result of comprehensive memory analysis"""
    should_save: bool
    content: Optional[str]
    original_message: str
    reason: str
    confidence: float
    source: str
    interaction_id: str

class ComprehensiveMemoryAnalyzer:
    """
    Unified memory analysis that combines all memory decision logic.
    
    This replaces the scattered memory analysis across different parts of the system
    with a single, comprehensive analysis that makes one decision per interaction.
    """
    
    def __init__(self, gemini_client):
        self.gemini_client = gemini_client
    
    async def analyze_memory_need(self, user_message: str, user_id: str, interaction_id: str, 
                                context_plan: Optional[Dict] = None) -> MemoryAnalysisResult:
        """
        Comprehensive analysis to determine if and what to save to memory.
        
        Args:
            user_message: The user's message
            user_id: User identifier
            interaction_id: Unique interaction identifier
            context_plan: Optional AI context plan with memory saving hints
            
        Returns:
            MemoryAnalysisResult with decision and extracted content
        """
        
        logger.info(f"🧠 [Memory Analysis] Starting comprehensive analysis for interaction {interaction_id}")
        
        try:
            # Step 1: AI Triage Analysis (primary decision maker)
            triage_result = await self._ai_triage_analysis(user_message)
            
            if not triage_result['should_remember']:
                return MemoryAnalysisResult(
                    should_save=False,
                    content=None,
                    original_message=user_message,
                    reason=f"AI_triage_skip: {triage_result.get('reasoning', 'Not memorable')}",
                    confidence=0.9,  # High confidence in AI decision to skip
                    source='ai_triage',
                    interaction_id=interaction_id
                )
            
            # Step 2: Check context plan hint (secondary validation)
            context_hint = self._extract_context_memory_hint(context_plan)
            
            # Step 3: Content quality check
            quality_score = self._assess_content_quality(triage_result['content'])
            
            if quality_score < 0.3:  # Low quality content threshold
                return MemoryAnalysisResult(
                    should_save=False,
                    content=None,
                    original_message=user_message,
                    reason=f"Low_quality_content: score={quality_score:.2f}",
                    confidence=0.8,
                    source='quality_filter',
                    interaction_id=interaction_id
                )
            
            # Step 4: Determine final content to save
            final_content = self._determine_final_content(
                triage_content=triage_result['content'],
                original_message=user_message,
                context_hint=context_hint
            )
            
            logger.info(f"✅ [Memory Analysis] Approved save for interaction {interaction_id}: {final_content[:50]}...")
            
            return MemoryAnalysisResult(
                should_save=True,
                content=final_content,
                original_message=user_message,
                reason="AI_triage_approved",
                confidence=quality_score,
                source='comprehensive_analysis',
                interaction_id=interaction_id
            )
            
        except Exception as e:
            logger.error(f"❌ [Memory Analysis] Error in analysis for interaction {interaction_id}: {e}")
            
            # Fallback to conservative heuristic
            fallback_result = self._fallback_heuristic_analysis(user_message)
            
            return MemoryAnalysisResult(
                should_save=fallback_result['should_save'],
                content=fallback_result.get('content'),
                original_message=user_message,
                reason=f"Fallback_heuristic: {fallback_result['reason']}",
                confidence=0.5,  # Lower confidence for fallback
                source='fallback_heuristic',
                interaction_id=interaction_id
            )
    
    async def _ai_triage_analysis(self, user_message: str) -> Dict:
        """
        AI triage analysis using Gemini to determine if content is memorable.
        
        This is the primary decision maker for memory saving.
        """
        try:
            prompt = f"""Analyze this message to determine if it contains information worth remembering in a personal memory system.

USER MESSAGE: "{user_message}"

MEMORABLE CONTENT includes:
- Personal facts (name, job, location, background, family)
- Preferences and opinions (likes, dislikes, beliefs, values)
- Goals, plans, and aspirations
- Important life events or experiences
- Skills, expertise, and knowledge areas
- Relationships and connections
- Projects, work, or learning activities
- Explicit requests to remember something
- Health, fitness, or personal development information

NOT MEMORABLE:
- Simple questions without personal context
- General requests for help or information
- Casual greetings or conversation fillers
- Temporary states (current mood, weather comments)
- Generic responses or acknowledgments
- Technical questions without personal relevance

RESPONSE FORMAT:
Decision: REMEMBER or SKIP
Content: [If REMEMBER, extract the specific memorable information. If SKIP, explain why.]
Reasoning: [Brief explanation of the decision]

Example 1:
Decision: REMEMBER
Content: User is a software engineer at Google who loves playing tennis on weekends
Reasoning: Contains personal professional and hobby information

Example 2:
Decision: SKIP  
Content: Simple question about weather with no personal information
Reasoning: Generic question without personal context"""
            
            response = await self.gemini_client.generate_response(prompt)
            result = response.strip()
            
            # Parse the response
            lines = result.split('\n')
            decision_line = next((line for line in lines if line.startswith('Decision:')), '')
            content_line = next((line for line in lines if line.startswith('Content:')), '')
            reasoning_line = next((line for line in lines if line.startswith('Reasoning:')), '')
            
            should_remember = 'REMEMBER' in decision_line.upper()
            content = content_line.replace('Content:', '').strip() if content_line else user_message
            reasoning = reasoning_line.replace('Reasoning:', '').strip() if reasoning_line else "No reasoning provided"
            
            logger.info(f"🤖 [AI Triage] '{user_message[:30]}...' -> {'REMEMBER' if should_remember else 'SKIP'} | {reasoning}")
            
            return {
                'should_remember': should_remember,
                'content': content,
                'reasoning': reasoning,
                'original_message': user_message
            }
            
        except Exception as e:
            logger.error(f"Error in AI triage analysis: {e}")
            raise
    
    def _extract_context_memory_hint(self, context_plan: Optional[Dict]) -> Optional[str]:
        """Extract memory saving hint from context plan if available"""
        if not context_plan:
            return None
        
        # Check if context plan suggests saving memory
        should_save = context_plan.get('should_save_memory', False)
        memorable_content = context_plan.get('memorable_content')
        
        if should_save and memorable_content:
            logger.info(f"💡 [Context Hint] Context plan suggests saving: {memorable_content[:50]}...")
            return memorable_content
        
        return None
    
    def _assess_content_quality(self, content: str) -> float:
        """
        Assess the quality of extracted memorable content.
        
        Returns a score from 0.0 to 1.0 where higher scores indicate better quality.
        """
        if not content or content.strip() == "":
            return 0.0
        
        # Length check - too short or too long reduces quality
        length = len(content.strip())
        if length < 10:  # Too short
            length_score = length / 10.0
        elif length > 500:  # Too long
            length_score = max(0.5, 1.0 - (length - 500) / 1000.0)
        else:
            length_score = 1.0
        
        # Content specificity check
        specific_indicators = [
            'i am', 'i\'m', 'my ', 'i like', 'i work', 'i live', 'i have',
            'i prefer', 'i believe', 'i think', 'i want', 'i need'
        ]
        
        specificity_score = 0.0
        content_lower = content.lower()
        for indicator in specific_indicators:
            if indicator in content_lower:
                specificity_score += 0.1
        
        specificity_score = min(1.0, specificity_score)
        
        # Avoid system/technical content
        system_indicators = [
            'error', 'exception', 'debug', 'log', 'system', 'process',
            'function', 'method', 'class', 'variable'
        ]
        
        system_penalty = 0.0
        for indicator in system_indicators:
            if indicator in content_lower:
                system_penalty += 0.2
        
        system_penalty = min(0.5, system_penalty)  # Max 50% penalty
        
        # Final quality score
        quality_score = (length_score * 0.3 + specificity_score * 0.7) - system_penalty
        quality_score = max(0.0, min(1.0, quality_score))
        
        logger.debug(f"📊 [Quality Assessment] Content quality: {quality_score:.2f} (length: {length_score:.2f}, specificity: {specificity_score:.2f}, penalty: {system_penalty:.2f})")
        
        return quality_score
    
    def _determine_final_content(self, triage_content: str, original_message: str, context_hint: Optional[str]) -> str:
        """
        Determine the final content to save based on all analysis inputs.
        
        Priority:
        1. AI triage extracted content (most reliable)
        2. Context hint content (if substantially different)
        3. Original message (fallback)
        """
        
        # Use triage content as primary choice
        if triage_content and triage_content.strip() != "":
            final_content = triage_content.strip()
        else:
            final_content = original_message.strip()
        
        # If context hint provides additional valuable information, consider it
        if context_hint and context_hint != triage_content:
            # Check if context hint adds significant new information
            if len(context_hint) > len(final_content) * 1.5:
                logger.info(f"🔄 [Content Decision] Using context hint over triage content (more comprehensive)")
                final_content = context_hint.strip()
        
        return final_content
    
    def _fallback_heuristic_analysis(self, user_message: str) -> Dict:
        """
        Fallback heuristic analysis when AI triage fails.
        
        Uses simple pattern matching to determine if message should be saved.
        """
        content_lower = user_message.lower()
        
        # Personal indicators
        personal_indicators = [
            'i am', 'i\'m', 'my name is', 'i work', 'i live', 'i like',
            'i hate', 'i prefer', 'i believe', 'i think', 'my job',
            'my hobby', 'my family', 'i have', 'i own', 'i study'
        ]
        
        # Question indicators (usually not memorable)
        question_indicators = [
            'what is', 'how do', 'can you', 'please', 'help me',
            'explain', 'show me', 'tell me'
        ]
        
        personal_score = sum(1 for indicator in personal_indicators if indicator in content_lower)
        question_score = sum(1 for indicator in question_indicators if indicator in content_lower)
        
        # Simple heuristic: if more personal indicators than question indicators, save it
        should_save = personal_score > question_score and personal_score > 0
        
        reason = f"personal_indicators={personal_score}, question_indicators={question_score}"
        
        return {
            'should_save': should_save,
            'content': user_message if should_save else None,
            'reason': reason
        }

def create_memory_analyzer(gemini_client):
    """Create a memory analyzer instance"""
    return ComprehensiveMemoryAnalyzer(gemini_client)