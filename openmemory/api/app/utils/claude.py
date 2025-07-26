"""
Claude Sonnet 4 service for intelligent strategy decisions.
Uses Claude Sonnet 4 for optimal tool calling and reasoning performance.
"""
import os
import anthropic
import logging
import time
from typing import Union, Dict

logger = logging.getLogger(__name__)


class ClaudeService:
    def __init__(self):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")
        
        self.client = anthropic.Anthropic(api_key=api_key)
        
    async def generate_response(self, prompt: str, model: str = "claude-sonnet-4-20250514") -> str:
        """
        Generate response using Claude.
        
        Args:
            prompt: The prompt to send
            model: Model to use (default: claude-sonnet-4 for optimal performance)
        """
        start_time = time.time()
        logger.info(f"🤖 [CLAUDE] Starting API call - Model: {model}")
        logger.debug(f"🤖 [CLAUDE] Prompt length: {len(prompt)} chars")
        
        try:
            response = self.client.messages.create(
                model=model,
                max_tokens=2000,  # Increased for Sonnet 4's more detailed responses
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            elapsed = time.time() - start_time
            logger.info(f"⏱️ [CLAUDE] API call completed: {elapsed:.2f}s")
            
            return response.content[0].text
            
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"❌ [CLAUDE] API call failed after {elapsed:.2f}s: {e}")
            raise
    
    async def fast_strategy_decision(self, prompt: str) -> str:
        """Intelligent strategy decision using Sonnet 4 for optimal tool calling performance"""
        return await self.generate_response(prompt, model="claude-sonnet-4-20250514")
    
    async def strategy_decision_optimized(self, prompt: str) -> str:
        """
        Optimized strategy decision using Sonnet 4 with specific parameters for tool calling.
        Uses lower temperature and optimized max_tokens for consistent, fast responses.
        """
        start_time = time.time()
        logger.info(f"🤖 [CLAUDE-STRATEGY] Starting optimized strategy call - Model: claude-sonnet-4-20250514")
        logger.debug(f"🤖 [CLAUDE-STRATEGY] Prompt length: {len(prompt)} chars")
        
        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=100,  # Very low for strategy decisions - should be just a few words
                temperature=0.1,  # Low temperature for consistent responses
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            elapsed = time.time() - start_time
            logger.info(f"⏱️ [CLAUDE-STRATEGY] Optimized strategy call completed: {elapsed:.2f}s")
            
            return response.content[0].text.strip()
            
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"❌ [CLAUDE-STRATEGY] Optimized strategy call failed after {elapsed:.2f}s: {e}")
            raise